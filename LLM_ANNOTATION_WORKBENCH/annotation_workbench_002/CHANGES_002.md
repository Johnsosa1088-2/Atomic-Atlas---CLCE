# Checkpoint size repair — 002

Cause found in version 001: `Ledger.append` creates a complete snapshot including base64 image data at every edit, and the exporter serialized every snapshot. A 6 MiB image becomes roughly 8 MiB of base64 per snapshot; a few edits can exceed the old 40 MiB export limit. Image opacity and zoom are not the cause.

Version 002 uses a compact transport envelope: each unique source image's bytes appear once in an asset table keyed by SHA-256. Event snapshots refer to those assets. Import restores the original snapshots before verifying the original event hashes. No history is discarded or re-signed. Legacy 001 checkpoint imports remain supported. This changes downloadable storage; the session ledger still uses full snapshots in memory. A future event/delta ledger would reduce that internal cost too.

Export/import limits are now 256 MiB, measured in UTF-8 bytes for export. Expanded history has a separate 512 MiB image-text budget to limit memory exhaustion; this is not a promise of a fixed browser RAM requirement. Session overhead and hashing still grow with edits. Individual image uploads remain limited to 8 MiB. Work in checkpoints for very long sessions.

The compact importer verifies all asset bytes, including images present only in earlier events. The final visible images are also decoded to check dimensions. The command-line verifier supports old and new formats.

The default annotation tools are object-neutral. The Aurelia part list and cage remain optional conveniences. A custom object/part ID field lets other domains use their own identifiers. No automatic object classification is added.

The size regression uses synthetic bytes, not a browser-decodable PNG: it tests storage, hashing and exact recovery. Browser upload/render verification remains unperformed because Chromium is unavailable in the development environment. No screenshot diagnosis is claimed; the supplied screenshot path was not available, and the export error was traced directly in the source.
