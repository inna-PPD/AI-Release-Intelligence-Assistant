from src.rag.retrieval_eval import is_relevant
from src.rag.search import matches, qdrant_filter, rrf, tokenize


def test_tokenize_keeps_ids_and_versions_whole_and_in_parts():
    tokens = tokenize("Fixed #9508 in pac 1.46.1 for cnt_invoice via svc-contoso-flows")
    assert {"9508", "1.46.1", "cnt_invoice", "svc-contoso-flows"} <= set(tokens)
    assert {"invoice", "contoso", "46"} <= set(tokens)  # частини складених токенів теж шукаються


def test_rrf_rewards_agreement_between_rankings():
    fused = rrf([[1, 2, 3], [3, 1, 4]], k=60)
    order = [idx for idx, _ in fused]
    assert order[0] == 1 and order[1] == 3  # 1 і 3 є в обох списках
    assert set(order) == {1, 2, 3, 4}


def test_metadata_filters():
    chunk = {"product": "CoE Starter Kit", "source": "github_release", "date": "2025-10-15", "version": "October 2025"}
    assert matches(chunk, None)
    assert matches(chunk, {"product": ["CoE Starter Kit", "ALM"], "date_from": "2025-01-01"})
    assert not matches(chunk, {"source": "synthetic"})
    assert not matches(chunk, {"date_to": "2025-06-30"})
    assert not matches({"date": None}, {"date_from": "2025-01-01"})


def test_qdrant_filter_builds_conditions():
    f = qdrant_filter({"product": "ALM", "date_from": "2025-01-01"})
    keys = [c.key for c in f.must]
    assert keys == ["product", "date_int"]
    assert f.must[1].range.gte == 20250101 and f.must[1].range.lte is None
    assert qdrant_filter(None) is None


def test_relevance_by_doc_and_phrase():
    q = {"relevant": [{"doc_id": "guide-1.5", "contains": "1.44 або новішої"}]}
    assert is_relevant({"doc_id": "guide-1.5", "text": "pac CLI версії 1.44 або новішої"}, q)
    assert not is_relevant({"doc_id": "guide-1.4", "text": "pac CLI версії 1.44 або новішої"}, q)
    assert not is_relevant({"doc_id": "guide-1.5", "text": "pac CLI версії 1.32"}, q)
