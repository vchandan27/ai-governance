"""Pydantic schemas describing the API request/response contracts."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CoverageStatus(str, Enum):
    COVERED = "covered"
    PARTIAL = "partial"
    GAP = "gap"


class Evidence(BaseModel):
    """A snippet of the source policy that supports a control."""

    text: str
    similarity: float = Field(..., description="Cosine similarity 0..1")
    matched_keywords: list[str] = Field(default_factory=list)


class ControlResult(BaseModel):
    control_id: str
    title: str
    reference: str
    category: str
    weight: int
    status: CoverageStatus
    score: float = Field(..., description="Blended coverage score 0..1")
    evidence: list[Evidence] = Field(default_factory=list)
    matched_keywords: list[str] = Field(default_factory=list)
    recommendation: Optional[str] = None
    description: str = ""


class FrameworkResult(BaseModel):
    framework_id: str
    name: str
    short_name: str
    version: str
    reference_url: str
    compliance_score: float = Field(..., description="Weighted 0..100 score")
    covered: int
    partial: int
    gaps: int
    total_controls: int
    controls: list[ControlResult]


class CrosswalkThemeResult(BaseModel):
    theme_id: str
    title: str
    # framework_id -> best status across that framework's mapped controls
    statuses: dict[str, Optional[CoverageStatus]]
    overall_status: CoverageStatus


class AnalysisSummary(BaseModel):
    overall_score: float
    total_controls: int
    covered: int
    partial: int
    gaps: int
    top_gaps: list[ControlResult]


class AnalysisResponse(BaseModel):
    document_name: str
    document_chars: int
    segments_analyzed: int
    engine: str
    summary: AnalysisSummary
    frameworks: list[FrameworkResult]
    crosswalk: list[CrosswalkThemeResult]


class FrameworkInfo(BaseModel):
    id: str
    name: str
    short_name: str
    version: str
    description: str
    reference_url: str
    control_count: int
