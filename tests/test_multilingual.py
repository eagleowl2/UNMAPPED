# coding: utf-8
"""
Multilingual parser tests — v0.3.1.

Covers:
  - Twi (Akan) alias hits for Ghana urban-informal
  - Ga alias hits for Ghana urban-informal
  - Armenian script + alias hits for Armenia
  - Russian alias hits for Armenia
  - AliasMatcher unit tests
  - Locale swap (GH ↔ AM) correctness
  - Canonical alias registry loaded from both profiles
"""
import pytest
from app.core.multilingual import AliasMatcher, candidate_phrases
from app.core.parser import EvidenceParser

# ---------------------------------------------------------------------------
# Shared parsers (module-scoped for speed)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def gh_parser():
    return EvidenceParser(country_code="GH", context_tag="urban_informal")


@pytest.fixture(scope="module")
def am_parser():
    return EvidenceParser(country_code="AM", context_tag="urban_informal")


# ---------------------------------------------------------------------------
# Twi (Akan) alias detection — Ghana
# ---------------------------------------------------------------------------

TWI_INPUTS = [
    # kayayei head-load porter
    (
        "Me din de Abena, kayayo at Agbogbloshie market, I carry loads every morning.",
        ["porter", "carrier", "kayayo"],
    ),
    # trotro driver
    (
        "My name is Kofi, I drive trotro on the Accra-Kumasi route.",
        ["trotro", "transport", "driv"],
    ),
    # MoMo agent
    (
        "Ama Serwaa does MoMo agent work at Circle.",
        ["momo", "mobile", "money", "agent"],
    ),
    # Twi trader
    (
        "Adwoa is a dwadini at Makola, she sells okra and tomatoes.",
        ["trad", "vendor", "market", "sell"],
    ),
    # Ga chop-bar cook
    (
        "Korkor runs a chop bar in Nima, cooking banku and okra soup.",
        ["cook", "food", "chop"],
    ),
]


class TestTwiAliasDetection:
    @pytest.mark.parametrize("text,expected_tokens", TWI_INPUTS)
    def test_alias_or_regex_finds_skill(self, gh_parser, text, expected_tokens):
        result = gh_parser.parse_for_profile(text)
        labels = " ".join(s["name"].lower() for s in result["skills"])
        assert any(
            tok in labels for tok in expected_tokens
        ), f"Expected one of {expected_tokens} in skill labels: {labels!r}\nInput: {text!r}"

    def test_kayayo_isco_9621(self, gh_parser):
        """kayayei must map to ISCO 9621 (elementary worker)."""
        r = gh_parser.parse("My name is Esi, I am a kayayo at Makola market.")
        matched = [
            s for s in r["skills"]
            if s["taxonomy_code"] == "9621"
        ]
        assert matched, f"No skill with ISCO 9621 in {r['skills']}"

    def test_momo_agent_isco_4211(self, gh_parser):
        r = gh_parser.parse("Abena is an MTN MoMo agent in Tema.")
        matched = [s for s in r["skills"] if s["taxonomy_code"] == "4211"]
        assert matched, f"No skill with ISCO 4211; got {[s['taxonomy_code'] for s in r['skills']]}"

    def test_kayayo_wage_has_ghs(self, gh_parser):
        r = gh_parser.parse_for_profile("I am a kayayei at Kantamanto market.")
        assert "GHS" in r["wage_signal"]["display_value"]

    def test_trotro_transport_network_entry(self, gh_parser):
        r = gh_parser.parse_for_profile("I drive trotro in Accra, 3 years experience.")
        channel = r["network_entry"]["channel"].lower()
        assert any(k in channel for k in ("gprtu", "transport", "momo", "nbssi"))


# ---------------------------------------------------------------------------
# Ga alias detection — Ghana
# ---------------------------------------------------------------------------

class TestGaAliasDetection:
    def test_chop_bar_cook(self, gh_parser):
        r = gh_parser.parse_for_profile("I run a chop bar in Nima and sell kenkey every day.")
        labels = [s["name"].lower() for s in r["skills"]]
        assert any("cook" in l or "food" in l or "chop" in l for l in labels), labels

    def test_phone_repair_english_gh(self, gh_parser):
        r = gh_parser.parse_for_profile(
            "My name is Naa, I fix mobile phones near Accra Mall, screen repair specialist."
        )
        labels = [s["name"].lower() for s in r["skills"]]
        assert any("phone" in l or "repair" in l for l in labels), labels

    def test_kiosk_operator(self, gh_parser):
        r = gh_parser.parse_for_profile("I run a kiosk at Darkuman junction.")
        labels = [s["name"].lower() for s in r["skills"]]
        assert any("kiosk" in l or "trad" in l or "vendor" in l or "market" in l for l in labels), labels


# ---------------------------------------------------------------------------
# Armenian alias detection — Armenia
# ---------------------------------------------------------------------------

