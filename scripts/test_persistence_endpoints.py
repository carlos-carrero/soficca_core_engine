"""
Manual endpoint roundtrip test for Cardio Pilot persistence (Stage 3D).

Uses httpx against a running FastAPI server at localhost:8000.

Usage:
    1. Start the backend:
       cd soficca_core_engine
       set PYTHONPATH=src
       uvicorn api.main:app --reload --port 8000

    2. In another terminal:
       cd soficca_core_engine
       python scripts/test_persistence_endpoints.py

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


def main() -> None:
    print("Soficca Cardio Pilot — Persistence Endpoint Test")
    print("=" * 55)

    # Verify server
    try:
        r = httpx.get(f"{BASE_HOST}/healthz", timeout=5)
        r.raise_for_status()
    except Exception:
        print(f"\nERROR: Backend not reachable at {BASE_HOST}")
        print("Start it with: uvicorn api.main:app --reload --port 8000")
        print("Or set API_PORT=<port> before running this script.")
        sys.exit(1)

    print("✓ Backend is running.\n")

    # 1. Create session
    print("1. POST /sessions")
    r = httpx.post(f"{BASE}/sessions", json={
        "label": "Endpoint Test Session",
        "mode": "endpoint_test",
        "environment": "development",
        "created_by": "test_script",
    })
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    session = r.json()["session"]
    session_id = session["id"]
    print(f"   ✓ Session: {session_id}")

    # 2. List sessions
    print("\n2. GET /sessions")
    r = httpx.get(f"{BASE}/sessions?limit=5")
    assert r.status_code == 200
    print(f"   ✓ Found {r.json()['count']} session(s)")

    # 3. Create case bundle
    test_case_id = f"CP-EP-{uuid4().hex[:6].upper()}"
    print(f"\n3. POST /cases — {test_case_id}")
    r = httpx.post(f"{BASE}/cases", json={
        "session_id": session_id,
        "case_id": test_case_id,
        "raw_narrative": "72-year-old female with acute onset dyspnea and pleuritic chest pain. "
                         "History of DVT. SpO2 91%. HR 110.",
        "chief_complaint_summary": "Acute dyspnea with pleuritic chest pain",
        "is_simulated": True,
        "ai_extraction": {
            "extraction_id": f"EXT-{uuid4().hex[:6]}",
            "model": "gpt-4o-mini",
            "extraction_source": "mock",
            "confidence": 0.88,
            "fields_json": {
                "age": 72,
                "chest_pain_present": True,
                "dyspnea": True,
                "pain_character": "pleuritic",
                "spo2": 91,
                "heart_rate": 110,
            },
        },
        "engine_report": {
            "route": "emergency_pathway",
            "decision_status": "routed",
            "report_json": {"decision": {"path": "emergency_pathway"}},
            "engine_input_json": {"state": {"age": 72}},
            "engine_version": "1.0.0",
        },
        "audit_record": {
            "audit_id": f"AUD-{uuid4().hex[:6]}",
            "audit_json": {"case_id": test_case_id, "route": "emergency_pathway"},
        },
    })
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    saved = r.json()
    print(f"   ✓ Case UUID: {saved['case_uuid']}")
    print(f"   ✓ Saved: {json.dumps(saved['saved'])}")

    # 4. Duplicate conflict
    print(f"\n4. POST /cases — duplicate {test_case_id}")
    r = httpx.post(f"{BASE}/cases", json={
        "case_id": test_case_id,
        "raw_narrative": "duplicate",
    })
    assert r.status_code == 409, f"Expected 409, got {r.status_code}"
    print(f"   ✓ Got 409 Conflict (expected)")

    # 5. Read case bundle
    print(f"\n5. GET /cases/{test_case_id}")
    r = httpx.get(f"{BASE}/cases/{test_case_id}")
    assert r.status_code == 200
    bundle = r.json()
    print(f"   ✓ Case: {bundle['case']['case_id']}")
    print(f"   ✓ Extraction: {bundle['ai_extraction']['extraction_id'] if bundle['ai_extraction'] else 'None'}")
    print(f"   ✓ Report route: {bundle['engine_report']['route'] if bundle['engine_report'] else 'None'}")

    # 6. Add reviewer feedback
    print(f"\n6. POST /cases/{test_case_id}/review")
    r = httpx.post(f"{BASE}/cases/{test_case_id}/review", json={
        "reviewer_name": "Dr. Endpoint Test",
        "reviewer_role": "cardiologist",
        "route_appropriate": "agree",
        "usefulness_score": 5,
        "comments": "Automated endpoint test — simulated data.",
    })
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    fb = r.json()
    print(f"   ✓ Feedback saved: {fb['feedback']['id']}")
    print(f"   ✓ Status updated: {fb['case_status_updated']}")

    # 7. Read case bundle again (should have feedback now)
    print(f"\n7. GET /cases/{test_case_id} (after review)")
    r = httpx.get(f"{BASE}/cases/{test_case_id}")
    bundle = r.json()
    print(f"   ✓ Feedback count: {len(bundle['reviewer_feedback'])}")
    print(f"   ✓ Case status: {bundle['case']['current_status']}")

    # 8. Not found
    print(f"\n8. GET /cases/NONEXISTENT")
    r = httpx.get(f"{BASE}/cases/NONEXISTENT")
    assert r.status_code == 404
    print(f"   ✓ Got 404 (expected)")

    # 9. Save session summary
    print(f"\n9. POST /sessions/{session_id}/summary")
    r = httpx.post(f"{BASE}/sessions/{session_id}/summary", json={
        "summary_id": f"SUM-{uuid4().hex[:6]}",
        "metrics_json": {"cases_processed": 1, "cases_reviewed": 1},
        "route_distribution_json": {"emergency": 1},
        "safety_assertions_json": {"autonomous_diagnosis_events": 0},
    })
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    print(f"   ✓ Summary: {r.json()['summary']['summary_id']}")

    # 10. Read session summary
    print(f"\n10. GET /sessions/{session_id}/summary")
    r = httpx.get(f"{BASE}/sessions/{session_id}/summary")
    assert r.status_code == 200
    print(f"   ✓ Summary found: {r.json()['summary']['summary_id']}")

    # 11. List cases
    print(f"\n11. GET /cases?session_id={session_id}")
    r = httpx.get(f"{BASE}/cases", params={"session_id": session_id})
    assert r.status_code == 200
    print(f"   ✓ Cases in session: {r.json()['count']}")

    print("\n" + "=" * 55)
    print("All endpoint tests passed.")
    print("All records marked is_simulated=true.")
    print("No secrets printed.")


if __name__ == "__main__":
    main()
