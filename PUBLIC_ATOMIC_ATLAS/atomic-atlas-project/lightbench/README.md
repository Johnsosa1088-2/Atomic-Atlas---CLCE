# Atomic Atlas LightBench 0.1.0

Open **LightBench.html** in a modern browser. No installation, account, network connection or server is required. The separate index.html/model.js pair is included for development. This is a private downloadable companion prototype; it does not replace or alter public Atomic Atlas checkpoint 014.

Choose C, H, N, O, P or S and click empty space; drag atoms, or switch to Bond and click two atoms. Bond order is editable before connecting. Select an atom to change formal charge or delete it. Use the water, ring and sulfur-bridge presets. Run or pause the energy model, adjust power/cooling/light fraction/wavelength, then export and import the scene.

## Implemented model

- Neutral electron counts use Z minus formal charge. Valence counts use the CHNOPS group values 1,4,5,6,5,6. The displayed unassigned count is simple bookkeeping, not an orbital calculation or octet validator. Electrons drawn around nodes are symbols, not trajectories.
- Bond-order warnings use simplified neutral templates H1, C4, N3, O2, P3, S2. These omit many valid ions, radicals, aromatic structures and higher-valence states. Warnings are not chemistry verdicts.
- Cycle rank is E−V+connected components. Branch points have degree ≥3. These are graph properties, not molecular stability measures.
- Hydrogen-bond candidates require H connected to one N/O/S donor, an unbonded N/O/S acceptor, 10–150 pixel separation and a forward alignment cosine >0.5. This new illustrative heuristic does not evaluate lone pairs, real distances, solvent, protonation or bond energies.
- Incoming energy Pin·dt splits into user-selected optical allocation and thermal energy. Cooling removes at most available thermal energy. Heat capacity is 10 J/K; cooling coefficient is W/K; the ambient is 293.15 K. The residual is input−light−cooling−stored heat. Changing efficiency or wavelength affects future increments only.
- Each equivalent photon has E=hc/λ using exact SI h=6.62607015×10⁻³⁴ J·s and c=299792458 m/s. Counts are fractional energy-equivalent expectations. There is no measured biological emitter or predictive biophoton rate.
- Export snapshots include an ordered edit journal and optional SHA-256 digest over the literal payload. Import checks that digest when available and validates topology, ranges and the energy balance. A digest detects changes; it does not establish authorship. The journal is not a complete replay: continuous thermal evolution is stored in the snapshot, and clearing/loading presets replaces the local scene journal.

## Source coverage

The verified local Example C energy model (`public_atomic_atlas_014/examples/c_closed_loop_budget/model.js`, ATLAS-C/1.0.0) informed the conservation-ledger pattern. This workbench is a **new SI lumped thermal model**, not a port of that dimensionless steam model.

## Updated source evidence (checkpoint 002)

Both supplied images were visually inspected on 2026-10-08. Copies and SHA-256 anchors are included in sources/. This supersedes the earlier OCR-only access limitation for these two pages; it does not imply access to the complete historical archives.

CLCEv1.0.png: source-ref-9311938e2e82. The flow and CHNOPS/topology vocabulary are visible. Its coherence 0.97 and locked_topology True are fixed return values, not calculated physical findings. Its branch description uses degree >=2 while its detect field uses degree>=3; this workbench uses >=3 for branch points. Its N-H/O-H hydrogen_bond labels do not distinguish a covalent donor bond from an intermolecular hydrogen bond; the workbench does distinguish them.

Screenshot_2026-08-09_143913.png: supplied Library ID source-ref-a8a28e496aa4. Original supplied name Screenshot 2026-08-09 143913(1).png. The filename is not treated as a verified source creation date. The proposed expression appears on line 40: dissipated_energy_j = 1e-19 * (coherence_delta * 4.2 + structural_stress_delta * 1.8), clamped on line 43 with max(0.0, dissipated_energy_j). Coherence delta is abs(initial_coherence-final_coherence), line 37. Photon conversion is on lines 46–49, using source constants h=6.626e-34, c=3.0e8, default 550 nm. These literals are reproduced in historical(), separately from the exact-SI live model. The coefficient units, calibration and physical meaning of the scores are not established. No silent scientific repair is made. Line 54 HIGH_COHERENCE_RELEASE is a threshold label, not an authenticated emission finding.

The separate historical calculator does not transfer its predicted energy to the live budget. That would require an explicit, independently justified source of energy. The comparison shows the proposed one-transition energy and the cumulative live budget total with their distinct meanings.

Historical executable hydrogen-bond code beyond the CLCE relationship labels remains unavailable. The candidate geometry rule remains a newly written heuristic. Archive downloads previously failed with HTTP 403; the full codebase is not claimed to be covered.

