"""
Human Layer renderer.
Produces profile card, SMS digest (≤160 chars), and USSD tree from VSS list.
Uses Jinja2 templates for profile card HTML.
"""
from __future__ import annotations

import uuid
from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape, BaseLoader, Template

from app.core.parser import ExtractedUser  # type: ignore[attr-defined]

_PROFILE_CARD_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ display_name }} — UNMAPPED Skills Card</title>
<style>
  body { font-family: 'Segoe UI', sans-serif; background: #f5f0e8; margin: 0; padding: 16px; }
  .card { max-width: 480px; margin: auto; background: #fff; border-radius: 12px;
          box-shadow: 0 2px 12px rgba(0,0,0,.12); padding: 24px; }
  .badge { display: inline-block; font-size: 11px; font-weight: 700; padding: 3px 10px;
           border-radius: 20px; color: #fff; background: #c0392b; margin-bottom: 8px; }
  .badge.zero-cred { background: #27ae60; }
  h2 { margin: 0 0 4px; font-size: 22px; color: #1a1a1a; }
  .headline { color: #555; font-size: 14px; margin-bottom: 12px; }
  .meta { font-size: 12px; color: #888; margin-bottom: 16px; }
  .skills { list-style: none; padding: 0; margin: 0; }
  .skills li { display: flex; align-items: center; gap: 8px; padding: 6px 0;
               border-bottom: 1px solid #f0f0f0; }
  .skills li:last-child { border-bottom: none; }
  .tier { font-size: 10px; padding: 2px 7px; border-radius: 10px; font-weight: 600; }
  .tier.expert { background: #2ecc71; color: #fff; }
  .tier.established { background: #3498db; color: #fff; }
  .tier.developing { background: #f39c12; color: #fff; }
  .tier.emerging { background: #bdc3c7; color: #444; }
  .score { font-size: 11px; color: #888; }
  .bio { font-size: 13px; color: #555; line-height: 1.5; margin-top: 12px; padding-top: 12px;
         border-top: 1px solid #eee; }
  .footer { font-size: 10px; color: #ccc; margin-top: 16px; text-align: center; }
</style>
</head>
<body>
<div class="card">
  {% if zero_credential %}<span class="badge zero-cred">Zero-Credential Path</span>{% endif %}
  <h2>{{ display_name }}</h2>
  <div class="headline">{{ headline }}</div>
  <div class="meta">
    📍 {{ location }}
    {% if languages %} &nbsp;|&nbsp; 🗣 {{ languages | join(', ') }}{% endif %}
  </div>
  <ul class="skills">
    {% for skill in skills_summary %}
    <li>
      <span>{{ skill.label }}</span>
      <span class="tier {{ skill.confidence_tier }}">{{ skill.confidence_tier }}</span>
      <span class="score">{{ "%.0f"|format(skill.confidence_score * 100) }}%</span>
    </li>
    {% endfor %}
  </ul>
  {% if bio_snippet %}<div class="bio">{{ bio_snippet }}</div>{% endif %}
  <div class="footer">UNMAPPED Protocol v0.2 — Skills Signal Engine</div>
</div>
</body>
</html>"""


class HumanLayerRenderer:
    def __init__(self, profile: dict[str, Any]) -> None:
        self.profile = profile
        self._env = Environment(loader=BaseLoader(), autoescape=select_autoescape(["html"]))
        self._card_template: Template = self._env.from_string(_PROFILE_CARD_TEMPLATE)

    def render(
        self,
        user: ExtractedUser,
        vss_list: list[dict[str, Any]],
        now: str,
    ) -> dict[str, Any]:
        profile_card = self._build_profile_card(user, vss_list)
        sms = self._build_sms(user, vss_list)
        ussd = self._build_ussd_tree(user, vss_list)

        return {
            "hl_id": f"hl_{uuid.uuid4()}",
            "schema_version": "v0.2",
            "created_at": now,
            "user_id": user.user_id,
            "vss_ids": [v["vss_id"] for v in vss_list],
            "profile_card": profile_card,
            "sms_summary": sms,
            "ussd_tree": ussd,
        }

    def _build_profile_card(
        self,
        user: ExtractedUser,
        vss_list: list[dict[str, Any]],
    ) -> dict[str, Any]:
        name = user.display_name or "Anonymous Worker"
        location_str = user.location.get("city", user.location.get("country_code", ""))

        skills_summary = []
        for vss in vss_list:
            skills_summary.append({
                "label": vss["skill"]["label"],
                "confidence_tier": vss["confidence"]["tier"],
                "confidence_score": vss["confidence"]["score"],
                "taxonomy_code": vss["taxonomy_crosswalk"]["primary"]["code"],
                "category": vss["skill"]["category"],
            })

        # Sort by confidence score descending
        skills_summary.sort(key=lambda x: x["confidence_score"], reverse=True)
        top_skill = skills_summary[0]["label"] if skills_summary else ""

        headline = self._generate_headline(name, skills_summary, location_str)
        bio_snippet = self._generate_bio(user, vss_list)

        lang_labels = self._bcp47_to_labels(user.languages)

        rendered_html = self._card_template.render(
            display_name=name,
            headline=headline,
            location=location_str,
            languages=lang_labels,
            skills_summary=skills_summary,
            zero_credential=user.zero_credential,
            bio_snippet=bio_snippet,
        )

        return {
            "display_name": name,
            "headline": headline[:120],
            "location": location_str,
            "languages": lang_labels,
            "skills_summary": skills_summary,
            "zero_credential_badge": user.zero_credential,
            "top_skill": top_skill,
            "bio_snippet": bio_snippet[:280] if bio_snippet else None,
            "rendered_html": rendered_html,
        }

    def _build_sms(
        self,
        user: ExtractedUser,
        vss_list: list[dict[str, Any]],
    ) -> dict[str, Any]:
        name = user.display_name or "Worker"
        city = user.location.get("city", "")
        loc_part = f" in {city}" if city else ""

        if not vss_list:
            text = f"UNMAPPED: {name}{loc_part}. No skills detected yet."
        else:
            top = vss_list[0]
            skill_label = top["skill"]["label"]
            tier = top["confidence"]["tier"]
            score_pct = int(top["confidence"]["score"] * 100)

            skill_parts = [f"{v['skill']['label']}({int(v['confidence']['score']*100)}%)"
                           for v in vss_list[:3]]
            skills_str = ", ".join(skill_parts)

            text = f"UNMAPPED:{name}{loc_part}|Skills:{skills_str}|Confidence:{tier.upper()}"
            if len(text) > 160:
                text = f"UNMAPPED:{name}|{skill_label} {score_pct}% confidence|unmapped.io"

        text = text[:160]
        return {"text": text, "char_count": len(text), "language": "en"}

    def _build_ussd_tree(
        self,
        user: ExtractedUser,
        vss_list: list[dict[str, Any]],
    ) -> dict[str, Any]:
        name = user.display_name or "Worker"
        top_skill = vss_list[0]["skill"]["label"] if vss_list else "Skills"
        tier = vss_list[0]["confidence"]["tier"].upper() if vss_list else "N/A"

        # Build skill sub-nodes
        skill_options = []
        for i, vss in enumerate(vss_list[:5], start=1):
            label = vss["skill"]["label"]
            score = int(vss["confidence"]["score"] * 100)
            code = vss["taxonomy_crosswalk"]["primary"]["code"]
            skill_options.append({
                "key": str(i),
                "label": f"{i}. {label}",
                "next": {
                    "id": f"skill_{i}",
                    "text": (
                        f"{label}\n"
                        f"Confidence: {score}% ({vss['confidence']['tier']})\n"
                        f"Code: {code}\n"
                        f"0. Back"
                    )[:182],
                    "input_type": "numeric",
                    "options": [{"key": "0", "label": "Back", "next": {"id": "main_back", "text": "Returning...", "is_terminal": True}}],
                    "is_terminal": False,
                },
            })
        skill_options.append({
            "key": "0",
            "label": "0. Exit",
            "next": {"id": "exit", "text": "Thank you. Visit unmapped.io", "is_terminal": True},
        })

        root = {
            "id": "root",
            "text": (
                f"UNMAPPED Skills\n"
                f"Name: {name}\n"
                f"Top: {top_skill} ({tier})\n"
                f"1-{min(len(vss_list),5)}: View skills  0: Exit"
            )[:182],
            "input_type": "numeric",
            "options": skill_options,
            "is_terminal": False,
        }
        return {"root": root, "session_timeout_sec": 180}

    # ------------------------------------------------------------------
    # Text generation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_headline(
        name: str,
        skills: list[dict[str, Any]],
        location: str,
    ) -> str:
        if not skills:
            return f"Informal worker based in {location}" if location else "Informal worker"
        top_labels = [s["label"] for s in skills[:2]]
        skills_str = " & ".join(top_labels)
        loc_part = f" | {location}" if location else ""
        return f"{skills_str} specialist{loc_part}"

    @staticmethod
    def _generate_bio(
        user: ExtractedUser,
        vss_list: list[dict[str, Any]],
    ) -> str:
        name = user.display_name or "This worker"
        city = user.location.get("city", "")
        loc = f" in {city}" if city else ""
        skills_str = ", ".join(v["skill"]["label"] for v in vss_list[:3])
        langs = user.languages[:3]
        lang_str = (", ".join(langs) + " speaker") if langs else ""
        zero = " Self-identified via zero-credential path." if user.zero_credential else ""
        return (
            f"{name} is a skilled worker{loc} with expertise in {skills_str}."
            f"{' ' + lang_str + '.' if lang_str else ''}{zero}"
        )[:280]

    @staticmethod
    def _bcp47_to_labels(tags: list[str]) -> list[str]:
        _MAP = {
            "en": "English", "en-GH": "English (GH)", "ak-GH": "Twi",
            "gaa": "Ga", "ee-GH": "Ewe", "ha-GH": "Hausa", "ha": "Hausa",
            "fr": "French", "ar": "Arabic", "sw": "Swahili",
        }
        return [_MAP.get(t, t) for t in tags]
