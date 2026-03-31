import json
from pathlib import Path

from cardio_triage_v1.validation import evaluate_readiness


def test_manual_deferred_pending_data_stays_conflict_without_safety_override() -> None:
    payload = json.loads(Path('examples/cardio_v1_manual_requests.json').read_text(encoding='utf-8'))
    deferred = next(item for item in payload['manual_requests'] if item['id'] == 'DEFERRED_PENDING_DATA')

    report = evaluate_readiness(deferred['request'])

    assert report['decision']['decision_type'] == 'DEFERRED_PENDING_DATA'
    assert report['decision']['status'] == 'CONFLICT'
    assert report['safety']['status'] == 'CLEAR'
    assert report['safety']['action'] == 'NONE'
    assert report['trace']['final_route'] is None