Primary definitions: https://www.nist.gov/pml/special-publication-330/sp-330-section-2 ; https://physics.nist.gov/cuu/Constants/Value/c.html ; https://goldbook.iupac.org/terms/view/HT07050

## Human and AI workflow

Humans choose structures and budgets; the UI makes proposals visible. An AI can inspect exported snapshots, state uncertainties, and propose changes by stable IDs. Treat proposals as unvalidated until checked. Preserve the original snapshot and append any correction or reviewed result in an external provenance store. This prototype has no LLM connection, SQLite persistence, Atomic Atlas core commit adapter, quantum solver or molecular dynamics. Those are future integrations, not demonstrated capabilities.

Run `node test_model.js` for deterministic model tests. Browser test details and actual results are recorded in RUN_RECEIPT.json. Fresh-process file recovery tests demonstrate deterministic recovery, not language-model recall or internal memory restoration.

## Checkpoint 003: undo, disulfide scaffold and nuclear playground

Undo/redo keeps up to 100 in-session snapshots of editable changes. A restore pauses play, restores energy state along with the graph, and appends an undo/redo entry. Atom ID counters do not decrease on undo. Continuous run steps are not individual undo actions. Slider movement may create multiple checkpoints. Export saves the scene, not the undo stack. Loading a preset/import or clearing is also undoable; these actions otherwise replace the scene journal as documented above.

Double disulfide scaffold is two six-carbon skeleton chains joined by two C–S–S–C links. Hydrogens and complete molecular context are omitted. A disulfide bond is editable here; the historical source's permanent-lock label is not imposed as chemistry.

The separate hydrogen-to-helium playground assumes a user-selected number of already completed proton–proton chains. It uses an approximate 26.7 MeV total per helium-4 produced (including positron annihilation), with conversion 1 eV = 1.602176634e-19 J. It reports hydrogen consumption, helium production, mass-equivalent decrease, and explicit neutrino/light/heat allocations. The approximate 2.2% neutrino default is editable; it is not universal across chain branches. The light/heat split is an arbitrary energy-allocation scenario, not a stellar transport result. E=mc² uses the exact SI c. No onset conditions, reaction rate, plasma dynamics or wall-plug gain are modeled. It does not alter the chemical scene or the live thermal energy ledger. Helium is represented only as a nuclear product in this panel.

References reviewed 2026-10-08: https://www.energy.gov/science/np/articles/proton-proton-fusion-powering-sun ; https://www.energy.gov/science/doe-explainsburning-plasma ; https://www.astro.princeton.edu/~burrows/classes/514/514.2025.pdf (26.7 MeV and approximately 0.6 MeV neutrino accounting).

Browser verification deferred for the next joint step. Model tests and JavaScript syntax checking do not establish browser usability.

## Checkpoint 004: thermal setup and Hermes worksheet

Ambient/starting temperature and heat capacity are now editable. Applying them pauses play and resets the thermal ledger, avoiding an unaccounted jump in stored energy. This action is undoable.

Hermes source inventory: Aurelia Presents the Hermes Loss Framework.png, source-ref-79fd484c42be, metadata creation 2026-09-12T08:22:40.086617Z; Cosmic Observatory of Unbribable Knowledge.png, source-ref-d982a8c42be6, metadata creation 2026-09-15T02:58:52.159971Z. Retrieved 2026-10-08 as extracted text only; pixels unavailable. Search descriptions contain clearer equations than the full OCR, so all implemented expressions are explicitly proposed transcriptions pending visual verification. The original executable implementation and complete function inventory were not located. This checkpoint does not claim every historical Hermes function is reproduced.

Implemented draft functions: declared response-change input; attack-magnitude normalization; sensitivity normalization; maximum normalized damage; inverse resistance score; distinct-family coverage; explicit counterexample flag; separate weighted prediction/relationship/conservation/provenance objective; exported worksheet record with notes and retrieval status. No attacks, measurement distance, sensitivities, units or loss terms are inferred automatically. The behavior contract's perturbation response, release response, domain, failure mode and transfer behavior require independently specified measurements. Definitions of uncertainty and provenance terms in the historical graphics remain incomplete.

Resistance is higher-is-better; weighted objective is lower-is-better. They share a historical name but are not merged. Untested resistance is null. A reported decisive counterexample is visible even if the numerical score looks good. Neither score establishes truth, immunity to future attacks or physical validation. Worksheet exports are separate declared records, not cryptographic attestations or Atomic Atlas core commits.

## Checkpoint 005: supplied code image

hermesless.png was visually inspected in five crops and preserved with a byte hash. See sources/HERMES_CODE_INVENTORY.json for all visible function names and full-image pixel coordinates. The image is five CLCE engine variants, distinct from the two Hermes score graphics retrieved earlier. Its source creation date and original executable files remain unknown.

