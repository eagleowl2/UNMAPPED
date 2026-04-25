"""Tests for taxonomy crosswalk engine."""
import pytest
from app.core.taxonomy import TaxonomyGraph, CrosswalkResult


@pytest.fixture
def graph():
    return TaxonomyGraph()


def test_phone_repair_crosswalk(graph):
    result = graph.crosswalk("fix phones in Accra")
    assert result is not None
    assert result.primary.code == "7421"
    assert result.primary.framework == "ISCO-08"
    assert result.primary.match_score > 0.9


def test_coding_crosswalk(graph):
    result = graph.crosswalk("learned coding on YouTube")
    assert result is not None
    assert result.primary.code == "2512"


def test_secondary_crosswalk_populated(graph):
    result = graph.crosswalk("phone repair technician")
    assert result is not None
    # Should have ESCO and/or O*NET secondary
    assert len(result.secondary) >= 1
    frameworks = [s.framework for s in result.secondary]
    assert any(f in frameworks for f in ("ESCO", "O*NET"))


def test_unknown_phrase_returns_none(graph):
    result = graph.crosswalk("xxxxunknownxxxxskillxxxx")
    assert result is None


def test_local_override_takes_priority(graph):
    graph.register_local_overrides([
        {"local_label": "phone fixer", "canonical_code": "7421", "framework": "ISCO-08"}
    ])
    result = graph.crosswalk("I am a phone fixer")
    assert result is not None
    assert result.primary.match_score == 0.98


def test_tailoring_crosswalk(graph):
    result = graph.crosswalk("tailoring and sewing")
    assert result is not None
    assert result.primary.code == "7436"
