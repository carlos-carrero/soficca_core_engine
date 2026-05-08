"""
Full persisted flow test for Cardio Pilot (Stage 3F QA).

Tests the complete persistence pipeline: session → case with all nested
resources → reviewer feedback → session summary → readback.

Usage:
    1. Start the backend:
       cd soficca_core_engine
       $env:PYTHONPATH = "src"
       uvicorn api.main:app --reload --port 8000

    2. In another terminal:
       cd soficca_core_engine
       python scripts/test_full_persisted_flow.py

Requirements:
    - Backend running on http://127.0.0.1:8000
    - DATABASE_URL configured in .env
    - Migrations applied
    - httpx installed (pip install httpx)

Safety:
    - All records are is_simulated=true
    - No real patient data
    - No secrets printed
    - Does not delete data
"""

from __future__ import annotations

import json
import sys
from uuid import uuid4

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(1)

import os

PORT = os.environ.get("API_PORT", "8000")
BASE_HOST = f"http://127.0.0.1:{PORT}"
BASE = f"{BASE_HOST}/v1/cardio/pilot"

PASS = 0
FAIL = 0


def check(label: str, passed: bool, detail: str = "") -> None:
    global PASS, FAIL
    if passed:
        PASS += 1
        print(f"  ✓ {label}")
    else:
        FAIL += 1
        print(f"  ✗ {label} — {detail}")


