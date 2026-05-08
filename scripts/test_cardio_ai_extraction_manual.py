#!/usr/bin/env python3
"""
Manual AI extraction harness for Cardio Pilot.

Runs 5 English sample narratives through the extraction endpoint logic
and prints a quality report comparing extracted fields to expected values.

Usage:
    cd soficca_core_engine
    PYTHONPATH=src OPENAI_API_KEY=sk-... python scripts/test_cardio_ai_extraction_manual.py

If OPENAI_API_KEY is not set, the script will exit safely with a message.
This is NOT part of CI — it requires real API calls.
"""

from __future__ import annotations

import os
import sys
import json
from typing import Any, Dict, List, Optional

# ── Check for API key early ──────────────────────────────────────

if not os.environ.get("OPENAI_API_KEY"):
    print("=" * 60)
    print("OPENAI_API_KEY is not set.")
    print("This script requires a real OpenAI API key to run.")
    print("Set it in your environment and try again:")
    print("  OPENAI_API_KEY=sk-... python scripts/test_cardio_ai_extraction_manual.py")
    print("=" * 60)
    sys.exit(0)

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api.routers.cardio_extract_router import (
    CardioPilotExtractRequest,
    CardioPilotExtractResponse,
    CardioAIRawOutput,
    DISALLOWED_FIELDS,
    _call_openai,
    strip_disallowed_fields,
)

# ── Test cases ───────────────────────────────────────────────────

CASES: List[Dict[str, Any]] = [
    {
        "name": "1. Emergency",
        "text": "64-year-old patient with severe pressure-like chest pain for 10 minutes radiating to the left arm. Patient experienced syncope during the episode. BP 120/74, HR 96. No known CAD. Not on cardiac medications.",
        "expected": {
            "age": 64,
            "chest_pain_present": True,
            "pain_character": "pressure",
            "pain_duration_minutes": 10,
            "pain_severity": "high",
            "pain_radiation": "left_arm",
            "syncope": True,
            "dyspnea": None,
            "systolic_bp": 120,
            "heart_rate": 96,
            "known_cad": False,
            "current_meds_none": True,
        },
    },
    {
        "name": "2. Urgent",
        "text": "63-year-old patient with moderate chest pressure for 20 minutes radiating to the jaw. Pain started with exertion. No syncope, no dyspnea. BP 126/80, HR 88. One cardiovascular risk factor.",
        "expected": {
            "age": 63,
            "chest_pain_present": True,
            "pain_character": "pressure",
            "pain_duration_minutes": 20,
            "pain_severity": "moderate",
            "pain_radiation": "jaw",
            "exertional_chest_pain": True,
            "syncope": False,
            "dyspnea": False,
            "systolic_bp": 126,
            "heart_rate": 88,
            "cv_risk_factors_count": 1,
        },
    },
    {
        "name": "3. Routine",
        "text": "60-year-old patient with low-grade pressure-like chest pain lasting 15 minutes. No radiation, no exertional component, no diaphoresis, no dyspnea, no syncope. BP 122/76, HR 78. No known CAD, no prior MI. One cardiovascular risk factor.",
        "expected": {
            "age": 60,
            "chest_pain_present": True,
            "pain_character": "pressure",
            "pain_duration_minutes": 15,
            "pain_severity": "low",
            "pain_radiation": "none",
            "exertional_chest_pain": False,
            "diaphoresis": False,
            "dyspnea": False,
            "syncope": False,
            "systolic_bp": 122,
            "heart_rate": 78,
            "known_cad": False,
            "prior_mi": False,
            "cv_risk_factors_count": 1,
        },
    },
    {
        "name": "4. Needs more info",
        "text": "62-year-old patient reports chest pain but does not provide duration, severity, radiation, or cardiovascular history. BP 124/80, HR 80. No current medications.",
        "expected": {
            "age": 62,
            "chest_pain_present": True,
            "pain_duration_minutes": None,
            "pain_severity": None,
            "pain_radiation": None,
            "known_cad": None,
            "prior_mi": None,
            "systolic_bp": 124,
            "heart_rate": 80,
            "current_meds_none": True,
        },
    },
    {
        "name": "5. Conflict",
        "text": "59-year-old patient denies chest pain but reports high-severity pressure radiating to the jaw for 20 minutes during exertion. BP 122/80, HR 84. No current medications.",
        "expected": {
            "age": 59,
            "chest_pain_present": False,
            "pain_character": "pressure",
            "pain_duration_minutes": 20,
            "pain_severity": "high",
            "pain_radiation": "jaw",
            "exertional_chest_pain": True,
            "systolic_bp": 122,
            "heart_rate": 84,
            "current_meds_none": True,
        },
        "expect_conflicts": True,
    },
]