ARM_INPUTS = [
    # Armenian teacher
    (
        "Անի Պետրոսյան, 29 տ., Երևան: Անգլ. թ. ու ռ. դաս. եմ տ., Idram:",
        ["teacher", "tutor", "teach"],
    ),
    # Armenian translator
    (
        "Արամ Խաչատրյան, թարգ. ռ.-հ., 5 տ. փ:",
        ["transl", "interpr"],
    ),
    # Armenian software developer
    (
        "Ես ծրագրավորող եմ, Python ու JavaScript:",
        ["software", "develop", "programm", "python", "javascript"],
    ),
    # Armenian driver
    (
        "Աշոտ վ. է, Gyumri-ից Yerevan ամ. մ. ա. ե.:",
        ["driv", "taxi", "transport"],
    ),
    # Armenian tailor
    (
        "Մariamе Հ., Gyumri: կ. և ձ., 7 տ. փ.:",
        ["tailor", "seamst", "sew"],
    ),
]


class TestArmenianAliasDetection:
    def test_teacher_in_armenian_script(self, am_parser):
        text = "Իմ անունը Անի է, ուսուցիչ եմ, Գ. Ն."
        r = am_parser.parse_for_profile(text)
        labels = [s["name"].lower() for s in r["skills"]]
        assert any("teach" in l or "tutor" in l for l in labels), labels

    def test_translator_in_armenian_script(self, am_parser):
        text = "Արամ, 35 տ., Երևան: թ.-ն. ռ. ու հ.:"
        r = am_parser.parse_for_profile(text)
        labels = [s["name"].lower() for s in r["skills"]]
        assert any("transl" in l or "interpr" in l for l in labels), labels

    def test_idram_mobile_money(self, am_parser):
        text = "Ունեմ Idram հաշիվ, ամ. ա. ե.:"
        r = am_parser.parse_for_profile(text)
        labels = [s["name"].lower() for s in r["skills"]]
        assert any("idram" in l or "mobile" in l or "money" in l for l in labels), labels

    def test_programmer_armenian_word(self, am_parser):
        text = "Ես ծ. ե., Python ու JavaScript."
        r = am_parser.parse_for_profile(text)
        labels = [s["name"].lower() for s in r["skills"]]
        assert any("software" in l or "develop" in l or "programm" in l or "python" in l for l in labels), labels

    def test_amd_wage_for_am_profile(self, am_parser):
        text = "Անի, ուսուցիչ, Gym., 4 տ. փ."
        r = am_parser.parse_for_profile(text)
        assert "AMD" in r["wage_signal"]["display_value"]

    def test_ussd_shortcode_404(self, am_parser):
        text = "Ani, teacher, translator, Idram"
        r = am_parser.parse_for_profile(text)
        assert any("*404#" in line for line in r["ussd_menu"])


# ---------------------------------------------------------------------------
# Russian alias detection — Armenia
# ---------------------------------------------------------------------------

RU_INPUTS = [
    ("Меня зовут Нина, я учитель, преподаю русский.", ["teach", "tutor"]),
    ("Работаю переводчиком с армянского на русский.", ["transl"]),
    ("Я программист, пишу на Python.", ["programm", "software", "develop", "python"]),
    ("Водитель такси в Ереване, 6 лет стажа.", ["driv", "taxi", "transport"]),
    ("Работаю портнихой, шью на заказ.", ["tailor", "sew", "seamst"]),
    ("Я бухгалтер, веду учёт для малого бизнеса.", ["account", "book", "financ"]),
]


class TestRussianAliasDetection:
    @pytest.mark.parametrize("text,expected_tokens", RU_INPUTS)
    def test_russian_skill_detected(self, am_parser, text, expected_tokens):
        r = am_parser.parse_for_profile(text)
        labels = " ".join(s["name"].lower() for s in r["skills"])
        assert any(tok in labels for tok in expected_tokens), (
            f"Expected one of {expected_tokens} in {labels!r}\nInput: {text!r}"
        )

    def test_russian_wage_is_amd(self, am_parser):
        r = am_parser.parse_for_profile("Я программист в Ереване, Idram.")
        assert "AMD" in r["wage_signal"]["display_value"]


# ---------------------------------------------------------------------------
# Locale swap — same skill, different country
# ---------------------------------------------------------------------------

