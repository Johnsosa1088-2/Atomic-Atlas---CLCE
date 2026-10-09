# Aurelia adapter 001 — private pocket and anchor scaffold

Open `workbench.html` directly in a modern browser. Drag the anchors, inspect a part, and export the edited JSON. The schematic connects the torso, pelvis and both legs. Subject left is viewer right. SVG coordinates have no physical calibration.

From this directory, with Python 3.10 or later:

```sh
python -m unittest -v
python adapter.py scaffold.json
python adapter.py scaffold.json --db aurelia-private.sqlite
```

Use `scaffold-edited.json` in the last command to commit an exported layout. The database receives one complete, hash-linked snapshot per distinct scaffold; repeated identical imports deduplicate. Corrections create new records. Existing bridge/store modules are copied unchanged. `bridge.packet(database_path, 'aurelia cage')` retrieves the scaffold for an LLM context packet; no model is called. A packet is evidence for review, not a command to execute. SQLite triggers discourage updates/deletes but do not make a database tamper-proof against its owner; verification checks the hash chain.

## Model and accounting

Water volume and gauge pressure are distinct from gas volume and absolute pressure. A pneumatic actuator may drive a water chamber, but coupling, compliance, geometry and materials remain unspecified hypotheses. There is no incompressibility, pressure, deformation, muscle, contact or fluid solver in this adapter. Pocket names are proposed engineering compartments, not assertions about human anatomy.

For an explicitly constant gauge-pressure approximation, exported Python helper `pressure_work_J` evaluates W = p_gauge × ΔV in joules. Expansion is positive work output. Variable pressure requires an integral along the actual path; this helper does not supply that path. No gas law or temperature is inferred. The energy residual is input minus mechanical output, heat loss and stored energy change. Missing terms return null; zero residual is only an accounting check, not a physics validation. Initial energy is metadata, not an extra per-step input.

## Provenance and coverage

The inspected source is the `generated/living_atomic_atlas.json` member of user-restored `Aurelia_restored.zip`. Archive and member SHA-256 anchors and source version are in the scaffold. Only its six broad region names informed the proposed mapping. Individual part IDs are new adapter IDs; mappings to atlas regions are unconfirmed. Source numerical morphology, coherence and physiological claims were not imported as measured values. Original packages were not modified.

The visible current user request proposes pneumatic water pockets, cage anchors and an energy budget. This is a normalized intent summary, not an exact quote. Source locator: current conversation, latest user message beginning “This is a good”; source timestamp unavailable. Retrieval date: 2026-10-09 UTC. No image pixels or image-region bindings were available for this step. No full historical-conversation coverage is claimed.

## Limitations and next step

This is a separate private adapter step, not a numbered conversation lab or public release. Image bindings, calibration, joint limits, pocket parameters and source-to-part bindings are null or explicitly unresolved. No face/body images are bundled. HTML exports are not automatically persisted; commit with Python. Automated tests cover deterministic file/database recovery, graph validation, unit arithmetic and packet integration. Browser drag/export behaviour and language-model recall are untested. Full external JSON Schema conformance is not claimed; the importer uses targeted Python validation, not a general JSON Schema validator.

Next: bind one user-labelled image region and two anchors to an existing part; preserve image hash, view, crop/region coordinates, scale uncertainty and the source decision. Then define and test one chamber's pressure–volume law before adding deformation.
