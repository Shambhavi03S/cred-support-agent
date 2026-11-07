"""Part 1: dataset + RAG core (Tasks 1-5)."""
from collections import Counter

import dataset
from app import config, rag
from app.grounded import grounded_answer


def test_dataset_thresholds():
    recs = dataset.LOAN_APPLICATIONS
    rep = dataset.validate(recs)
    assert len(recs) >= 40
    cc = Counter(r["category"] for r in recs)
    assert all(cc[c] >= 3 for c in dataset.CATEGORIES)
    assert set(r["status"] for r in recs) >= set(dataset.STATUSES)
    assert 10 <= rep["fraud_pct"] <= 30
    assert all(0 <= r["days_since_created"] <= 30 for r in recs)
    for k in ("record_id", "category", "status", "loan_amount_inr", "days_since_created",
              "flagged_for_fraud_review"):
        assert all(k in r for r in recs)


def test_dataset_is_deterministic():
    assert dataset.generate_loan_applications() == dataset.generate_loan_applications()


def test_kb_has_12_plus_docs_of_2_to_5_sentences():
    docs = rag.list_documents()
    assert len(docs) >= 12
    for d in docs:
        assert 2 <= d["sentences"] <= 5, d


def test_chunkers_differ_and_overlap():
    text = rag.load_kb_documents()[0].text
    fixed, sent = rag.chunk_fixed(text), rag.chunk_sentences(text)
    assert len(fixed) >= 2 and len(sent) >= 2
    assert fixed != sent
    # overlap: consecutive fixed chunks share words
    assert set(fixed[0].split()) & set(fixed[1].split())


def test_two_collections_retrieve_sensibly():
    rag.ensure_index()
    for col in (config.COLLECTION_FIXED, config.COLLECTION_SENTENCE):
        hits = rag.retrieve("What is the prepayment penalty on fixed rate loans?", col, 3)
        assert hits[0]["doc_id"] == "kb08_prepayment_penalty"


def test_grounded_answer_and_fallback():
    r = grounded_answer("How do I close my savings account?")
    assert not r["fallback"] and "closure" in r["answer"].lower()
    oos = grounded_answer("Who won the cricket world cup final?")
    assert oos["fallback"] and "don't know" in oos["answer"].lower()