class TestLocaleSwap:
    def test_sms_uses_ghs_for_gh(self, gh_parser):
        r = gh_parser.parse_for_profile("I teach English in Accra.")
        assert "GHS" in r["wage_signal"]["display_value"]

    def test_sms_uses_amd_for_am(self, am_parser):
        r = am_parser.parse_for_profile("I teach English in Yerevan.")
        assert "AMD" in r["wage_signal"]["display_value"]

    def test_ussd_shortcode_differs_by_country(self, gh_parser, am_parser):
        text = "I teach English."
        gh_r = gh_parser.parse_for_profile(text)
        am_r = am_parser.parse_for_profile(text)
        gh_menu = " ".join(gh_r["ussd_menu"])
        am_menu = " ".join(am_r["ussd_menu"])
        assert "*789#" in gh_menu
        assert "*404#" in am_menu

    def test_network_entry_coords_differ(self, gh_parser, am_parser):
        text = "I am a software developer."
        gh_ne = gh_parser.parse_for_profile(text)["network_entry"]
        am_ne = am_parser.parse_for_profile(text)["network_entry"]
        assert gh_ne["lat"] != am_ne["lat"]
        assert gh_ne["lng"] != am_ne["lng"]

    def test_same_teacher_skill_different_network(self, gh_parser, am_parser):
        text = "I am a teacher."
        gh_ch = gh_parser.parse_for_profile(text)["network_entry"]["channel"].lower()
        am_ch = am_parser.parse_for_profile(text)["network_entry"]["channel"].lower()
        assert "ghana" in gh_ch or "ghanalearn" in gh_ch or "ges" in gh_ch or gh_ch != am_ch

    def test_zero_credential_gh_true_am_false(self, gh_parser, am_parser):
        assert gh_parser.zero_credential_default is True
        assert am_parser.zero_credential_default is False


# ---------------------------------------------------------------------------
# AliasMatcher unit tests
# ---------------------------------------------------------------------------

class TestAliasMatcher:
    def test_empty_registry_returns_empty(self):
        m = AliasMatcher([])
        assert m.find_all("I am a teacher") == []

    def test_case_insensitive_match(self):
        registry = [{
            "canonical_label": "Mobile phone repair technician",
            "aliases": ["Phone Fixer"],
            "isco_code": "7421",
            "category": "technical",
            "base_weight": 0.86,
        }]
        m = AliasMatcher(registry)
        hits = m.find_all("I am a phone fixer in Accra")
        assert len(hits) == 1
        assert hits[0].canonical_label == "Mobile phone repair technician"

    def test_unicode_nfc_match(self):
        registry = [{
            "canonical_label": "Teacher / private tutor",
            "aliases": ["ուսուցիչ"],
            "isco_code": "2320",
            "category": "care",
            "base_weight": 0.88,
        }]
        m = AliasMatcher(registry)
        hits = m.find_all("Ես ուսուցիչ եմ Երևանում")
        assert hits, "Armenian alias should match"
        assert hits[0].isco_code == "2320"

    def test_no_duplicate_canonical(self):
        registry = [{
            "canonical_label": "Teacher / private tutor",
            "aliases": ["teacher", "tutor", "tutoring", "teach"],
            "isco_code": "2320",
            "category": "care",
            "base_weight": 0.85,
        }]
        m = AliasMatcher(registry)
        hits = m.find_all("I am a teacher who does tutoring and teaching")
        labels = [h.canonical_label for h in hits]
        assert len(labels) == len(set(labels)), "No duplicates allowed"
        assert len(hits) == 1

    def test_longer_alias_wins(self):
        registry = [{
            "canonical_label": "Mobile phone repair technician",
            "aliases": ["phone repair", "phone", "repair"],
            "isco_code": "7421",
            "category": "technical",
            "base_weight": 0.86,
        }]
        m = AliasMatcher(registry)
        hits = m.find_all("I specialize in phone repair")
        assert hits[0].matched_alias == "phone repair"

    def test_twi_kayayo_match(self):
        from app.core.country_profile import load_country_profile, get_skill_alias_registry
        profile = load_country_profile("GH", "urban_informal")
        registry = get_skill_alias_registry(profile)
        m = AliasMatcher(registry)
        hits = m.find_all("I am a kayayo at Agbogbloshie")
        assert hits, "kayayo should hit alias registry"
        assert any(h.isco_code == "9621" for h in hits)

    def test_russian_translator_match(self):
        from app.core.country_profile import load_country_profile, get_skill_alias_registry
        profile = load_country_profile("AM", "urban_informal")
        registry = get_skill_alias_registry(profile)
        m = AliasMatcher(registry)
        hits = m.find_all("Я работаю переводчиком")
        assert hits, "Russian 'переводчиком' should hit alias registry"
        assert any(h.isco_code == "2643" for h in hits)


# ---------------------------------------------------------------------------
# candidate_phrases utility
# ---------------------------------------------------------------------------

class TestCandidatePhrases:
    def test_english_phrases(self):
        phrases = candidate_phrases("I fix phones in Accra")
        assert "fix phones" in phrases or "phones" in phrases

    def test_armenian_phrases_preserved(self):
        phrases = candidate_phrases("ուսուցիչ եմ Երևանում")
        assert any("ուսուցիչ" in p for p in phrases), phrases

    def test_russian_phrases_preserved(self):
        phrases = candidate_phrases("Я переводчик в Ереване")
        assert any("переводчик" in p for p in phrases), phrases

    def test_deduplication(self):
        phrases = candidate_phrases("teacher teacher teacher")
        assert phrases.count("teacher") == 1

    def test_max_words_respected(self):
        phrases = candidate_phrases("one two three four five six", max_words=3)
        assert all(len(p.split()) <= 3 for p in phrases)
