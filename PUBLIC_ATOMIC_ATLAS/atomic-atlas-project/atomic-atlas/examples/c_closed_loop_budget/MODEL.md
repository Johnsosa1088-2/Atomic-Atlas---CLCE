# Example C — declared dimensionless budget model
Version ATLAS-C/1.0.0. All equations below are PROJECT_PROPOSED for this implementation. They are not literal transcriptions of historical graphics.

State mass inventories: B (boiler liquid), V (vapour line), C (transition/condenser chamber vapour), D (condensate awaiting pump), R (return reservoir). Initial B=1 and all others=0.

Liquid thermal energy U starts at zero. Returning liquid and condensate are assigned zero thermal energy. Each vapour mass unit stores H=5 energy units; boiling threshold T_B=1. Fixed demo-clock timestep Δt=0.1. No mapping to kelvin, watts, pascals, joules, kg or experimental seconds is asserted.

## Per-step operator order
1. External heater adds q=p_heat Δt only when B>0.02 and V<0.35−10^-12. This guard is an illustrative inventory cap, not a pressure safety model. Qin += q.
2. Ambient loss l=min(U,0.012 U Δt); U -= l; Qout += l.
3. Evaporation:
   x=min(max(0,B−0.02),max(0,0.35−V),0.08 Δt,max(0,U−B T_B)/(H−T_B)).
   B -= x; V += x; U -= H x.
4. If steam edge is connected, v=min(V,0.12 valve Δt). V -= v; C += v.
5. Condensation d=min(C,0.10 cooling Δt). C -= d; D += d; Qout += H d.
6. Pump transfer r=min(D,0.10 pump Δt). D -= r; R += r.
7. If return edge is connected, b=min(R,0.10 pump Δt). R -= b; B += b; cumulativeReturned += b.

Transport and condensation may occur within one split timestep. This is a compartment bookkeeping abstraction with prescribed rates, not resolved advection, geometry or condenser thermodynamics.

## Invariants
Total mass B+V+C+D+R = 1.
Stored energy E=U+H(V+C).
Mass residual = totalMass−1.
Energy residual = E−Qin+Qout, initially zero.
Evaporation transfers Hx from U to vapour energy; condensation sends Hd to the external cooling sink. Mass and energy are conserved by the declared ledger.

## Frozen paired protocol
Two fresh states; controls frozen before the run; both edges initially connected. Duration60 demo seconds, intervention at20, dt0.1. Branches: return cut, steam cut, cooling off, sham. Metric cumulative liquid return. Signed difference base−perturbed; demo relative change |difference|/|base|, undefined if |base|≤10^-9.
A changed return is expected from the declared model and is not new physical evidence. No candidate CLCE predictor, held-out apparatus observations, historical Hermes attack normalization, Solomon composite weights, or independent baseline PDE is implemented.

## Ledger and recovery
Receipts contain version, UTC event timestamp (machine time, not trusted attestation), parameters, state, fixed-step count since prior receipt, origin and previous hash. Portable SHA-256 canonicalizes sorted object keys. Append checks the previous chain; updates are not exposed. New-run resets append. Replay verifies every hash then executes the stored steps under the previously active controls, checking exact state snapshots. Model source hash is retained on export. An attacker can rewrite and rehash an entire chain; an independently retained head is needed to detect replacement/truncation.

No claims of consciousness, internal memory restoration or mathematical validity follow from the visual metaphors.

## Next experimental step
Supply a declared apparatus geometry, working fluid, units, instruments, pressure boundary conditions and time-synchronised measurements. Freeze an ordinary physical model, preserve test/train separation, compare measured residuals, and test whether a separately defined CLCE candidate earns held-out predictive improvement. Keep physical validation separate from successful software tests.

