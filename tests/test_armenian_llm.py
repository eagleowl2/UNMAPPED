# coding: utf-8
"""
Tests for the Armenian normalisation module (v0.3.4 — OpenRouter backend).

Covers:
  * Tier-A deterministic abbreviation expander (offline, always on).
  * Tier-B LLM normaliser graceful-degradation contract:
        - Missing OPENROUTER_API_KEY → disabled, no exceptions.
        - Mocked successful httpx response → augments parser output.
        - Mocked HTTP failure → silent fallback.
  * Parser integration: previously failing abbreviated translator input
    now produces a translation/interpretation skill via Tier-A only.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core import armenian_llm
from app.core.armenian_llm import (
    ArmenianLLMNormaliser,
    expand_armenian_abbreviations,
    has_armenian_script,
    normalise_for_skills,
)
from app.core.parser import EvidenceParser


# ---------------------------------------------------------------------------
# has_armenian_script
# ---------------------------------------------------------------------------


class TestHasArmenianScript:
    def test_armenian_letters(self):
        assert has_armenian_script("Իմ անունը Անի է")

    def test_pure_english(self):
        assert not has_armenian_script("I am a translator")

    def test_pure_russian(self):
        assert not has_armenian_script("Я переводчик")

    def test_empty(self):
        assert not has_armenian_script("")

    def test_mixed(self):
        assert has_armenian_script("Idram and Իդրամ")


# ---------------------------------------------------------------------------
# Tier A — abbreviation expander
# ---------------------------------------------------------------------------


class TestExpandArmenianAbbreviations:
    def test_translator_abbrev_expanded(self):
        text = "Արամ, 35 տ., Երևան: թ.-ն. ռ. ու հ.:"
        out = expand_armenian_abbreviations(text)
        assert "թարգմանիչ" in out, out

    def test_programmer_abbrev_expanded(self):
        text = "Ես ծ. ե., Python ու JavaScript."
        out = expand_armenian_abbreviations(text)
        assert "ծրագրավորող" in out, out

    def test_tailor_abbrev_expanded(self):
        text = "Մարիամե Հ., Gyumri: կ. և ձ., 7 տ. փ.:"
        out = expand_armenian_abbreviations(text)
        assert "դերձակ" in out or "կարուհի" in out, out

    def test_driver_abbrev_expanded(self):
        text = "Աշոտ վ. է, Gyumri-ից Yerevan."
        out = expand_armenian_abbreviations(text)
        assert "վարորդ" in out, out

    def test_gym_to_gyumri(self):
        text = "Անի, ուսուցիչ, Gym., 4 տ. փ."
        out = expand_armenian_abbreviations(text)
        assert "Գյումրի" in out, out

    def test_no_armenian_no_change(self):
        text = "I am an English translator in Yerevan."
        assert expand_armenian_abbreviations(text) == text

    def test_idempotent_on_full_armenian_words(self):
        text = "Ես ուսուցիչ եմ Երևանում:"
        assert expand_armenian_abbreviations(text) == text


# ---------------------------------------------------------------------------
# Tier B — LLM normaliser graceful degradation
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_llm_singleton(monkeypatch):
    """Reset the module-level singleton between tests so monkeypatched env
    variables actually take effect."""
    ArmenianLLMNormaliser._instance = None
    yield
    ArmenianLLMNormaliser._instance = None


def _strip_keys(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPEN_ROUTER_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def _mock_openrouter_response(text: str) -> MagicMock:
    """Build a MagicMock response that mimics the OpenRouter chat-completions shape."""
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "choices": [{"message": {"content": text}}],
    }
    return response


class TestArmenianLLMNormaliserGracefulDegradation:
    def test_disabled_without_api_key(self, monkeypatch):
        _strip_keys(monkeypatch)
        norm = ArmenianLLMNormaliser.get()
        assert norm.available is False
        result = norm.normalise("Արամ, թ.-ն. ռ. ու հ.")
        assert result.english_phrases == ""
        assert result.source == "disabled"

    def test_explicit_disable_flag(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-fake")
        monkeypatch.setattr(armenian_llm, "_LLM_DISABLED", True)
        norm = ArmenianLLMNormaliser.get()
        assert norm.available is False

    def test_normalise_with_mocked_openrouter(self, monkeypatch):
        """Inject a mock httpx client and verify the parser augments
        text with the returned English phrases."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-fake")
        monkeypatch.setattr(armenian_llm, "_LLM_DISABLED", False)
        monkeypatch.setattr(armenian_llm, "_LLM_BACKEND", "openrouter")

        norm = ArmenianLLMNormaliser.get()
        assert norm.available is True

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = False
        mock_client.post.return_value = _mock_openrouter_response("translator, interpreter")

        with patch.object(armenian_llm.httpx, "Client", return_value=mock_client):
            result = norm.normalise("Արամ, թ.-ն. ռ. ու հ.")
        assert result.source == "openrouter"
        assert "translator" in result.english_phrases
        # Second call should hit the in-process cache.
        result2 = norm.normalise("Արամ, թ.-ն. ռ. ու հ.")
        assert result2.source == "cache"

    def test_normalise_swallows_http_exception(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-fake")
        monkeypatch.setattr(armenian_llm, "_LLM_DISABLED", False)
        monkeypatch.setattr(armenian_llm, "_LLM_BACKEND", "openrouter")

        norm = ArmenianLLMNormaliser.get()

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = False
        mock_client.post.side_effect = RuntimeError("network down")

        with patch.object(armenian_llm.httpx, "Client", return_value=mock_client):
            result = norm.normalise("Արամ թ.-ն.")
        assert result.source == "error"
        assert result.english_phrases == ""

    def test_none_response_yields_empty(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-fake")
        monkeypatch.setattr(armenian_llm, "_LLM_DISABLED", False)
        monkeypatch.setattr(armenian_llm, "_LLM_BACKEND", "openrouter")
        norm = ArmenianLLMNormaliser.get()

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = False
        mock_client.post.return_value = _mock_openrouter_response("NONE")

        with patch.object(armenian_llm.httpx, "Client", return_value=mock_client):
            result = norm.normalise("Hello world")
        assert result.english_phrases == ""


# ---------------------------------------------------------------------------
# normalise_for_skills entry point
# ---------------------------------------------------------------------------


class TestNormaliseForSkills:
    def test_no_armenian_is_noop(self):
        text = "I am an English teacher in Accra."
        out, source = normalise_for_skills(text)
        assert out == text
        assert source == "noop"

    def test_armenian_runs_tier_a_only_when_skills_already_found(self):
        text = "Արամ, թ.-ն. ռ. ու հ."
        out, source = normalise_for_skills(text, skills_already_found=5)
        assert source == "tier-a"
        assert "թարգմանիչ" in out

    def test_armenian_with_no_llm_falls_back_to_tier_a(self, monkeypatch):
        _strip_keys(monkeypatch)
        text = "Արամ, թ.-ն. ռ. ու հ."
        out, source = normalise_for_skills(text, skills_already_found=0)
        assert source == "tier-a"
        assert "թարգմանիչ" in out


# ---------------------------------------------------------------------------
# End-to-end parser integration
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def am_parser():
    return EvidenceParser(country_code="AM", context_tag="urban_informal")


class TestAbbreviatedArmenianParserIntegration:
    """Inputs that the previous E5-embedder pipeline missed entirely."""

    def test_abbreviated_translator(self, am_parser):
        text = "Արամ, 35 տ., Երևան: թ.-ն. ռ. ու հ.:"
        result = am_parser.parse_for_profile(text)
        labels = " ".join(s["name"].lower() for s in result["skills"])
        assert "transl" in labels or "interpr" in labels, labels

    def test_abbreviated_programmer(self, am_parser):
        text = "Ես ծ. ե., Python ու JavaScript."
        result = am_parser.parse_for_profile(text)
        labels = " ".join(s["name"].lower() for s in result["skills"])
        assert any(
            tok in labels for tok in ("programm", "software", "develop", "python")
        ), labels

    def test_abbreviated_translator_via_llm_path(self, am_parser, monkeypatch):
        """Force Tier-A to be a no-op so the LLM-augmentation path runs."""
        monkeypatch.setattr(
            armenian_llm, "expand_armenian_abbreviations", lambda t: t
        )
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-fake")
        monkeypatch.setattr(armenian_llm, "_LLM_DISABLED", False)
        monkeypatch.setattr(armenian_llm, "_LLM_BACKEND", "openrouter")

        ArmenianLLMNormaliser._instance = None

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = False
        mock_client.post.return_value = _mock_openrouter_response(
            "translator, interpreter"
        )

        with patch.object(armenian_llm.httpx, "Client", return_value=mock_client):
            text = "Արամ, թ.-ն. ռ. ու հ."
            result = am_parser.parse_for_profile(text)
        labels = " ".join(s["name"].lower() for s in result["skills"])
        assert "transl" in labels or "interpr" in labels, labels
        ArmenianLLMNormaliser._instance = None