Added graph density and triangle counts alongside existing branch counts. Bond order is ignored for these unweighted graph metrics. The source's rings quantity is a triangle count, not general ring detection; the UI uses explicit names rather than silently conflating it with independent cycle rank. Graph metrics use drawing connectivity only, not physical measurements.

The coordinate, strain, Laplacian and phase-model functions are inventoried but not ported. Comments claiming physical invariance or true quantum coherence require independent review. The screenshot's chosen spring constants, geometry construction, phase prescription and cutoffs do not constitute established quantum chemistry. This checkpoint does not claim all source functions are implemented. The previous score formulas remain draft; this code image does not show them. Browser behavior remains unverified.

## Checkpoint 006: all five engine stages callable

Added engines.js with all five screenshot class constructors and visible named methods. The source is adapted to JavaScript with explicit checks and documented deviations. Complete fidelity is not claimed: the stage-1 score expression is clipped, the random generator differs from NumPy, and known source defects are handled transparently. See ENGINE_ADAPTATIONS.md for exact method inventory, formulas, limitations and numerical conventions. Earlier checkpoint sections describe their historical coverage at that checkpoint; this section supersedes their not-yet-ported status.

Use Methane star for the tetrahedral central-atom experiment or Single water for the bent experiment. The Five CLCE engine experiments panel lets you run a baseline and displaced version and export both results with declared inputs. A generated-coordinate projection provides visual feedback. These calculations never alter the main scene or its thermal ledger. Synthetic graph stage uses the scene atom count, not its bonds; displacement has no effect in that stage. The other stages use their documented source-specific interpretations rather than sharing one score.

Verification: `node test_model.js`; `node test_engines.js`; optional independent numerical checks `python test_numpy_reference.py -v` with NumPy installed. The Python reference tests compare weights, Laplacian eigenvalues, complex dominant eigenvalue and density score against NumPy on a declared nondegenerate four-node fixture. This verifies those kernels, not all graphs or scientific validity. Tests ran with Node24.19.0 and NumPy2.3.5. Browser tests remain pending; the included test_browser.js still covers the earlier interface and is not a full test of the new panel.

## Checkpoint 007: user-proposed Hermitian phase lab

The user supplied an antisymmetric phase-angle construction in the current conversation on 2026-10-08. The assistant suggested consistent per-node phases as a separate baseline, and the user authorized both options. The new panel implements both and keeps the screenshot's historical Stage5 engine separate.

Run the panel on 1–24 scene atoms. In node mode θij=φi−φj, with Pij=exp(iθij); in pairwise mode each upper-triangle angle is sampled independently and the lower triangle negated. Complete matrices have unit diagonal. A checked bond mask multiplies by the symmetric binary scene adjacency and makes the diagonal zero. Bond order and charge do not alter these phase matrices.

The seed uses a documented LCG32 generator, not NumPy's generator; identical seed values across the two systems do not imply identical matrices. This is reproducibility within the browser implementation. Phase values are simulated and do not derive from photons, atom coordinates, heat or measured signals. A zero Hermitian residual is a numerical symmetry result, not quantum evidence.

Diagnostics: Hermitian residual; real-block eigensolver eigenvalues; rank and PSD at tolerance 1e-9·max(1,N); trace; graph cycle rank and a fundamental-cycle closure check. Full consistent node matrices have rank1 and traceN; dividing by N gives a trace-one PSD matrix as a mathematical construction. Masked matrices generally are indefinite coupling matrices, not density matrices. Pairwise phases may be frustrated. No loops yields NO_LOOPS_TO_TEST, not an empirical consistency claim. The cycle diagnostics use a spanning forest; the maximum residual is across its fundamental cycles, not all simple cycles.

Export phase run includes atom order, seed, generator name, mask adjacency, actual angles/complex entries, diagnostics and UTC creation time. It preserves a declared calculation rather than a core Atlas commit or authenticated measurement. Color-table cells show wrapped radians and a tooltip with complex entries. The energy ledger is unchanged.

Verification adds twelve phase checks and two NumPy spectrum comparisons (complete node/pairwise matrices and a masked fixture). This brings the packaged check total to74. Browser controls remain for the user's joint verification; model checks do not substitute for browser interaction testing.

## Checkpoint 008: screenshot review and stale comparison fix

Two user screenshots confirm rendering of the water scene, live energy display, historical comparison and fusion budget in the user's browser. They are partial visual evidence, not complete interaction verification. They revealed a stale comparison total: the historical panel showed zero current light despite the main panel showing 0.04J. The historical proposal now remains labeled as the last calculation, while the current budget total refreshes with rendering, including resets and undo. Syntax checking passed. The prior 74 numerical checks remain the checkpoint007 evidence; numerical model files were unchanged in008. No new independent browser test ran. See BROWSER_SCREENSHOT_REVIEW_008.json for evidence hashes and limitations.
