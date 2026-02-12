# api/main.py
"""
Soficca Core API (decision-first, v0.3)

This is a thin FastAPI adapter over the deterministic engine.
- No chat UI
- No sessions/DB
- No turn logging
- No assistant messages
- Output is the Decision Report contract (v0.3)
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

from soficca_core.engine import evaluate as evaluate_decision


# -----------------------------
# Contract: Decision Report v0.3 (JSON Schema)
# -----------------------------
DECISION_REPORT_V0_3_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://soficca.ai/schemas/decision_report_v0_3.json",
    "title": "Soficca Decision Report v0.3",
    "type": "object",
    "additionalProperties": False,
    "required": ["ok", "errors", "versions", "decision", "safety", "trace"],
    "properties": {
        "ok": {"type": "boolean"},
        "errors": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["code", "message", "path"],
                "properties": {
                    "code": {"type": "string"},
                    "message": {"type": "string"},
                    "path": {"type": "string"},
                    "meta": {"type": "object"},
                },
            },
        },
        "versions": {
            "type": "object",
            "additionalProperties": False,
            "required": ["engine", "ruleset", "safety_policy"],
            "properties": {
                "engine": {"type": "string"},
                "ruleset": {"type": "string"},
                "safety_policy": {"type": "string"},
            },
        },
        "decision": {
            "type": "object",
            "additionalProperties": False,
            "required": ["status", "path", "flags", "reasons", "recommendations"],
            "properties": {
                "status": {"type": "string", "enum": ["DECIDED", "NEEDS_MORE_INFO", "CONFLICT", "ESCALATED"]},
                "path": {
                    "type": ["string", "null"],
                    "enum": ["PATH_MORE_QUESTIONS", "PATH_EVAL_FIRST", "PATH_MEDS_OK", "PATH_ESCALATE_HUMAN", None],
                },
                "flags": {"type": "array", "items": {"type": "string"}},
                "reasons": {"type": "array", "items": {"type": "string"}},
                "recommendations": {"type": "array", "items": {"type": "string"}},
                "required_fields": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "If NEEDS_MORE_INFO, fields required to progress.",
                },
            },
        },
        "safety": {
            "type": "object",
            "additionalProperties": False,
            "required": ["status", "action", "triggers", "user_guidance_required_fields", "policy_version"],
            "properties": {
                "status": {"type": "string", "enum": ["CLEAR", "TRIGGERED"]},
                "action": {"type": "string", "enum": ["NONE", "OVERRIDE_ESCALATE", "OVERRIDE_BLOCK_RECS"]},
                "triggers": {"type": "array", "items": {"type": "string"}},
                "user_guidance_required_fields": {"type": "array", "items": {"type": "string"}},
                "policy_version": {"type": "string"},
            },
        },
        "trace": {
            "type": "object",
            "additionalProperties": False,
            "required": ["policy_trace", "rules_evaluated", "rules_triggered", "evidence", "uncertainty_notes"],
            "properties": {
                "policy_trace": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["evaluated", "triggered"],
                    "properties": {
                        "evaluated": {"type": "array", "items": {"type": "string"}},
                        "triggered": {"type": "array", "items": {"type": "string"}},
                    },
                },
                "rules_evaluated": {"type": "array", "items": {"type": "string"}},
                "rules_triggered": {"type": "array", "items": {"type": "string"}},
                "evidence": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["value", "source", "recency_days", "confidence", "contradiction"],
                        "properties": {
                            "value": {},
                            "source": {"type": "string", "enum": ["USER", "DEVICE", "CLINICIAN", "UNKNOWN"]},
                            "recency_days": {"type": ["number", "null"]},
                            "confidence": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
                            "contradiction": {"type": "boolean"},
                        },
                    },
                },
                "uncertainty_notes": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
}


# -----------------------------
# API Models
# -----------------------------
class EvaluateRequest(BaseModel):
    """
    Decision-first input.
    - 'state' can be partial; the engine decides if it's sufficient.
    - 'context' is optional metadata (source, recency).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "state": {
                        "frequency": "daily",
                        "desire": "low",
                        "stress": "high",
                        "morning_erection": "sometimes",
                        "wants_meds": True,
                        "country": "CO",
                        "safety_flags": [],
                    },
                    "context": {"source": "USER", "recency_days": 1},
                },
                {
                    "state": {
                        "frequency": "daily",
                        "desire": "low",
                        "stress": "high",
                        "morning_erection": "none",
                        "wants_meds": True,
                        "country": "CO",
                        "safety_flags": ["CHEST_PAIN"],
                    },
                    "context": {"source": "USER", "recency_days": 0},
                },
            ]
        }
    )

    state: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)


class BatchEvaluateRequest(BaseModel):
    items: List[EvaluateRequest] = Field(default_factory=list)


class BatchEvaluateResponse(BaseModel):
    results: List[Dict[str, Any]]


# -----------------------------
# App
# -----------------------------
app = FastAPI(title="Soficca Core API (Decision-First)", version="0.3.0")


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "service": "Soficca Core API",
        "mode": "decision_first",
        "version": "0.3.0",
        "docs": "/docs",
        "contract": "/contract",
        "health": "/healthz",
    }


@app.get("/healthz")
def healthz() -> Dict[str, Any]:
    return {"ok": True, "service": "Soficca Core API", "mode": "decision_first"}


@app.get("/contract")
def contract() -> Dict[str, Any]:
    # Returns the canonical Decision Report schema (v0.3)
    return DECISION_REPORT_V0_3_SCHEMA


@app.post("/v1/evaluate")
def v1_evaluate(payload: EvaluateRequest) -> Dict[str, Any]:
    report = evaluate_decision({"state": payload.state, "context": payload.context})

    # Adapter invariant enforcement (demo-safe)
    decision = report.get("decision", {})
    if (
        decision.get("status") == "DECIDED"
        and decision.get("path") == "PATH_MORE_QUESTIONS"
        and not decision.get("required_fields")
    ):
        decision["path"] = None

    return report


@app.post("/v1/evaluate/batch", response_model=BatchEvaluateResponse)
def v1_evaluate_batch(payload: BatchEvaluateRequest) -> BatchEvaluateResponse:
    results: List[Dict[str, Any]] = []
    for item in payload.items:
        results.append(evaluate_decision({"state": item.state, "context": item.context}))
    return BatchEvaluateResponse(results=results)


if __name__ == "__main__":
    import uvicorn

    # Optional convenience entrypoint (PyCharm "Run api/main.py").
    # Your primary dev command remains: uvicorn api.main:app --reload
    uvicorn.run(app, host="127.0.0.1", port=8000)

