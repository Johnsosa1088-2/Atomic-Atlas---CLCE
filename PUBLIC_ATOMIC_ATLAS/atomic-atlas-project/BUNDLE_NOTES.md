# Atomic Atlas — core and LightBench

This bundle contains a provenance-oriented core with reproducible checks, plus an interactive SVG LightBench and a separate aspiration roadmap. It is a reviewable release candidate, not a published release or a validated physical simulator.

## Start here

1. Extract this outer ZIP.
2. Extract `ATOMIC_ATLAS_LIGHTBENCH_008.zip`. Open `LightBench/LightBench.html` in a browser for the standalone interactive demonstration. Read `LightBench/README.md` and `ENGINE_ADAPTATIONS.md` for controls and model assumptions. The inner README retains historical checkpoint notes; later checkpoint notes supersede earlier ones.
3. Extract `PUBLIC_ATOMIC_ATLAS_STEP10_014_REPEATABLE.zip` into its own new folder. Begin with `WINDOWS_START_HERE.txt` and `RELEASE_CANDIDATE_GUIDE.txt`.

4. Extract `ATLAS_ASPIRATION_MAP_009(2).zip` and read `ASPIRATION_MAP_009.txt` alongside `APPLICATION_MAP.json`. This documentation-only roadmap groups 13 proposed application families; it does not establish those capabilities. The original image is retained as source material, with transcription and redistribution limits documented inside.

These are separate components. LightBench does not currently commit its state to the Atomic Atlas core, provide an LLM integration, or maintain a persistent SQLite memory store.

## What is included

| Component | Contents |
|---|---|
| Core checkpoint 014 | Core version `0.0.5.dev1`, schemas, proposal harness, examples A–C, independent validation materials, reproducible verification runner and historical receipts |
| LightBench checkpoint 008 | C/H/N/O/P/S graph editing, bond controls, presets, energy accounting, experimental CLCE adaptations, Hermes worksheet, Hermitian phase diagnostics, source graphics and tests |
| Aspiration map 009 | Documentation-only application roadmap, proposed evidence requirements, source image and historical receipt |
| Bundle documentation | This README, archive hashes and an assembly review receipt |

For human and AI workflows, read the core package's `AI_GUIDE.md`, `CAPABILITIES_AND_LIMITATIONS.md` and release candidate guide. Preserve source attribution, distinguish observations from hypotheses, and report missing evidence instead of filling gaps from recall.

## Core verification

Use an external Python environment with the dependencies specified by the included guides and lock files, plus Node.js. Do not reuse or modify a ComfyUI environment.

From PowerShell in the extracted core folder, with the external environment available:

```powershell
node --version
..\atlas-012-venv\Scripts\python.exe .\verify_candidate.py
$LASTEXITCODE
```

Substitute your environment's actual path. Follow the included setup guide if that environment does not exist. A full pass requires exit code zero and the final PASS result. The runner saves logs and receipts in a retained sibling `atlas-014-run-*` directory and checks source integrity before and after. Do not run `run_suite.py` directly; it is the runner's internal worker.

## Evidence and limits

- The core archive contains repeat-run evidence and its original 43 frozen source anchors. Historical receipts describe the checkpoint at which they were written.
- A separate user-supplied Windows run was previously reviewed: Python 3.11.0, Node 24.21.0, exit zero, with the copied 43 anchors matching. That run archive is **not included here**. The unchanged core archive still labels Windows evidence pending; this README does not rewrite that historical status or claim a Windows run occurred during this assembly.
- LightBench retains 74 passing checks from checkpoint 007: 37 model, 19 engine, 12 phase and six independent NumPy checks. Checkpoint 008 changed the live comparison display; its embedded JavaScript syntax was checked, but those 74 checks were not rerun for that checkpoint.
- User screenshots provide partial rendering evidence. Automated real-browser verification and broad browser compatibility remain unverified.
- Energy accounting and matrix diagnostics describe the implemented models. Chemistry validity, fusion onset or rates, quantum behavior, biophoton emission, consciousness and internal-memory restoration are not demonstrated.
- Some historical formula transcriptions remain pending visual confirmation. See the source coverage reports and engine adaptations before treating any expression as an exact source transcription or a scientifically validated equation.

## Public release checklist

The core and proposal harness contain MIT notices. Do not assume those notices license every example, graphic or LightBench asset. Example/asset licensing, owner-selected public attribution and citation, a release version, and independent external review remain open. Review source graphics and provenance metadata for intended public disclosure before publishing.

This bundle contains no new publication authorization. No repository URL, DOI, ORCID or finalized citation has been invented.

## Integrity

The three inner ZIPs are preserved byte for byte from the supplied bundle. `BUNDLE_MANIFEST.json` records their SHA-256 hashes and the README hash. `BUNDLE_REVIEW_RECEIPT.json` records this assembly's checks and limitations. Keep historical receipts intact; append later evidence rather than overwriting it.

## Constructing the next stage

Keep the core as the tested foundation, LightBench as the experimental demonstration, and the aspiration map as the planning layer. Advance one bounded use case at a time: freeze inputs and success criteria, implement an explicit adapter, compare with an independent baseline, and append reproducible results.

The roadmap recommends an offline retrieval evaluation first. Compare ordinary retrieval with atlas-organized retrieval using the same model, source corpus, tasks and resource budget. Measure answer accuracy, source attribution, unsupported claims, contradictions and retrieval overhead. This is a proposed experiment; no improvement is claimed.

The aspiration ZIP is included at the owner’s request for this review bundle. Its statement that it was not inserted into the public candidate describes its historical assembly, now superseded by this bundle’s inclusion decision. Its deferred README and pending Step 9 notes are also historical. Including it does not resolve the source-image redistribution rights or authorize publication.


GitHub preparation: use the extracted folders listed in the root README instead of the historical ZIP extraction instructions above. Companion private file IDs were replaced with neutral references, and companion manifests regenerated. Historical companion receipts are not claims that these new bytes passed those historical runs. The core is byte-identical to checkpoint 014. No broad browser or automated secret scan was performed.