def main() -> None:
    global PASS, FAIL
    print("=" * 60)
    print("Soficca Cardio Pilot — Full Persisted Flow QA")
    print("=" * 60)

    # ── 0. Health check ──────────────────────────────────────────
    print("\n0. Health check")
    try:
        r = httpx.get(f"{BASE_HOST}/healthz", timeout=5)
        r.raise_for_status()
        check("Backend reachable", True)
    except Exception as e:
        check("Backend reachable", False, str(e))
        print("\nERROR: Start backend before running this script.")
        sys.exit(1)

    # ── 1. Create session ────────────────────────────────────────
    print("\n1. Create persisted session")
    r = httpx.post(f"{BASE}/sessions", json={
        "label": "Full Flow QA Session",
        "mode": "qa_test",
        "environment": "development",
        "created_by": "test_full_persisted_flow",
    })
    check("POST /sessions → 201", r.status_code == 201, f"got {r.status_code}")
    session = r.json().get("session", {})
    session_id = session.get("id", "")
    session_sid = session.get("session_id", session_id)
    check("Session ID present", bool(session_id), "missing id")
    print(f"    session_id: {session_sid}")

    # ── 2. List sessions ─────────────────────────────────────────
    print("\n2. List sessions")
    r = httpx.get(f"{BASE}/sessions?limit=5")
    check("GET /sessions → 200", r.status_code == 200, f"got {r.status_code}")
    check("Count ≥ 1", r.json().get("count", 0) >= 1, f"count={r.json().get('count')}")

    # ── 3. Create full case bundle ───────────────────────────────
    test_case_id = f"CP-QA-{uuid4().hex[:6].upper()}"
    print(f"\n3. Create case bundle: {test_case_id}")
    r = httpx.post(f"{BASE}/cases", json={
        "session_id": session_id,
        "case_id": test_case_id,
        "source": "free_text",
        "raw_narrative": (
            "68-year-old male with acute substernal chest pain radiating to "
            "left arm for 20 minutes. History of HTN, DM2. Diaphoretic. "
            "BP 150/90, HR 105. ECG shows ST elevation in leads II, III, aVF."
        ),
        "chief_complaint_summary": "Acute chest pain with ST elevation",
        "current_status": "routed",
        "final_route": "emergency_pathway",
        "decision_status": "routed",
        "extraction_source": "mock",
        "routing_source": "mock_fallback",
        "is_simulated": True,
        "ai_extraction": {
            "extraction_id": f"EXT-{uuid4().hex[:6]}",
            "model": "gpt-4o-mini",
            "extraction_source": "mock",
            "confidence": 0.92,
            "fields_json": {
                "age": 68,
                "sex": "male",
                "chest_pain_present": True,
                "pain_character": "pressure",
                "pain_radiation": "left_arm",
                "duration_minutes": 20,
                "diaphoresis": True,
                "systolic_bp": 150,
                "diastolic_bp": 90,
                "heart_rate": 105,
                "ecg_st_changes": True,
            },
        },
        "human_correction": {
            "correction_id": f"HC-{uuid4().hex[:6]}",
            "corrected_by": "qa_script",
            "fields_edited_count": 1,
            "original_fields_json": {"age": 67},
            "corrected_fields_json": {"age": 68},
            "final_structured_input_json": {
                "age": 68,
                "chest_pain_present": True,
                "ecg_st_changes": True,
            },
        },
        "engine_report": {
            "route": "emergency_pathway",
            "decision_status": "routed",
            "report_json": {
                "decision": {
                    "path": "emergency_pathway",
                    "status": "routed",
                    "reason_primary": "ST elevation with acute chest pain",
                },
            },
            "engine_input_json": {"state": {"age": 68, "ecg_st_changes": True}},
            "engine_version": "1.0.0",
            "ruleset_version": "cardio_triage_v1",
        },
        "audit_record": {
            "audit_id": f"AUD-{uuid4().hex[:6]}",
            "audit_json": {
                "case_id": test_case_id,
                "route": "emergency_pathway",
                "no_diagnosis_generated": True,
                "no_prescription_generated": True,
            },
        },
    })
    check("POST /cases → 201", r.status_code == 201, f"got {r.status_code}: {r.text[:200]}")
    if r.status_code == 201:
        saved = r.json().get("saved", {})
        check("case saved", saved.get("case", False))
        check("ai_extraction saved", saved.get("ai_extraction", False))
        check("human_correction saved", saved.get("human_correction", False))
        check("engine_report saved", saved.get("engine_report", False))
        check("audit_record saved", saved.get("audit_record", False))
        print(f"    case_uuid: {r.json().get('case_uuid', '?')}")

    # ── 4. Duplicate conflict ────────────────────────────────────
    print(f"\n4. Duplicate case: {test_case_id}")
    r = httpx.post(f"{BASE}/cases", json={
        "case_id": test_case_id,
        "raw_narrative": "duplicate attempt",
    })
    check("POST /cases duplicate → 409", r.status_code == 409, f"got {r.status_code}")

    # ── 5. Read case bundle ──────────────────────────────────────
    print(f"\n5. Read case bundle: {test_case_id}")
    r = httpx.get(f"{BASE}/cases/{test_case_id}")
    check("GET /cases/{id} → 200", r.status_code == 200, f"got {r.status_code}")
    if r.status_code == 200:
        b = r.json()
        check("case present", b.get("case") is not None)
        check("ai_extraction present", b.get("ai_extraction") is not None)
        check("human_correction present", b.get("human_correction") is not None)
        check("engine_report present", b.get("engine_report") is not None)
        check("audit_record present", b.get("audit_record") is not None)
        check("session_id matches", str(b["case"].get("session_id", "")) == str(session_id),
              f"expected {session_id}, got {b['case'].get('session_id')}")

    # ── 6. Not found ─────────────────────────────────────────────
    print("\n6. Case not found")
    r = httpx.get(f"{BASE}/cases/NONEXISTENT-CASE-ID")
    check("GET /cases/NONEXISTENT → 404", r.status_code == 404, f"got {r.status_code}")

    # ── 7. Reviewer feedback ─────────────────────────────────────
    print(f"\n7. Reviewer feedback: {test_case_id}")
    r = httpx.post(f"{BASE}/cases/{test_case_id}/review", json={
        "reviewer_name": "Dr. QA Reviewer",
        "reviewer_role": "cardiologist",
        "route_appropriate": "agree",
        "usefulness_score": 4,
        "missing_info_surfaced": "all_key_fields_present",
        "safety_flags_assessment": "no",
        "estimated_review_time_saved": "3_5_minutes",
        "useful_before_consultation": "yes",
        "comments": "Full flow QA test — simulated data only.",
    })
    check("POST /cases/{id}/review → 201", r.status_code == 201, f"got {r.status_code}: {r.text[:200]}")
    if r.status_code == 201:
        fb = r.json()
        check("feedback saved", fb.get("feedback") is not None)
        check("case_status_updated", fb.get("case_status_updated", False) is True,
              f"got {fb.get('case_status_updated')}")

    # ── 8. Read bundle after review ──────────────────────────────
    print(f"\n8. Read bundle after review: {test_case_id}")
    r = httpx.get(f"{BASE}/cases/{test_case_id}")
    if r.status_code == 200:
        b = r.json()
        fb_count = len(b.get("reviewer_feedback", []))
        check("reviewer_feedback count ≥ 1", fb_count >= 1, f"count={fb_count}")
        check("case status = reviewed", b["case"].get("current_status") == "reviewed",
              f"status={b['case'].get('current_status')}")

    # ── 9. Review for nonexistent case ───────────────────────────
    print("\n9. Review for nonexistent case")
    r = httpx.post(f"{BASE}/cases/NONEXISTENT-CASE/review", json={
        "route_appropriate": "agree",
        "usefulness_score": 3,
    })
    check("POST review nonexistent → 404", r.status_code == 404, f"got {r.status_code}")

    # ── 10. Session summary ──────────────────────────────────────
    summary_id = f"SUM-QA-{uuid4().hex[:6]}"
    print(f"\n10. Save session summary: {summary_id}")
    r = httpx.post(f"{BASE}/sessions/{session_id}/summary", json={
        "summary_id": summary_id,
        "metrics_json": {
            "cases_processed": 1,
            "cases_reviewed": 1,
            "agreement_rate": 1.0,
            "average_usefulness_score": 4.0,
            "autonomous_diagnosis_events": 0,
            "autonomous_prescription_events": 0,
        },
        "route_distribution_json": {"emergency": 1, "urgent": 0, "routine": 0},
        "reviewer_metrics_json": {
            "cases_sent_to_reviewer": 1,
            "cases_reviewed": 1,
            "agreement_rate": 1.0,
        },
        "workflow_impact_json": {
            "estimated_review_time_saved_distribution": {"3_5_minutes": 1},
        },
        "governance_metrics_json": {
            "autonomous_diagnosis_events": 0,
            "autonomous_prescription_events": 0,
            "ai_route_decisions": 0,
        },
        "safety_assertions_json": {
            "autonomous_diagnosis_events": 0,
            "autonomous_prescription_events": 0,
            "physician_review_required": True,
        },
        "case_summaries_json": [
            {
                "case_id": test_case_id,
                "route": "emergency_pathway",
                "review_status": "reviewed",
                "no_diagnosis_generated": True,
            },
        ],
    })
    check("POST /sessions/{id}/summary → 201", r.status_code == 201,
          f"got {r.status_code}: {r.text[:200]}")

    # ── 11. Read session summary ─────────────────────────────────
    print(f"\n11. Read session summary")
    r = httpx.get(f"{BASE}/sessions/{session_id}/summary")
    check("GET /sessions/{id}/summary → 200", r.status_code == 200, f"got {r.status_code}")
    if r.status_code == 200:
        s = r.json().get("summary", {})
        check("summary_id matches", s.get("summary_id") == summary_id,
              f"expected {summary_id}, got {s.get('summary_id')}")

    # ── 12. List cases by session ────────────────────────────────
    print(f"\n12. List cases by session")
    r = httpx.get(f"{BASE}/cases", params={"session_id": session_id})
    check("GET /cases?session_id → 200", r.status_code == 200, f"got {r.status_code}")
    if r.status_code == 200:
        check("cases count ≥ 1", r.json().get("count", 0) >= 1,
              f"count={r.json().get('count')}")

    # ── Summary ──────────────────────────────────────────────────
    print("\n" + "=" * 60)
    total = PASS + FAIL
    print(f"Results: {PASS}/{total} passed, {FAIL} failed")
    print(f"All records marked is_simulated=true.")
    print(f"No secrets printed. No real patient data.")
    if FAIL > 0:
        print("\n⚠ Some checks FAILED. Review output above.")
        sys.exit(1)
    else:
        print("\n✓ Full persisted flow QA passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
