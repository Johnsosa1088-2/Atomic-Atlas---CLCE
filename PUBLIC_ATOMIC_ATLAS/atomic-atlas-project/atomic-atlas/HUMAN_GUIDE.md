# Atomic Atlas: Human Guide

Documentation edition 0.2 — 8 October 2026. Applies to assembled project checkpoint 010, core 0.0.5.dev1 and source-only harness 0.1. Preparation for release; no publication or independent release approval is implied.

Read [Capabilities and Limitations](CAPABILITIES_AND_LIMITATIONS.md) for evidence boundaries and the shared SVG workflow. The [AI Guide](AI_GUIDE.md) specifies assistant responsibilities.


### 1. Inspect the package before using it

Read `START_HERE.txt`, `CAPABILITIES_AND_LIMITS.txt`, `RUN_RECEIPT.json` and `step9/CAPABILITY_REGISTER.json`. Check which evidence is current and which is inherited. Inspect unfamiliar code before execution. Keep a working copy separate from any historical archive.

Retain a trusted copy of the package digest and any ledger-head anchor outside the working directory. A manifest travelling with a modified archive cannot independently authenticate that archive.

### 2. Prepare a local environment

Use a Python virtual environment. The following commands are intended to be run from the extracted project root in a POSIX shell:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r core/audit/independent/requirements-lock.txt
python verify_candidate.py
```

Node.js must also be installed for the JavaScript example tests. The audit requirements install testing dependencies, not a language model or physical solver. The verification command uses the bundled core source. The wheel installs only the core, not the proposal harness or examples.

Windows and real-browser checks remain release gates. These shell instructions do not establish Windows compatibility. Record your Python, dependency and Node versions, commands, output and failures when reproducing a run.

### 3. Begin with the synthetic review demonstration

```sh
python proposal_harness/demo.py
```

The default demonstration uses a temporary synthetic ledger. To retain a run, use `--output-folder NEW_DIRECTORY`, where that directory does not already exist. Inspect the proposals, review outcomes and reconstructed state. Treat the demonstration as software behavior, not experimental evidence.

### 4. Represent a small domain explicitly

Start with one bounded object or workflow. Use the supplied schemas, fixtures and `step8/domains.json` as contract references. Assign stable IDs to regions, entities, relations and routes. Preserve unknown coordinates and measurements as unknown where the contract permits them; do not invent values to make the representation appear complete.

Run structural validation and model integrity checks. Schema acceptance alone does not check every cross-object endpoint, identity or sequence rule. Do not assume that a label such as “thermal” or “causal” activates a solver.

The proposal harness stores reviewed claims separately from the structural graph. It does not automatically convert prose into a graph or synchronize accepted claims into graph fields.

### 5. Register a source and propose a claim

Keep private sources out of any ledger intended for distribution: source text is stored verbatim. Register an authorized local text source, then copy its returned source ID into your proposal:

```sh
python proposal_harness/cli.py --ledger work/review.jsonl source --locator local/manual-source --text-file YOUR_SOURCE.txt
python proposal_harness/cli.py --ledger work/review.jsonl propose --json-file YOUR_PROPOSAL.json
python proposal_harness/cli.py --ledger work/review.jsonl view
```

Every proposal has exactly these fields:

```json
{
  "id": "proposal-001",
  "key": "example.claim",
  "value": "A source-supported declaration",
  "source_id": "COPY_THE_REGISTERED_SOURCE_ID",
  "summary": "A concise summary, not an exact quotation.",
  "summary_kind": "SUMMARY",
  "uncertainty": [],
  "supersedes": null,
  "revises": null,
  "truth_status": "UNVERIFIED"
}
```

This is an illustrative template; replace the placeholder source ID before use. Use `uncertainty` for unresolved issues. An empty list means you have declared no unresolved issue; it does not prove certainty. The adapter checks this shape with explicit Python guards, not an additional core JSON Schema.

### 6. Review explicitly

Compare the proposal against the source. Check qualifiers, corrections, scope, units and missing information. Copy the proposal digest and current state digest from the current view; do not guess them.

```sh
python proposal_harness/cli.py --ledger work/review.jsonl decide --proposal-id proposal-001 --outcome ACCEPT --reason "Source and scope reviewed" --reviewer "local reviewer" --proposal-digest COPIED_PROPOSAL_DIGEST --state-digest COPIED_STATE_DIGEST
```

Use `REJECT` when appropriate. Acceptance creates a declared state-patch event; rejection leaves accepted state unchanged. Unresolved uncertainty blocks acceptance. A current accepted key requires explicit `supersedes`; a revised proposal can use `revises` to link the earlier same-key proposal. Preserve the prior records.

If a digest is stale, stop and inspect the changed state. Do not remove guards or retry with newly copied hashes without reviewing the difference. Reviewer labels are declarations, not authenticated identities. Blocked attempts are not automatically logged.

### 7. Verify and retain the result

Inspect the reconstructed view and keep the source, ledger, independent head anchor, version information and run output together. The optional `--expected-head` checks a retained ledger head when reopening history. Hashes establish byte association and detect changes relative to anchors; they do not prove source truth or authorship.

Do not delete an abandoned lock automatically. Inspect the history before explicit recovery. No cross-file atomic transaction or universal power-loss guarantee is established.

## Working with SVG references

Use a separate original image, annotation image and legend. Give regions stable IDs, declare view and scale where known, and preserve unknown depth. Begin with one contour or joint, compare source and overlay with adjustable opacity, and retain a baseline before changing geometry. Test that intended attachments remain connected and unaffected regions remain stable.

The complete collaboration cycle and its limits are in [Capabilities and Limitations](CAPABILITIES_AND_LIMITATIONS.md). The [AI Guide](AI_GUIDE.md) describes how an assistant should report proposals and uncertainty. These instructions describe a workflow; they do not mean every SVG adapter or test is already implemented in the current core.

## Documentation scope

Commands reflect the bundled usage contract. This documentation edition does not constitute a new runtime test run; reproduce and retain your own results.
