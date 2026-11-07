"""Query sets used by calibration (Task 4), chunk comparison (Task 5) and the RAG triad (Task 13).
gold = parent KB documents that genuinely answer the query (hand-labelled)."""

# Task 4/5: in-scope queries with gold parent documents
IN_SCOPE = [
    ("What is the minimum monthly income needed for a personal loan?", ["kb01_loan_eligibility"]),
    ("How is the EMI calculated on a reducing balance loan?", ["kb02_emi_calculation"]),
    ("What is the late payment fee on the credit card?", ["kb03_credit_card_fees"]),
    ("Which documents are required for KYC verification?", ["kb04_kyc_documents"]),
    ("How do I dispute an unauthorised card transaction?", ["kb05_fraud_dispute"]),
    ("What is the process to close my savings account?", ["kb06_account_closure"]),
    ("What interest rate will I get on a home loan?", ["kb07_interest_rate_slabs"]),
    ("Is there a penalty for prepaying a fixed-rate loan?", ["kb08_prepayment_penalty"]),
    ("What factors lower my credit score?", ["kb10_credit_score_impact"]),
    ("Who can sign in a jointly operated account?", ["kb11_joint_account_rules"]),
]

# Deliberately out of scope (must trigger the fallback)
OUT_OF_SCOPE = [
    "Who won the cricket world cup final?",
    "What is the best recipe for chicken biryani?",
    "How do I reset my Netflix password?",
    "Explain quantum entanglement in simple words.",
    "What is the capital of France?",
]

# Task 13: 15-query RAG-triad set: every required KB topic + >=2 out-of-scope/edge
TRIAD_QUERIES = [
    ("Which loan types have income and age eligibility rules?", ["kb01_loan_eligibility"], False),
    ("How do I calculate my monthly EMI?", ["kb02_emi_calculation"], False),
    ("What fees does the credit card carry?", ["kb03_credit_card_fees"], False),
    ("What KYC documents do I need to submit?", ["kb04_kyc_documents"], False),
    ("What happens after I report a fraudulent transaction?", ["kb05_fraud_dispute"], False),
    ("What do I need to do to close my account?", ["kb06_account_closure"], False),
    ("What are the interest rate slabs for loans?", ["kb07_interest_rate_slabs"], False),
    ("What is the prepayment penalty on my loan?", ["kb08_prepayment_penalty"], False),
    ("What minimum balance must I maintain?", ["kb09_minimum_balance"], False),
    ("How does my payment history affect my credit score?", ["kb10_credit_score_impact"], False),
    ("What are the rules for a joint account?", ["kb11_joint_account_rules"], False),
    ("Can a non-resident Indian open an NRE account?", ["kb12_nri_account_eligibility"], False),
    ("When should a loan application be escalated to a senior officer?",
     ["kb14_escalation_policy"], False),
    # out-of-scope / edge (expected: fallback)
    ("Who won the cricket world cup final?", [], True),
    ("Please tell me the weather forecast for Mumbai tomorrow.", [], True),
]

# Task 5 (set B): queries whose answer spans 2-3 documents (multi-gold), so Precision@3 /
# Recall@3 can actually discriminate between chunking strategies. Gold = hand-labelled by content.
MULTI_GOLD = [
    ("What happens if I miss a payment on my loan or credit card?",
     ["kb03_credit_card_fees", "kb15_grievance_late_payment", "kb10_credit_score_impact"]),
    ("What documents and income do I need to apply for a home loan?",
     ["kb01_loan_eligibility", "kb04_kyc_documents"]),
    ("What fees or penalties can be charged on a loan?",
     ["kb08_prepayment_penalty", "kb15_grievance_late_payment"]),
    ("How does a fraud flag affect my loan application?",
     ["kb05_fraud_dispute", "kb14_escalation_policy"]),
    ("Can an NRI open a joint account and what KYC is needed?",
     ["kb11_joint_account_rules", "kb12_nri_account_eligibility", "kb04_kyc_documents"]),
    ("Which savings accounts need a minimum balance and how do I close one?",
     ["kb09_minimum_balance", "kb06_account_closure"]),
]
