# Atomic Atlas Persistence — prototype 001

A standalone, neutral SQLite persistence prototype using Python's standard library. This is new implementation, not a recovered copy of any private SQLite system or an adapter to the published Atomic Atlas core. It contains synthetic data only.

## Run

Extract this package. Open a terminal in its folder and run:

```sh
python demo.py
python -m unittest -v test_store
```

On Windows, `py -3.11` can replace `python`. The demo saves a synthetic lamp state, closes the writer, launches another Python process, and checks exact record recovery. Its temporary database is deleted afterwards. For durable use, construct `Store('my-state.sqlite')` with a path outside the temporary demo.

## Record grammar v1

Each record carries an ID, entity ID, full state snapshot, source object, evidence classification, UTC recording time, format version and preceding record hash. The envelope is canonically serialized and SHA-256 anchored. Entity state is recovered from the latest ordered full snapshot, not by merging arbitrary patches. Missing entities return `None`.

States are JSON objects. Applications must define their own domain schemas, variables, units and constraints; the store does not validate physics or Atomic Atlas contracts. The demo explicitly represents power as value plus unit. Source locators are declarations, not authenticated evidence. Source observation timestamps, timezone, artifact hashes and uncertainty can be supplied within the source object; they are not invented automatically.

## Integrity and concurrency

Writes use an immediate transaction, expected-head comparison and record-ID deduplication. Identical retries return the original anchor; conflicting ID reuse fails. SQL triggers reject row updates and deletes. Recovery verifies the full hash chain before returning state. Changes should be appended as new snapshots with explanation/source links, retaining older records.

A hash chain detects many edits; it is not a signature or an independently trusted anchor. A database owner can remove triggers, rewrite the entire chain, or truncate its tail without detection against an external saved head. Keep a trusted head hash separately if that threat matters. This prototype provides no encryption, authentication, access control or cross-language canonicalization guarantee.

## Versions and migrations

Database `user_version=0` is initialized to v1; unsupported versions are rejected. Record envelopes also carry v1. No v1-to-v2 migration is implemented because no v2 contract exists yet. A future migration must use a separate copy, retain original anchors, and append an explicit migration receipt. Do not call version rejection a completed migration framework.

## Tests and next step

Tests cover fresh-process recovery, ordering, deduplication, conflicting IDs, stale writers, append-only triggers, content tampering, unsupported versions, nonfinite numbers, required source attribution, hypothesis labels and missing entities. Browser behavior, native Windows execution, crash/power-loss durability, simultaneous process stress, truncation detection with an external anchor and language-model recall are untested.

Next: bind the envelope to actual core state-snapshot/provenance schemas with a tested adapter, then specify and test a real migration. The frozen published core remains unchanged. No GitHub upload or publication was performed for this prototype.

This package does not add a new license grant; redistribution terms for this new module remain to be selected by the project owner.
