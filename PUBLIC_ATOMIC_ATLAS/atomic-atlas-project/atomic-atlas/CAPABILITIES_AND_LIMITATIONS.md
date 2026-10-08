# Atomic Atlas: Capabilities and Limitations

Documentation edition 0.2 — 8 October 2026. Applies to assembled project checkpoint 010, core 0.0.5.dev1 and source-only harness 0.1. Preparation for release; no publication or independent release approval is implied.

## Overview


Atomic Atlas represents entities, relationships, declared state changes and source-linked decisions. It helps users inspect, record and replay those declarations while keeping proposals separate from accepted records.

Current tests demonstrate bounded structural validation, guarded updates, deterministic file recovery and workflow portability across eight synthetic domains. They do not establish physical simulation, scientific causality or improved language-model performance.

**An accepted declaration records a review decision; it does not establish truth.**

Preserve what the source supports, label what remains unknown, and link corrections without erasing history.

## Capabilities at a glance

| Capability | Evidence in the project | Boundary | Next useful check |
| --- | --- | --- | --- |
| Declarative topology and route inspection | Core tests and eight synthetic-domain substitution cases | A connection is not physical flow; labels do not create mechanisms | Larger graphs and real domain adapters |
| Explicit state changes and replay | Ordered-event tests and fresh-process recovery | Reproduces supplied patches from an event-free baseline, not physical dynamics or LLM recall | Independent installation and recovery review |
| Source-linked proposal review | Harness tests for review, conflict, revision and supersession | Acceptance is a declaration; reviewers and source authenticity are not authenticated | External review of representative workflows |
| Structural schema checks | 12 schemas; 5,097 bounded classifications agreeing with an independent validator | Runtime evaluator supports the used keyword subset; structural validity is not factual validity | Wider conformance and stress corpus |
| Content hashes and append history | Hash, tamper and cooperating-writer tests | Trusted external anchors are needed; no hostile-caller sandbox or cross-file atomic transaction | Independent recovery and failure testing |
| Examples A, B and C | Separate SVG mapping, synthetic retrieval and toy-budget suites | Standalone demonstrations, not automatic integration into the core | Explicit integration contracts and measured evaluations |

Checkpoint 008 reported 123 core tests, 41 harness tests and 65 substitution checks. These are distinct bounded suites, not a universal confidence score. Checkpoint 009 changed documentation and preserved 43 implementation anchors; it did not rerun runtime suites.

## Human–AI collaboration in SVG space

SVG provides explicit, inspectable geometry and grouping. Raster references provide appearance and visual evidence. Neither automatically determines the other. The following is a recommended collaboration protocol distilled from the project workflow, not a claim that the Python core already implements a complete image-to-SVG or 3D pipeline.

### Keep four layers distinct

| Layer | Contains | Does not establish |
| --- | --- | --- |
| Source | Original image bytes, view, legend, scale and source locator | Hidden geometry or a physical measurement unless independently supplied |
| Proposed structure | SVG paths, region IDs, anchors, parent relationships and estimated dimensions | A unique 3D reconstruction or validated anatomy/mechanics |
| Rendering | Color, texture, opacity, lighting and visual overlays | Correct structure merely because it looks convincing |
| Behavior and evidence | Declared transformations, tests, before/after states and receipts | Physical function or causality merely because animation runs |

### A productive bounded cycle

1. **Set the task.** The human specifies the target region, desired change and what must remain fixed. The AI summarizes that intent and preserves qualifiers. Select a small testable change, such as moving one hinge or adjusting one contour.
2. **Prepare references.** Preserve the original image. Supply a separate colored annotation and legend with stable region IDs. Document view, crop, reference dimensions and scale. Treat unmarked, occluded and uncertain regions explicitly rather than guessing their meaning.
3. **Propose structure.** The AI proposes SVG groups, paths, anchors and relationships with confidence and source associations. Use a declared `viewBox` and coordinate convention. Record image-to-SVG transforms, including crop, scale and offsets; do not assume a displayed pixel equals a world unit.
4. **Inspect the overlay.** Use an opacity control to compare source and proposed contours without modifying the source. Show the full view and relevant close-ups. Check alignment, joint roots, parent relationships and connected branches. A visually touching limb is not necessarily structurally attached.
5. **Change one factor.** Retain a baseline and make one explicit transformation. Compare before and after, including regions expected not to change. Separate deliberate motion from camera, lighting, texture or opacity changes.
6. **Check behavior.** Run available structural and event checks. For an SVG adapter, separately test expected transformed coordinates, attachment continuity, view alignment and unaffected controls. Such adapter tests must be implemented and reported explicitly; core graph tests alone do not establish SVG behavior.
7. **Accept or retain as a candidate.** An authorized reviewer records the decision. Preserve unresolved geometry as a candidate. If using the proposal harness, remember that reviewed claims and SVG geometry require an explicit adapter association; acceptance does not synchronize them automatically.
8. **Save provenance.** Retain source and output hashes, legend version, coordinate transforms, changed IDs, parameters, commands, test output and decision links. Append corrections and supersession links. Recover the saved files in a fresh process when deterministic recovery is part of the claim.

### Practical lessons

- **A legend helps identify regions, not infer depth.** Colored annotations are segmentation aids. Keep them separate from the uncolored appearance reference.
- **Multiple views reduce ambiguity but do not remove it.** Front, side and back references need compatible scale, pose and landmarks. Occlusion and asymmetry remain explicit uncertainties.
- **Brightness is not automatically height.** A grayscale image may reflect illumination or material. Treat it as a height/displacement map only when its encoding, range, scale and direction are defined; otherwise it is a proposed interpretation.
- **Appearance and geometry need separate controls.** Skin/material color matching, shadows and high-resolution textures cannot repair disconnected anchors or incorrect proportions. Upscaling cannot recover absent geometric evidence.
- **Use stable IDs rather than visual proximity.** Declare attachment points and parent transforms. Test joints and branch continuity; avoid assuming that overlapping paths share topology.
- **Prefer small edits with unchanged-region checks.** A successful local adjustment includes evidence that unrelated regions remained stable. Use fixed view presets for comparisons and record the actual camera transform.
- **Keep source pixels intact.** Store annotations, overlays and rendered outputs as linked derivatives. If reference bytes change, record the new hash and their relationship to the prior source rather than retaining a stale receipt.
- **Save enough to explain and reproduce a change.** A screenshot records appearance. Structured parameters, geometry, inputs and versioned transformations support deterministic reproduction; neither implies language-model recall.

### Responsibilities

The human supplies intended meaning, authorized sources, reference constraints and review decisions. The AI proposes inspectable structure, tracks uncertainty, explains changes and executes only authorized operations. Both compare evidence against the intended task. No role is automatically a scientific validator, and review does not convert an estimate into a measured fact.

The [Human Guide](HUMAN_GUIDE.md) describes local operation and explicit review. The [AI Guide](AI_GUIDE.md) specifies source-handling and authorization boundaries.

## Proposed applications and release gates


Applications in robotics, games, retrieval, industry, medicine and space remain research directions. Each needs domain-specific adapters, models and independent evidence. A retrieval experiment could hold model, sources and tasks fixed while varying retrieval organization, then measure accuracy, attribution, unsupported claims, contradictions and overhead. No model-performance advantage has yet been established.

Before release: independent package inspection; fresh-environment and clean-install checks; Windows and real-browser verification; example/asset licensing; citation metadata; and a release-version decision. The core and harness carry MIT licenses, but no blanket license is asserted for all examples or assets. Final README and publication remain deferred.

