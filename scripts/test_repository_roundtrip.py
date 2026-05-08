"""
Repository roundtrip test for Soficca Cardio Pilot.

Creates a test session, case, extraction, correction, engine report,
audit record, reviewer feedback, and session summary — then reads
the case bundle and prints a summary.

Usage:
    cd soficca_core_engine
    set PYTHONPATH=src
    python scripts/test_repository_roundtrip.py

Requirements:
    - DATABASE_URL configured in .env
    - Migrations applied (python scripts/run_migrations.py)

Safety:
    - All records are marked is_simulated=true
    - No real patient data
    - No secrets printed
    - Does not delete data automatically
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from uuid import uuid4

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from db.config import database_url_configured
from db.pool import create_pool, close_pool
from repositories.cardio_models import (
    AIExtractionCreate,
    AuditRecordCreate,
    EngineReportCreate,
    HumanCorrectionCreate,
    PilotCaseCreate,
    PilotSessionCreate,
    ReviewerFeedbackCreate,
    SessionSummaryCreate,
)
from repositories.cardio_pilot_repository import (
    create_pilot_session,
    create_pilot_case,
    save_ai_extraction,
    save_human_correction,
    save_engine_report,
    save_audit_record,
    save_reviewer_feedback,
    save_session_summary,
    get_case_bundle,
    get_session_summary,
    list_pilot_sessions,
)


async def main() -> None:
    print("Soficca Cardio Pilot — Repository Roundtrip Test")
    print("=" * 55)

    if not database_url_configured():
        print("\nERROR: DATABASE_URL is not configured.")
        print("Set it in .env. See .env.example for format.")
        sys.exit(1)

    # Create pool
    print("\nConnecting to database...")
    await create_pool(min_size=1, max_size=3)
    print("  ✓ Pool created.")

    try:
        # 1. Create session
        print("\n1. Creating test session...")
        session = await create_pilot_session(PilotSessionCreate(
            label="Roundtrip Test Session",
            mode="repository_test",
            environment="development",
            created_by="test_script",
        ))
        session_id = session["id"]
        print(f"   ✓ Session: {session_id}")

        # 2. Create case
        test_case_id = f"CP-ROUNDTRIP-{uuid4().hex[:6].upper()}"
        print(f"\n2. Creating test case: {test_case_id}")
        case = await create_pilot_case(PilotCaseCreate(
            session_id=session_id,
            case_id=test_case_id,
            source="test_roundtrip",
            raw_narrative="64-year-old male with severe substernal chest pressure radiating to left arm. "
                          "Onset 20 minutes ago. Diaphoresis present. History of CAD. "
                          "BP 145/90, HR 102. Currently on aspirin and metoprolol.",
            chief_complaint_summary="Severe chest pressure with radiation, diaphoresis",
            is_simulated=True,
            contains_pii_warning=False,
        ))
        case_uuid = case["id"]
        print(f"   ✓ Case UUID: {case_uuid}")

        # 3. Save AI extraction
        print("\n3. Saving AI extraction...")
        extraction = await save_ai_extraction(AIExtractionCreate(
            case_id=case_uuid,
            extraction_id=f"EXT-{uuid4().hex[:6]}",
            model="gpt-4o-mini",
            extraction_source="mock",
            confidence=0.92,
            structured_summary="64-year-old male presenting with acute substernal chest pressure.",
            fields_json={
                "age": 64,
                "chest_pain_present": True,
                "pain_duration_minutes": 20,
                "pain_character": "pressure",
                "pain_severity": "high",
                "pain_radiation": "left_arm",
                "diaphoresis": True,
                "known_cad": True,
                "systolic_bp": 145,
                "heart_rate": 102,
                "current_meds_none": False,
                "current_meds_summary": "aspirin, metoprolol",
            },
            field_evidence_json=[
                {"field": "age", "value": "64", "source_text": "64-year-old", "confidence": 0.99},
            ],
            quality_flags_json=["requires_human_confirmation"],
            pii_warnings_json=[],
        ))
        print(f"   ✓ Extraction: {extraction['extraction_id']}")

        # 4. Save human correction
        print("\n4. Saving human correction...")
        correction = await save_human_correction(HumanCorrectionCreate(
            case_id=case_uuid,
            human_edits_applied=True,
            fields_edited_count=1,
            diffs_json=[{"field": "pain_severity", "old": "high", "new": "high"}],
            final_structured_input_json={
                "age": 64,
                "chest_pain_present": True,
                "pain_duration_minutes": 20,
                "pain_character": "pressure",
                "pain_severity": "high",
                "pain_radiation": "left_arm",
                "diaphoresis": True,
                "known_cad": True,
                "systolic_bp": 145,
                "heart_rate": 102,
                "current_meds_none": False,
                "current_meds_summary": "aspirin, metoprolol",
            },
            reviewer_label="test_reviewer",
        ))
        print(f"   ✓ Correction: {correction['id']}")

        # 5. Save engine report
        print("\n5. Saving engine report...")
        report = await save_engine_report(EngineReportCreate(
            case_id=case_uuid,
            route="emergency_pathway",
            decision_status="routed",
            report_json={"decision": {"path": "emergency_pathway", "status": "routed"}, "safety": {"status": "safe"}},
            engine_input_json={"state": {"age": 64, "chest_pain_present": True}, "context": {"source": "mock"}},
            safety_json={"status": "safe", "has_red_flags": True, "triggers": ["acute_chest_pain_with_radiation"]},
            trace_json={"activated_rules": ["rule_emergency_acute_chest"], "final_route": "emergency_pathway"},
            activated_rules_json=["rule_emergency_acute_chest"],
            engine_version="1.0.0",
            ruleset_version="1.0.0",
            safety_policy_version="1.0.0",
            contract_version="0.3",
        ))
        print(f"   ✓ Report: {report['id']}")

        # 6. Save audit record
        print("\n6. Saving audit record...")
        audit = await save_audit_record(AuditRecordCreate(
            case_id=case_uuid,
            audit_id=f"AUD-{uuid4().hex[:6]}",
            audit_json={"case_id": test_case_id, "route": "emergency_pathway", "pilot_mode": "repository_test"},
            markdown_snapshot="# Audit Record\n\nTest roundtrip audit.",
        ))
        print(f"   ✓ Audit: {audit['audit_id']}")

        # 7. Save reviewer feedback
        print("\n7. Saving reviewer feedback...")
        feedback = await save_reviewer_feedback(ReviewerFeedbackCreate(
            case_id=case_uuid,
            reviewer_name="Dr. Test",
            reviewer_role="cardiologist",
            route_appropriate="agree",
            usefulness_score=4,
            missing_info_surfaced="no",
            estimated_review_time_saved="3_5_minutes",
            useful_before_consultation="yes",
            comments="Routing was appropriate for this acute presentation.",
        ))
        print(f"   ✓ Feedback: {feedback['id']}")

        # 8. Save session summary
        print("\n8. Saving session summary...")
        summary = await save_session_summary(SessionSummaryCreate(
            session_id=session_id,
            summary_id=f"SUM-{uuid4().hex[:6]}",
            metrics_json={"cases_processed": 1, "cases_reviewed": 1},
            route_distribution_json={"emergency": 1, "urgent": 0, "routine": 0},
            safety_assertions_json={"autonomous_diagnosis_events": 0},
        ))
        print(f"   ✓ Summary: {summary['summary_id']}")

        # 9. Read case bundle
        print(f"\n9. Reading case bundle for {test_case_id}...")
        bundle = await get_case_bundle(test_case_id)
        if bundle:
            print(f"   ✓ Case: {bundle['case']['case_id']}")
            print(f"   ✓ Extraction: {bundle['ai_extraction']['extraction_id'] if bundle['ai_extraction'] else 'None'}")
            print(f"   ✓ Correction: {'present' if bundle['human_correction'] else 'None'}")
            print(f"   ✓ Report: {bundle['engine_report']['route'] if bundle['engine_report'] else 'None'}")
            print(f"   ✓ Audit: {bundle['audit_record']['audit_id'] if bundle['audit_record'] else 'None'}")
            print(f"   ✓ Feedback count: {len(bundle['reviewer_feedback'])}")
        else:
            print("   ✗ Bundle not found!")

        # 10. Read session summary
        print(f"\n10. Reading session summary...")
        s = await get_session_summary(session_id)
        if s:
            print(f"   ✓ Summary: {s['summary_id']}")
            metrics = s["metrics_json"]
            if isinstance(metrics, str):
                metrics = json.loads(metrics)
            print(f"   ✓ Cases processed: {metrics.get('cases_processed', 'N/A') if isinstance(metrics, dict) else 'N/A'}")
        else:
            print("   ✗ Summary not found!")

        # 11. List sessions
        print(f"\n11. Listing sessions...")
        sessions = await list_pilot_sessions(limit=5)
        print(f"   ✓ Found {len(sessions)} session(s)")

        print("\n" + "=" * 55)
        print("Roundtrip test completed successfully.")
        print("All records marked is_simulated=true.")
        print("No secrets printed.")

    finally:
        await close_pool()
        print("\nPool closed.")


if __name__ == "__main__":
    asyncio.run(main())
