#!/usr/bin/env python3
"""
Example A Public Test Runner
Dependency-free reference test for the neutral Atomic Atlas example bundle.

This runner does NOT simulate real fluid pressure, CFD, FEA, or silicone mechanics.
It validates only the declared neutral topology, state/event vocabulary, budgets,
SVG grouping plan, and public-core guardrails included in this bundle.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

PASS = "PASS"
FAIL = "FAIL"

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_json(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))

def check(condition: bool, label: str, detail: str = ""):
    status = PASS if condition else FAIL
    suffix = f" — {detail}" if detail else ""
    print(f"[{status}] {label}{suffix}")
    return bool(condition)

def main() -> int:
    mapping = load_json("EXAMPLE_A_ATLAS_MAPPING.json")
    expected = load_json("EXPECTED_TEST_RESULTS.json")

    print("ATLAS EXAMPLE A — SOFT ROBOTIC FINGER PUBLIC TEST 002")
    print("=" * 62)

    results = []

    results.append(check(
        mapping["example_id"] == "ATLAS_EXAMPLE_A_SOFT_ROBOTIC_FINGER_TEST_002",
        "example identity"
    ))
    results.append(check(mapping["public_core_compatible"] is None, "core integration remains untested"))
    results.append(check(mapping["physical_validation"] is False, "physical validation remains false"))

    mat = mapping["material_profile"]
    results.append(check(
        mat["vendor_locked"] is False and mat["grade_locked"] is False,
        "material remains profile-level and vendor-neutral"
    ))

    structure = mapping["structure"]
    regions = set(structure["regions"])
    entities = set(structure["entities"])
    route = structure["route"]
    states = set(structure["states"])
    events = set(structure["events"])
    svg_groups = set(mapping["svg_groups"])
    budgets = set(mapping["budgets"])
    guardrails = set(mapping["guardrails"])

    required_regions = {"base_region", "inlet_region", "chamber_region", "shell_region", "tip_region"}
    required_entities = {
        "base_mount", "pressure_interface", "internal_route",
        "pocket_01", "pocket_02", "pocket_03", "pocket_04", "outer_shell", "strain_limiting_layer", "feeler_tip"
    }
    required_states = {"idle", "primed", "pocketed_low", "pocketed_medium", "pocketed_high", "contacting", "released"}
    required_events = {"prime", "inflate", "partial_inflate", "full_inflate", "contact", "deflate", "release"}
    required_budgets = {"pressure_budget", "active_pocket_count", "deformation_budget", "contact_budget"}

    results.append(check(required_regions <= regions, "required regions present"))
    results.append(check(required_entities <= entities, "required entities present"))
    results.append(check(required_states <= states, "required states present"))
    results.append(check(required_events <= events, "required events present"))
    results.append(check(required_budgets <= budgets, "neutral budgets present"))

    results.append(check(
        route == [
            "pressure_interface", "internal_route",
            "pocket_01", "pocket_02", "pocket_03", "pocket_04", "feeler_tip"
        ],
        "declared topological route preserved"
    ))

    required_svg = {
        "base_mount", "inlet_tube", "pressure_interface", "outer_shell",
        "strain_limiting_layer", "internal_route",
        "pocket_01", "pocket_02", "pocket_03", "pocket_04",
        "feeler_tip", "route_overlay", "candidate_overlay", "state_overlay"
    }
    results.append(check(required_svg <= svg_groups, "declared SVG grouping vocabulary present"))

    results.append(check(
        "declared route does not establish physical flow" in guardrails,
        "connection != physical flow"
    ))
    results.append(check(
        "budget arithmetic does not establish mechanics" in guardrails,
        "budget arithmetic != physical mechanics"
    ))
    results.append(check(
        "material choice does not belong to neutral core" in guardrails,
        "material choice remains outside neutral core"
    ))
    results.append(check(
        "image is a reference asset, not validated geometry" in guardrails,
        "image reference != validated geometry"
    ))

    asset = ROOT / "soft_robotic_finger_asset.png"
    results.append(check(asset.exists() and asset.stat().st_size > 0, "image asset present"))

    # Verify package file hashes against the manifest, excluding the manifest itself.
    manifest = load_json("PUBLIC_TEST_MANIFEST.json")
    file_entries = manifest["files"]
    hash_ok = True
    for entry in file_entries:
        p = ROOT / entry["name"]
        if not p.exists() or sha256(p) != entry["sha256"]:
            hash_ok = False
            break
    results.append(check(hash_ok, "manifest file hashes"))

    html_path = ROOT / "index.html"
    html_text = html_path.read_text(encoding="utf-8") if html_path.exists() else ""
    results.append(check(html_path.exists(), "interactive HTML present"))
    results.append(check(all(f'pocket_0{i}' in html_text for i in range(1,5)), "four SVG fluid pockets present"))
    results.append(check('feeler_tip' in html_text, "feeler tip SVG group present"))
    results.append(check(all(x in html_text for x in ["inflateAll","deflateAll","progressive","resetBtn"]), "interactive action controls present"))
    results.append(check("<script>" in html_text and "<svg" in html_text, "self-contained SVG/JS demo contract"))
    results.append(check(all(f'joint_0{i}' in html_text for i in range(1,5)), "four nested bend joints present"))
    results.append(check(all(f'bend_line_0{i}' in html_text for i in range(1,5)), "four bend guide lines present"))
    results.append(check(all(f'bend_arc_0{i}' in html_text for i in range(1,5)), "four bend-limit arcs present"))
    results.append(check(all(x in html_text for x in ["autoBend","bend1","bend2","bend3","bend4"]), "auto/manual bend controls present"))
    results.append(check("edgeColor" in html_text and "#d64545" in html_text, "bend-limit edge coloring present"))
    results.append(check("Highest limit use" in html_text, "limit utilization readout present"))

    passed = sum(results)
    total = len(results)
    print("-" * 62)
    print(f"RESULT: {passed}/{total} checks passed")

    expected_total = expected["expected_check_count"]
    if total != expected_total:
        print(f"[FAIL] runner check count changed: expected {expected_total}, got {total}")
        return 2

    if not all(results):
        return 1

    print("[PASS] Example A satisfies its declared neutral public-test contract.")
    print("NOTE: This does not validate real pneumatic, elastomer, pressure, or contact physics.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
