"""Seeded, deterministic loan-application dataset generator (Part 1, Task 1).

Run `python dataset.py` to print the validation report.  All people / IDs are
fabricated.  Design choices (also stated in README.md):

* SEED = 7, N_RECORDS = 60
* CATEGORY_WEIGHTS / STATUS_WEIGHTS below
* loan_amount_inr ranges per category (see AMOUNT_RANGES_INR)
* Fraud-review probability 0.20 (validated to land in the 10-30 % band)
"""
from __future__ import annotations

import random
from collections import Counter
from datetime import date, timedelta

SEED = 7
N_RECORDS = 60
REFERENCE_DATE = date(2026, 11, 1)  # fixed so "created_date" is reproducible

CATEGORIES = ["Personal Loan", "Home Loan", "Auto Loan", "Education Loan", "Business Loan"]
STATUSES = ["Submitted", "Under Review", "Approved", "Rejected", "Disbursed"]

CATEGORY_WEIGHTS = {"Personal Loan": 0.28, "Home Loan": 0.18, "Auto Loan": 0.20,
                    "Education Loan": 0.14, "Business Loan": 0.20}
STATUS_WEIGHTS = {"Submitted": 0.22, "Under Review": 0.26, "Approved": 0.20,
                  "Rejected": 0.14, "Disbursed": 0.18}

# Realistic ticket sizes for Indian retail lending, in INR.  Reasoning (one
# sentence): ranges mirror typical retail-bank ticket sizes -- small unsecured
# personal loans up to large secured home loans -- so amounts differ by product.
AMOUNT_RANGES_INR = {
    "Personal Loan": (50_000, 1_500_000),
    "Home Loan": (1_500_000, 15_000_000),
    "Auto Loan": (300_000, 2_500_000),
    "Education Loan": (200_000, 3_000_000),
    "Business Loan": (500_000, 10_000_000),
}
FRAUD_PROBABILITY = 0.20
AMOUNT_ROUNDING = 5_000

_FIRST = ["Aarav", "Diya", "Kabir", "Meera", "Rohan", "Sana", "Vikram", "Ishita",
          "Arjun", "Neha", "Karan", "Priya", "Rahul", "Tanvi", "Yash", "Zoya"]
_LAST = ["Sharma", "Iyer", "Khan", "Patel", "Nair", "Reddy", "Gupta", "Mehta",
         "Singh", "Das", "Bose", "Joshi", "Menon", "Kulkarni", "Verma", "Rao"]


def generate_loan_applications(seed: int = SEED, n: int = N_RECORDS) -> list[dict]:
    rng = random.Random(seed)
    cats, cw = list(CATEGORY_WEIGHTS), list(CATEGORY_WEIGHTS.values())
    stats, sw = list(STATUS_WEIGHTS), list(STATUS_WEIGHTS.values())
    records = []
    for i in range(n):
        category = rng.choices(cats, cw)[0]
        status = rng.choices(stats, sw)[0]
        lo, hi = AMOUNT_RANGES_INR[category]
        amount = int(round(rng.uniform(lo, hi) / AMOUNT_ROUNDING) * AMOUNT_ROUNDING)
        days = rng.randint(0, 30)
        records.append({
            "record_id": f"LA-{1001 + i}",
            "category": category,
            "status": status,
            "loan_amount_inr": amount,
            "days_since_created": days,
            "flagged_for_fraud_review": rng.random() < FRAUD_PROBABILITY,
            # extra, fabricated metadata
            "customer_id": f"CUST-{rng.randint(10000, 99999)}",
            "applicant_name": f"{rng.choice(_FIRST)} {rng.choice(_LAST)}",
            "created_date": (REFERENCE_DATE - timedelta(days=days)).isoformat(),
        })
    return records


LOAN_APPLICATIONS: list[dict] = generate_loan_applications()


def validate(records: list[dict]) -> dict:
    """Check every structural threshold from the brief; raises on violation."""
    cat_counts = Counter(r["category"] for r in records)
    stat_counts = Counter(r["status"] for r in records)
    fraud_pct = 100.0 * sum(r["flagged_for_fraud_review"] for r in records) / len(records)
    assert len(records) >= 40, "need >= 40 records"
    for c in CATEGORIES:
        assert cat_counts[c] >= 3, f"category {c} has < 3 records"
    for s in STATUSES:
        assert stat_counts[s] >= 1, f"status {s} missing"
    assert 10.0 <= fraud_pct <= 30.0, f"fraud % {fraud_pct:.1f} outside 10-30"
    assert all(0 <= r["days_since_created"] <= 30 for r in records)
    assert len({r["record_id"] for r in records}) == len(records)
    return {"count": len(records), "per_category": dict(cat_counts),
            "per_status": dict(stat_counts), "fraud_pct": round(fraud_pct, 2)}


def get_record(record_id: str) -> dict | None:
    rid = record_id.strip().upper()
    return next((r for r in LOAN_APPLICATIONS if r["record_id"] == rid), None)


if __name__ == "__main__":
    rep = validate(LOAN_APPLICATIONS)
    print(f"Records generated      : {rep['count']} (seed={SEED})")
    print("Count per category     :")
    for c in CATEGORIES:
        print(f"   {c:<15} {rep['per_category'][c]}")
    print("Count per status       :")
    for s in STATUSES:
        print(f"   {s:<15} {rep['per_status'][s]}")
    print(f"Fraud-review flagged % : {rep['fraud_pct']}  (required band 10-30)")
    print("Validation             : PASS")
