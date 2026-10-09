# Aurelia image annotation foundation 002

Open `workbench.html` in a modern desktop browser. It is self-contained and makes no network calls. If local-file SHA-256 is unavailable, run `python -m http.server 8000 --bind 127.0.0.1` in this directory and open http://127.0.0.1:8000/workbench.html. Do not use a public host for private images.

## Human workflow

1. Upload a PNG/JPEG/WebP (maximum 8 MiB). The original bytes are SHA-256 hashed and embedded; duplicate hashes select the existing image. Set front/side/back view explicitly.
2. Type a meaningful label and optionally choose an adapter part. Confidence may remain unknown.
3. Choose Landmark and click a point. Choose Region, click polygon vertices and Finish region. Choose Connection and click two accepted landmarks.
4. Select an annotation to change its metadata. Drag human landmarks in Select mode. Removing a landmark removes dependent connections in the new snapshot; earlier snapshots remain.
5. Export the checkpoint before closing. Import verifies the event chain, current state, embedded source hashes and current image dimensions before replacing the session. Replacement asks you to preserve unsaved work first.

Image coordinates are original source pixels, independent of displayed zoom. There is no depth, physical scale, segmentation, pressure solver or anatomical inference. The optional cage overlay is a proportionally fitted schematic from adapter 001, not a measured binding. Part links express the operator's annotation, not verified mechanics. Labels display as text, never HTML. Only raster image data is supported; uploaded SVG/script content is rejected.

## AI workflow and provenance

No model runs in this release. AI integrations should use the same geometry and IDs, with `author: "ai"`, a specific `method` identifier and `status: "proposed"`. Proposed marks are dashed. A person accepts or rejects them explicitly. The model validator requires valid authors, methods, statuses, references and bounds; it does not prove the author actually is human or AI. This is review metadata, not authenticated identity.

To build a proposal checkpoint programmatically, load `model.js`, load an existing checkpoint into `Ledger`, clone its state, add proposed annotations and call `append('AI proposal: method/version', state)`. Export `ledger.project`. On browser import, the proposal retains its status. Preserve source image hashes, label uncertainty and method/version; do not fabricate pixel measurements from descriptions. Records support unknown confidence and unbound parts. Accepted landmarks may be connected; AI landmarks are not manually dragged, so corrections should be a new human mark and rejection of the original proposal.

Events contain sequence, UTC recording time, action, previous hash and a complete state snapshot. Edits and removals append snapshots; Undo appends the preceding snapshot as a restoration event. Repeated Undo restores the preceding event, so it may toggle between snapshots; this is not a conventional multi-step undo stack. Source capture dates are not inferred from filenames or upload times. Exported checkpoints store each source image once and retain all event snapshots. Internal session snapshots still repeat image text; use bounded batches. Maximum compact checkpoint size is 256 MiB; expanded historical image text is limited to 512 MiB. Session work is in memory only; there is no automatic durable saving or IndexedDB recovery yet.

The hash chain detects accidental changes and broken ordering. An owner can recompute a whole chain; there are no signatures or external trust anchors. Store export hashes independently when stronger provenance is needed. Import replaces a session; merging branches and conflicts is not implemented. Historic snapshots are structurally validated; embedded byte hashes are checked for images in the final state. No image deletion control is exposed in this release.

## Verification and integration boundary

With Node 18 or later: `node test_model.cjs` runs model tests. `node verify_checkpoint.cjs your-checkpoint.json` independently checks an exported chain and final embedded image bytes. The CLI does not decode image dimensions; browser import does.

`adapter_001/` preserves the prior Python cage/SQLite/LLM package unchanged. The annotation format deliberately remains separate: part links use its IDs, but no automatic annotation-to-SQLite conversion is provided yet. This avoids silently treating image annotations as measured physical state. Next integration should commit validated annotation checkpoints and use region/anchor links as retrieved evidence, with physical calibration and units added explicitly.

## Scope

New private implementation, authorized by the user's visible request to build a robust annotation foundation. The current source request has no supplied image to bind. No private reference image is bundled. Gemini's dashboard idea informed the arrangement only; its fake telemetry and claims of a connected simulator were not imported. No full external JSON Schema conformance, scientific validation, model recall or automated object recognition is claimed. See run receipt for tested and untested coverage. See CHANGES_002.md for the size repair and compatibility details.
