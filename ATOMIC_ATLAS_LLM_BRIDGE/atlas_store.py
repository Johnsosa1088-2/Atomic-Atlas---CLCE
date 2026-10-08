"""Neutral SQLite prototype. This is not an Atomic Atlas core adapter."""
import datetime
import hashlib
import json
import sqlite3

VERSION = 1


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path, isolation_level=None, timeout=10)
        try:
            self.db.execute('BEGIN IMMEDIATE')
            version = self.db.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0, VERSION):
                raise ValueError('Unsupported database version; explicit migration required')
            self.db.execute('CREATE TABLE IF NOT EXISTS records(seq INTEGER PRIMARY KEY, record_id TEXT UNIQUE NOT NULL, body TEXT NOT NULL, anchor TEXT UNIQUE NOT NULL)')
            for operation in ('UPDATE', 'DELETE'):
                self.db.execute(f"CREATE TRIGGER IF NOT EXISTS block_{operation.lower()} BEFORE {operation} ON records BEGIN SELECT RAISE(ABORT, 'append-only'); END")
            self.db.execute(f'PRAGMA user_version={VERSION}')
            self.db.execute('COMMIT')
        except Exception:
            self.db.execute('ROLLBACK')
            self.db.close()
            raise

    def close(self):
        self.db.close()

    def verify(self):
        previous = None
        for expected, (seq, record_id, body, anchor) in enumerate(self.db.execute('SELECT seq,record_id,body,anchor FROM records ORDER BY seq'), 1):
            record = json.loads(body)
            if seq != expected or record['record_id'] != record_id or record['previous_hash'] != previous or digest(record) != anchor:
                raise ValueError('Record chain integrity failure')
            previous = anchor
        return previous

    def append(self, record_id, entity, state, source, expected_head):
        """Full replacement snapshot; expected_head provides optimistic concurrency."""
        if not all(isinstance(x, str) and x.strip() for x in (record_id, entity)):
            raise ValueError('Nonempty record and entity identifiers required')
        if not isinstance(state, dict) or not isinstance(source, dict):
            raise ValueError('State and source must be objects')
        if not isinstance(source.get('locator'), str) or not source['locator'].strip():
            raise ValueError('Source locator required')
        if source.get('evidence') not in ('observation', 'hypothesis', 'user_declaration', 'synthetic'):
            raise ValueError('Explicit evidence classification required')
        payload = {'entity': entity, 'state': state, 'source': source}
        canonical(payload)
        self.db.execute('BEGIN IMMEDIATE')
        try:
            head = self.verify()
            existing = self.db.execute('SELECT body,anchor FROM records WHERE record_id=?', (record_id,)).fetchone()
            if existing:
                old = json.loads(existing[0])
                if any(old[k] != payload[k] for k in payload):
                    raise ValueError('Record ID reused with different content')
                self.db.execute('COMMIT')
                return existing[1]
            if head != expected_head:
                raise ValueError('Stale head; refresh and review before retry')
            record = dict(payload, record_id=record_id, format_version=VERSION,
                          recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), previous_hash=head)
            anchor = digest(record)
            self.db.execute('INSERT INTO records(record_id,body,anchor) VALUES(?,?,?)', (record_id, canonical(record), anchor))
            self.db.execute('COMMIT')
            return anchor
        except Exception:
            self.db.execute('ROLLBACK')
            raise

    def recover(self, entity):
        self.verify()
        result = None
        for body, in self.db.execute('SELECT body FROM records ORDER BY seq'):
            record = json.loads(body)
            if record['entity'] == entity:
                result = record
        return result

    def export(self):
        self.verify()
        return [{'record': json.loads(b), 'sha256': h} for b, h in self.db.execute('SELECT body,anchor FROM records ORDER BY seq')]