# ── Runner ───────────────────────────────────────────────────────


def run_case(case: Dict[str, Any], model: str) -> Dict[str, Any]:
    """Run a single extraction case and produce a quality report."""
    name = case["name"]
    text = case["text"]
    expected = case["expected"]
    expect_conflicts = case.get("expect_conflicts", False)

    print(f"\n{'=' * 60}")
    print(f"  {name}")
    print(f"{'=' * 60}")
    print(f"  Narrative: {text[:100]}...")

    try:
        raw_output = _call_openai(text, model)
    except Exception as e:
        print(f"  ERROR: {e}")
        return {"name": name, "status": "error", "error": str(e)}

    raw_dict = raw_output.model_dump()
    safety_warnings = strip_disallowed_fields(raw_dict)
    cleaned = CardioAIRawOutput.model_validate(raw_dict)

    fields = cleaned.fields.model_dump()

    # Compare
    matches = 0
    mismatches: List[str] = []
    for key, expected_val in expected.items():
        actual_val = fields.get(key, "__MISSING__")
        if actual_val == expected_val:
            matches += 1
        else:
            mismatches.append(f"    {key}: expected={expected_val!r}, got={actual_val!r}")

    total = len(expected)
    match_pct = (matches / total * 100) if total > 0 else 0

    # Print results
    print(f"\n  Confidence: {cleaned.confidence}")
    print(f"  Language: {cleaned.language_detected}")
    print(f"  Missing fields: {cleaned.missing_fields}")
    print(f"  Possible conflicts: {cleaned.possible_conflicts}")
    print(f"  Warnings: {cleaned.warnings}")
    if safety_warnings:
        print(f"  SAFETY WARNINGS: {safety_warnings}")
    print(f"  Field evidence count: {len(cleaned.field_evidence)}")

    # New intelligence fields
    print(f"\n  --- AI Intelligence Layer ---")
    summary = cleaned.structured_clinical_summary
    print(f"  Summary: {summary[:120]}..." if len(summary) > 120 else f"  Summary: {summary}")
    # Check summary for disallowed language
    summary_lower = summary.lower()
    summary_clean = not any(
        phrase in summary_lower
        for phrase in ["diagnos", "prescri", "recommend", "route to", "emergency decision"]
    )
    print(f"  Summary avoids diagnosis/routing language: {'PASS' if summary_clean else 'FAIL'}")

    mi = cleaned.missing_information
    print(f"  Missing info — required_for_routing: {mi.required_for_routing}")
    print(f"  Missing info — clinically_useful: {mi.clinically_useful}")
    print(f"  Missing info — unconfirmed: {mi.unconfirmed}")
    print(f"  Completion questions: {len(cleaned.completion_questions)}")
    for i, q in enumerate(cleaned.completion_questions, 1):
        print(f"    {i}. {q}")
    print(f"  Quality flags: {cleaned.extraction_quality_flags}")
    print(f"  PII warnings: {cleaned.pii_warnings}")

    print(f"\n  Match: {matches}/{total} ({match_pct:.0f}%)")
    if mismatches:
        print(f"  Mismatches:")
        for m in mismatches:
            print(m)

    if expect_conflicts:
        if cleaned.possible_conflicts:
            print(f"  Conflict detection: PASS (conflicts found)")
        else:
            print(f"  Conflict detection: FAIL (expected conflicts, none found)")

    # Check for disallowed fields
    disallowed_found = []
    for k in fields:
        if k in DISALLOWED_FIELDS:
            disallowed_found.append(k)
    if disallowed_found:
        print(f"  DISALLOWED FIELDS FOUND: {disallowed_found}")
    else:
        print(f"  Disallowed fields: None (clean)")

    # Print extracted key fields
    print(f"\n  Extracted fields:")
    for key in sorted(fields.keys()):
        val = fields[key]
        marker = ""
        if key in expected:
            if val == expected[key]:
                marker = " ✓"
            else:
                marker = " ✗"
        if val is not None:
            print(f"    {key}: {val!r}{marker}")

    return {
        "name": name,
        "status": "ok",
        "matches": matches,
        "total": total,
        "match_pct": match_pct,
        "mismatches": len(mismatches),
        "confidence": cleaned.confidence,
        "conflicts_found": len(cleaned.possible_conflicts),
        "disallowed_found": len(disallowed_found),
        "safety_warnings": len(safety_warnings),
        "evidence_count": len(cleaned.field_evidence),
        "has_summary": bool(cleaned.structured_clinical_summary),
        "summary_clean": summary_clean,
        "completion_questions": len(cleaned.completion_questions),
        "quality_flags": len(cleaned.extraction_quality_flags),
        "pii_warnings": len(cleaned.pii_warnings),
    }


