"""
Taxonomy crosswalk engine using NetworkX.
Maps extracted skill phrases to ISCO-08, ESCO, O*NET codes via a weighted graph.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

import networkx as nx

logger = logging.getLogger(__name__)


@dataclass
class TaxonomyMatch:
    framework: str
    code: str
    label: str
    match_score: float


@dataclass
class CrosswalkResult:
    primary: TaxonomyMatch
    secondary: list[TaxonomyMatch] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Static taxonomy graph — seed data for MVP (expandable via DB / API)
# Each node: (framework, code) -> label
# Each edge: keyword trigger -> node with match weight
# ---------------------------------------------------------------------------

_ISCO_NODES = {
    ("ISCO-08", "7421"): "Electronics and telecommunications installers and repairers",
    ("ISCO-08", "2512"): "Software developers",
    ("ISCO-08", "5221"): "Shop salespersons",
    ("ISCO-08", "7411"): "Building and related electricians",
    ("ISCO-08", "6110"): "Crop farmers",
    ("ISCO-08", "5141"): "Hairdressers",
    ("ISCO-08", "7436"): "Tailors, dressmakers, and hatters",
    ("ISCO-08", "8322"): "Motorcycle drivers",
    ("ISCO-08", "3120"): "ICT technicians",
    ("ISCO-08", "4131"): "Keyboard operators",
    ("ISCO-08", "5322"): "Home-based personal care workers",
}

_ESCO_NODES = {
    ("ESCO", "esco/3565"): "ICT help desk agent",
    ("ESCO", "esco/2690"): "Software developer",
    ("ESCO", "esco/5435"): "Electronic equipment repairer",
    ("ESCO", "esco/7436"): "Tailor",
    ("ESCO", "esco/6110"): "Crop production worker",
}

_ONET_NODES = {
    ("O*NET", "49-2022.00"): "Telecommunications Equipment Installers and Repairers",
    ("O*NET", "15-1252.00"): "Software Developers",
    ("O*NET", "41-2031.00"): "Retail Salespersons",
}

# keyword → list of (framework, code, base_weight)
_KEYWORD_MAP: list[tuple[str, str, str, float]] = [
    # Mobile/phone repair
    ("phone repair", "ISCO-08", "7421", 0.95),
    ("fix phone", "ISCO-08", "7421", 0.95),
    ("fixing phone", "ISCO-08", "7421", 0.95),
    ("mobile repair", "ISCO-08", "7421", 0.93),
    ("phone technician", "ISCO-08", "7421", 0.92),
    ("electronics repair", "ISCO-08", "7421", 0.85),
    ("screen replacement", "ISCO-08", "7421", 0.88),
    ("hardware repair", "ISCO-08", "7421", 0.80),
    # Software / coding
    ("coding", "ISCO-08", "2512", 0.85),
    ("programming", "ISCO-08", "2512", 0.90),
    ("software", "ISCO-08", "2512", 0.88),
    ("web development", "ISCO-08", "2512", 0.90),
    ("python", "ISCO-08", "2512", 0.82),
    ("javascript", "ISCO-08", "2512", 0.82),
    ("youtube coding", "ISCO-08", "2512", 0.70),
    ("learned coding", "ISCO-08", "2512", 0.72),
    # Trade / retail
    ("selling", "ISCO-08", "5221", 0.75),
    ("sales", "ISCO-08", "5221", 0.78),
    ("kiosk", "ISCO-08", "5221", 0.80),
    ("market trader", "ISCO-08", "5221", 0.82),
    # Tailoring
    ("tailoring", "ISCO-08", "7436", 0.92),
    ("sewing", "ISCO-08", "7436", 0.88),
    ("dressmaking", "ISCO-08", "7436", 0.92),
    # Teaching / tutoring
    ("teaching", "ISCO-08", "2320", 0.85),
    ("tutoring", "ISCO-08", "2320", 0.83),
    # Farming
    ("farming", "ISCO-08", "6110", 0.88),
    ("agriculture", "ISCO-08", "6110", 0.88),
    ("crop", "ISCO-08", "6110", 0.75),
    # Transport
    ("driving", "ISCO-08", "8322", 0.80),
    ("delivery", "ISCO-08", "8322", 0.72),
    ("motorbike", "ISCO-08", "8322", 0.85),
    # Care work
    ("childcare", "ISCO-08", "5322", 0.88),
    ("nursing", "ISCO-08", "5322", 0.80),
    ("caregiver", "ISCO-08", "5322", 0.88),
]

# ISCO → ESCO crosswalk bridges
_ISCO_TO_ESCO: dict[str, tuple[str, str, float]] = {
    "7421": ("ESCO", "esco/5435", 0.90),
    "2512": ("ESCO", "esco/2690", 0.92),
    "5221": ("ESCO", "esco/5435", 0.70),
    "7436": ("ESCO", "esco/7436", 0.95),
    "6110": ("ESCO", "esco/6110", 0.92),
}

# ISCO → O*NET crosswalk bridges
_ISCO_TO_ONET: dict[str, tuple[str, str, float]] = {
    "7421": ("O*NET", "49-2022.00", 0.88),
    "2512": ("O*NET", "15-1252.00", 0.92),
    "5221": ("O*NET", "41-2031.00", 0.85),
}

# ISCO node labels (full registry)
_ISCO_LABELS: dict[str, str] = {code: label for (_, code), label in _ISCO_NODES.items()}
_ISCO_LABELS["2320"] = "Vocational education teachers"


class TaxonomyGraph:
    """NetworkX-backed taxonomy crosswalk graph."""

    def __init__(self) -> None:
        self._g: nx.DiGraph = nx.DiGraph()
        self._local_overrides: list[dict[str, str]] = []
        self._build_graph()

    def _build_graph(self) -> None:
        for (fw, code), label in {**_ISCO_NODES, **_ESCO_NODES, **_ONET_NODES}.items():
            self._g.add_node(f"{fw}:{code}", framework=fw, code=code, label=label)

        for isco_code, (esco_fw, esco_code, weight) in _ISCO_TO_ESCO.items():
            src = f"ISCO-08:{isco_code}"
            tgt = f"{esco_fw}:{esco_code}"
            if src in self._g and tgt in self._g:
                self._g.add_edge(src, tgt, weight=weight, relation="crosswalk")

        for isco_code, (onet_fw, onet_code, weight) in _ISCO_TO_ONET.items():
            src = f"ISCO-08:{isco_code}"
            tgt = f"{onet_fw}:{onet_code}"
            if src in self._g and tgt in self._g:
                self._g.add_edge(src, tgt, weight=weight, relation="crosswalk")

    def register_local_overrides(self, overrides: list[dict[str, str]]) -> None:
        """Register country-profile local skill overrides into the graph."""
        self._local_overrides = overrides

    def crosswalk(self, phrase: str) -> Optional[CrosswalkResult]:
        """Find best taxonomy match for a skill phrase.

        Checks local overrides first, then keyword map with fuzzy normalisation.
        Returns CrosswalkResult with primary ISCO-08 match + secondary crosswalks.
        """
        normalised = self._normalise(phrase)

        # 1. Local override exact/partial match
        for override in self._local_overrides:
            if override["local_label"].lower() in normalised:
                code = override["canonical_code"]
                fw = override["framework"]
                label = _ISCO_LABELS.get(code, code)
                primary = TaxonomyMatch(framework=fw, code=code, label=label, match_score=0.98)
                return CrosswalkResult(
                    primary=primary,
                    secondary=self._get_secondary(fw, code),
                )

        # 2. Keyword map — find best scoring match
        best: Optional[tuple[str, str, str, float]] = None
        for keyword, fw, code, base_weight in _KEYWORD_MAP:
            if keyword in normalised:
                if best is None or base_weight > best[3]:
                    best = (keyword, fw, code, base_weight)

        if best is None:
            return None

        _, fw, code, score = best
        label = _ISCO_LABELS.get(code, code)
        primary = TaxonomyMatch(framework=fw, code=code, label=label, match_score=score)
        return CrosswalkResult(primary=primary, secondary=self._get_secondary(fw, code))

    def _get_secondary(self, fw: str, code: str) -> list[TaxonomyMatch]:
        node_id = f"{fw}:{code}"
        secondary: list[TaxonomyMatch] = []
        if node_id not in self._g:
            return secondary
        for _, tgt, data in self._g.out_edges(node_id, data=True):
            node_data = self._g.nodes[tgt]
            secondary.append(TaxonomyMatch(
                framework=node_data["framework"],
                code=node_data["code"],
                label=node_data["label"],
                match_score=data.get("weight", 0.8),
            ))
        return secondary

    @staticmethod
    def _normalise(text: str) -> str:
        return re.sub(r"\s+", " ", text.lower().strip())
