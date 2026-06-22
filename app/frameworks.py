"""Loading and in-memory representation of governance frameworks."""
from __future__ import annotations

import functools
from dataclasses import dataclass, field
from typing import Optional

import yaml

from . import config


@dataclass
class Control:
    id: str
    title: str
    reference: str
    category: str
    description: str
    keywords: list[str]
    expected_evidence: list[str] = field(default_factory=list)
    weight: int = 3

    @property
    def query_text(self) -> str:
        """Text used to represent the control when matching against a policy."""
        parts = [self.title, self.description] + self.keywords
        return " ".join(p for p in parts if p)


@dataclass
class Framework:
    id: str
    name: str
    short_name: str
    version: str
    authority: str
    reference_url: str
    description: str
    controls: list[Control]
    covered_threshold: float = 0.32
    partial_threshold: float = 0.14

    def control_by_id(self, control_id: str) -> Optional[Control]:
        for c in self.controls:
            if c.id == control_id:
                return c
        return None


@dataclass
class CrosswalkTheme:
    id: str
    title: str
    controls: dict[str, list[str]]  # framework_id -> [control_id, ...]


def _parse_framework(raw: dict) -> Framework:
    thresholds = raw.get("thresholds", {}) or {}
    controls = [
        Control(
            id=c["id"],
            title=c["title"],
            reference=c.get("reference", ""),
            category=c.get("category", "General"),
            description=c.get("description", "").strip(),
            keywords=[k.lower() for k in c.get("keywords", [])],
            expected_evidence=c.get("expected_evidence", []),
            weight=int(c.get("weight", 3)),
        )
        for c in raw.get("controls", [])
    ]
    return Framework(
        id=raw["id"],
        name=raw["name"],
        short_name=raw.get("short_name", raw["name"]),
        version=str(raw.get("version", "")),
        authority=raw.get("authority", ""),
        reference_url=raw.get("reference_url", ""),
        description=raw.get("description", "").strip(),
        controls=controls,
        covered_threshold=float(thresholds.get("covered", 0.32)),
        partial_threshold=float(thresholds.get("partial", 0.14)),
    )


@functools.lru_cache(maxsize=1)
def load_frameworks() -> dict[str, Framework]:
    """Load all framework YAML files into a dict keyed by framework id."""
    frameworks: dict[str, Framework] = {}
    for path in sorted(config.FRAMEWORKS_DIR.glob("*.yaml")):
        with open(path, "r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
        if not raw:
            continue
        fw = _parse_framework(raw)
        frameworks[fw.id] = fw
    return frameworks


@functools.lru_cache(maxsize=1)
def load_crosswalk() -> list[CrosswalkTheme]:
    if not config.CROSSWALK_FILE.exists():
        return []
    with open(config.CROSSWALK_FILE, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    themes = []
    for t in raw.get("themes", []):
        themes.append(
            CrosswalkTheme(
                id=t["id"],
                title=t["title"],
                controls={k: list(v or []) for k, v in (t.get("controls") or {}).items()},
            )
        )
    return themes