def main():
    model = os.environ.get("CARDIO_EXTRACTION_MODEL", "gpt-4o-mini")
    print(f"Cardio AI Extraction Manual Harness")
    print(f"Model: {model}")
    print(f"Cases: {len(CASES)}")

    results = []
    for case in CASES:
        result = run_case(case, model)
        results.append(result)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  SUMMARY")
    print(f"{'=' * 60}")

    ok_results = [r for r in results if r["status"] == "ok"]
    err_results = [r for r in results if r["status"] == "error"]

    if ok_results:
        total_matches = sum(r["matches"] for r in ok_results)
        total_fields = sum(r["total"] for r in ok_results)
        avg_pct = total_matches / total_fields * 100 if total_fields > 0 else 0
        avg_confidence = sum(r["confidence"] for r in ok_results) / len(ok_results)
        total_disallowed = sum(r["disallowed_found"] for r in ok_results)
        total_safety = sum(r["safety_warnings"] for r in ok_results)

        summaries_ok = sum(1 for r in ok_results if r.get("has_summary"))
        summaries_clean = sum(1 for r in ok_results if r.get("summary_clean"))
        total_qs = sum(r.get("completion_questions", 0) for r in ok_results)
        total_flags = sum(r.get("quality_flags", 0) for r in ok_results)
        total_pii = sum(r.get("pii_warnings", 0) for r in ok_results)

        print(f"  Successful: {len(ok_results)}/{len(results)}")
        print(f"  Overall field match: {total_matches}/{total_fields} ({avg_pct:.0f}%)")
        print(f"  Average confidence: {avg_confidence:.2f}")
        print(f"  Disallowed fields found: {total_disallowed}")
        print(f"  Safety filter warnings: {total_safety}")
        print(f"  Summaries generated: {summaries_ok}/{len(ok_results)}")
        print(f"  Summaries clean (no diagnosis/route): {summaries_clean}/{summaries_ok}")
        print(f"  Total completion questions: {total_qs}")
        print(f"  Total quality flags: {total_flags}")
        print(f"  Total PII warnings: {total_pii}")

        for r in ok_results:
            status = "PASS" if r["mismatches"] == 0 else f"MISMATCH ({r['mismatches']})"
            print(f"    {r['name']}: {r['match_pct']:.0f}% — {status}")

    if err_results:
        print(f"\n  Errors: {len(err_results)}")
        for r in err_results:
            print(f"    {r['name']}: {r['error']}")

    print()


if __name__ == "__main__":
    main()
