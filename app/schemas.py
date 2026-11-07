"""Task 9: structured output schema. Pydantic model -> JSON Schema, plus jsonschema
validation in code for every agent response."""
from __future__ import annotations

import json
from typing import Literal, Optional

import jsonschema
from pydantic import BaseModel, Field

from .config import ROOT

Intent = Literal["policy_question", "loan_status", "clarification", "blocked", "unknown"]


class SourceRef(BaseModel):
    doc_id: str
    title: str
    similarity: float = Field(ge=-1.0, le=1.0)
    snippet: str


class LoanInfo(BaseModel):
    record_id: str
    category: str
    status: str
    loan_amount_inr: int
    days_since_created: int
    flagged_for_fraud_review: bool
    escalation_score: float = Field(ge=0.0, le=1.0)
    escalate: bool


class Guardrails(BaseModel):
    pii_masked: list[str] = []
    injection_detected: bool = False
    grounded: bool = True
    fallback_triggered: bool = False


class AgentResponse(BaseModel):
    conversation_id: str
    trace_id: Optional[str] = None
    intent: Intent
    route: Literal["rag", "loan_tool", "clarify", "blocked"]
    answer: str = Field(min_length=1)
    sources: list[SourceRef] = []
    loan: Optional[LoanInfo] = None
    guardrails: Guardrails
    model: str
    nodes_executed: list[str] = []


AGENT_RESPONSE_SCHEMA = AgentResponse.model_json_schema()
(ROOT / "schemas").mkdir(exist_ok=True)
(ROOT / "schemas" / "agent_response.schema.json").write_text(
    json.dumps(AGENT_RESPONSE_SCHEMA, indent=2), encoding="utf-8")


def validate_response(payload: dict) -> dict:
    """Validate against the JSON Schema (raises jsonschema.ValidationError)."""
    jsonschema.validate(instance=payload, schema=AGENT_RESPONSE_SCHEMA)
    return payload
