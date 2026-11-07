"""Task 6: check_loan_application_status + designed escalation score.

Deliberately depends only on dataset.py so the MCP server stays lightweight.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dataset import get_record  # noqa: E402

# Kept as literals (mirrors app/config.py) so this module has no heavy imports.
W_FRAUD, W_AGE, MAX_DAYS, ESCALATION_THRESHOLD = 0.5, 0.5, 30, 0.70


def escalation_score(flagged: bool, days_since_created: int) -> float:
    """score = 0.5*fraud_flag + 0.5*(days_since_created/30), clipped to [0, 1]."""
    recency = max(0.0, min(1.0, days_since_created / MAX_DAYS))
    return round(max(0.0, min(1.0, W_FRAUD * float(flagged) + W_AGE * recency)), 4)


def check_loan_application_status(record_id: str) -> dict:
    """Look up a loan application by record ID (e.g. "LA-1005").

    Returns the application's status, loan_amount_inr and a designed
    escalation_score in [0, 1] computed as
    0.5 * flagged_for_fraud_review + 0.5 * (days_since_created / 30).
    Escalation is recommended when the score is >= 0.70.
    If the record does not exist, found=False and an error message is returned.
    """
    rec = get_record(record_id) if isinstance(record_id, str) else None
    if rec is None:
        return {"found": False, "record_id": str(record_id),
                "error": f"No loan application found with record_id '{record_id}'."}
    score = escalation_score(rec["flagged_for_fraud_review"], rec["days_since_created"])
    return {
        "found": True,
        "record_id": rec["record_id"],
        "category": rec["category"],
        "status": rec["status"],
        "loan_amount_inr": rec["loan_amount_inr"],
        "days_since_created": rec["days_since_created"],
        "flagged_for_fraud_review": rec["flagged_for_fraud_review"],
        "escalation_score": score,
        "escalation_threshold": ESCALATION_THRESHOLD,
        "escalate": score >= ESCALATION_THRESHOLD,
    }
