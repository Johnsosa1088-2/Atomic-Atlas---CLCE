# Five experimental CLCE engines — checkpoint 006

Source: supplied hermesless.png, byte hash and crop coordinates in sources/HERMES_CODE_INVENTORY.json. Each class and visible named method is implemented in engines.js. Browser adaptations are labeled separately from exact historical execution. The image is not a complete executable file; some lines end beyond captured panel boundaries. There is no claim of NumPy bit-for-bit replay, physical calibration or measured quantum coherence.

| Source class | Callable methods | Interpretation and adaptations |
|---|---|---|
| CLCEEngine | compute_graph_properties; run_flow | Binary graph density, degree>=3 branches and triangles. JS seeded random generator differs from NumPy. Noise flips unordered edges symmetrically, unlike the asymmetric full random mask shown. The cropped complete coherence expression is unresolved: coherence is null, not invented. Visible feedback multiplier .15 is reported only. |
| PhysicalCLCEEngine | generate_coordinates; analyze_topology | Source planar central-angle arrangement; last atom displaced in x. Counts every pair within 15% of radius sums, including nonbonded pairs. Score is this fraction, not a chemical stability verdict. Angle literals are retained as shown, rather than silently converted from their comments. |
| StructuralTopologyEngine | compute_3d_topology | Central-atom tetrahedral, bent and linear vectors; first peripheral receives a perturbation. Dimensionless score is mean exp(-5 strain²). Source calls this energy but supplies no joule calibration. Source linear vectors both point to +z and therefore overlap; retained with explicit warning. Excess peripherals are rejected rather than silently left at the origin. |
| GlobalTopologyCLCEEngine | resolve_network_coordinates; analyze_spectral_invariance | First-listed-neighbor construction with golden-angle directions, then distance-weighted Laplacian. Weights exp(-3 strain), Fiedler λ₂, score sigmoid(λ₂); source .5/.1 Fiedler disposition thresholds retained. Construction can use an as-yet-unpositioned neighbor and is order-dependent. These are disclosed limitations, not an invariant claim. |
| QuantumCoherenceCLCEEngine | relax_3d_geometry; compute_quantum_phase_coherence | Seeded normal initialization, 50 spring/repulsion updates, .05 step, spring factor2, repulsion .1/r². Different random sequence from NumPy. Source exp(i·2π·distance/1.5) is assigned symmetrically and is not Hermitian. The implementation explicitly mirrors the lower triangle by conjugation, matching NumPy eigh's default triangle interpretation. A real-block Jacobi solver then supplies the dominant complex eigenvector. A normalized off-diagonal pure-vector score is calculated; degeneracy is reported. |

All constructors expose the screenshot's radius table. Undefined elements are rejected instead of silently using fallback radii. Methods have explicit shape, finite-value and size checks. The numerical kernels use 24-atom limits and report convergence failure. The visible constructors are JavaScript constructors, not callable Python __init__ methods. Coordinates use the source's nominal radius units (Å according to its comments); drawing pixels are not converted into molecular distances.

## Formula readings and unresolved source

The visually read formulas below are source-informed literal equivalents, distinct from the browser implementation and its named adaptations. Full-image bounding regions use [x0,y0,x1,y1] pixels. No source creation date has been inferred from its upload.

- Panel1 graph section, [23,64,336,240]: density = edges/max_edges; branches = sum(degrees>=3); squared_matrix = matrix_power(matrix,3); tr = trace(squared_matrix); rings = int(tr//6). The variable rings counts triangles only for a simple symmetric binary graph. The later coherence line is clipped on the right: not reconstructed.
- Panel2 ratio section, [378,471,670,756]: valid_bonds / total_possible; pair tolerance ideal_dist*0.15. Pair classification does not establish whether a covalent bond exists.
- Panel3 strain section, [723,443,1027,705]: strain = abs(actual_dist-ideal_dist)/ideal_dist; accumulation exp(-strain**2*5.0); divide by number of peripherals. Coefficient units and physical calibration are absent.
- Panel4 weight/spectrum section, [1104,513,1414,955]: W_ij = exp(-3·strain); L=D-W; λ₂ is the second-smallest eigenvalue; score = 1/(1+exp(-λ₂)). The source calls this parameter-free even though the weighting factor, mapping and decision thresholds are chosen constants.
- Panel5 phase section, [1565,623,1878,1020]: phase=2π·distance/1.5; H_ij=exp(i·phase) on bonds; rho=outer(principal_state,conj(principal_state)); score=(sum(abs(rho))-trace(abs(rho)))/(n-1), clipped to [0,1]. The phase denominator is a chosen length scale, not the biophoton calculator's 550nm wavelength. No established biological or quantum derivation is supplied.

These coordinates locate equation regions rather than character-perfect crops; the screenshot is low-resolution and some right-side code is clipped. AS_RENDERED issues remain visible in the preserved image. The adaptation does not fix the source quietly.

## How to explore

Build a small graph; select an engine stage. Press Run baseline + perturbation to calculate both outputs without changing the input graph. Preview coordinates are a 2D projection of newly generated 3D positions. They are not inferred from your drawn positions. For stage3, the first atom is the center and others are proposed peripherals; use at most four for tetrahedral or two for bent/linear. Stage1 uses the current atom count but generates its own graph; its displacement field does not affect that graph. Stages4–5 ignore bond order, charge and hydrogen-bond candidates. Export engine run saves the actual declared inputs, results and adaptation label; it does not authenticate scientific validity or create an Atlas core commit.

Changes in these scores do not create joules. None supplies temperature, reaction kinetics, molecular force-field validity, an LLM improvement or quantum evidence. Continuous power/heat/light remain in their explicit separate budget. Browser behavior remains unverified.
