import json
import pytest
from src.monitoring.stats_agent import _stats_for, run


def test_stats_for_empty():
    result = _stats_for([])
    assert result["count"] == 0
    assert result["total_tokens"] == 0


def test_stats_for_single_value():
    result = _stats_for([100])
    assert result["count"] == 1
    assert result["total_tokens"] == 100
    assert result["avg_tokens"] == 100.0
    assert result["min_tokens"] == 100
    assert result["max_tokens"] == 100
    assert result["std_tokens"] == 0.0


def test_stats_for_multiple_values():
    result = _stats_for([100, 200, 300])
    assert result["count"] == 3
    assert result["total_tokens"] == 600
    assert result["avg_tokens"] == 200.0
    assert result["min_tokens"] == 100
    assert result["max_tokens"] == 300


def test_run_no_classifications_file(tmp_path, monkeypatch):
    import src.monitoring.stats_agent as agent
    monkeypatch.setattr(agent, "CLASSIFICATIONS_FILE", tmp_path / "classifications.json")
    monkeypatch.setattr(agent, "STATS_FILE", tmp_path / "stats.json")
    run()
    assert not (tmp_path / "stats.json").exists()


def test_run_generates_stats_file(tmp_path, monkeypatch):
    import src.monitoring.stats_agent as agent

    classifications = [
        {"filename": "a.pdf", "category": "prices", "confidence": "high",
         "classified_by": "title", "collection": "prices_vs", "token_count": 1000},
        {"filename": "b.pdf", "category": "quotes", "confidence": "medium",
         "classified_by": "title", "collection": "quotes_vs", "token_count": 500},
        {"filename": "c.pdf", "category": "prices", "confidence": "high",
         "classified_by": "content (pdf)", "collection": "prices_vs", "token_count": 2000},
    ]
    clf_file = tmp_path / "classifications.json"
    clf_file.write_text(json.dumps(classifications))
    stats_file = tmp_path / "stats.json"

    monkeypatch.setattr(agent, "CLASSIFICATIONS_FILE", clf_file)
    monkeypatch.setattr(agent, "STATS_FILE", stats_file)
    monkeypatch.setattr(agent, "REPORTS_DIR", tmp_path)

    run()

    assert stats_file.exists()
    stats = json.loads(stats_file.read_text())

    assert stats["overall"]["total_files"] == 3
    assert stats["overall"]["total_tokens"] == 3500
    assert stats["overall"]["max_tokens"] == 2000
    assert stats["overall"]["min_tokens"] == 500
    assert set(stats["overall"]["categories_found"]) == {"prices", "quotes"}
    assert stats["overall"]["high_confidence"] == 2
    assert stats["overall"]["medium_confidence"] == 1

    assert stats["by_category"]["prices"]["count"] == 2
    assert stats["by_category"]["prices"]["total_tokens"] == 3000
    assert stats["by_category"]["quotes"]["count"] == 1


def test_run_empty_classifications(tmp_path, monkeypatch):
    import src.monitoring.stats_agent as agent
    clf_file = tmp_path / "classifications.json"
    clf_file.write_text("[]")
    monkeypatch.setattr(agent, "CLASSIFICATIONS_FILE", clf_file)
    monkeypatch.setattr(agent, "STATS_FILE", tmp_path / "stats.json")
    run()
    assert not (tmp_path / "stats.json").exists()
