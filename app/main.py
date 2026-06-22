"""FastAPI application exposing the AI Governance Tracker."""
from __future__ import annotations

import io
import json

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles

from . import __version__, config
from .engine import get_engine
from .extraction import ExtractionError, extract_text
from .frameworks import load_frameworks
from .reporting import to_markdown
from .schemas import AnalysisResponse, FrameworkInfo

app = FastAPI(
    title="AI Governance Tracker",
    version=__version__,
    description=(
        "Upload an organisation's AI policy and map it against governance "
        "frameworks (EU AI Act, ISO/IEC 42001, NIST AI RMF) to surface coverage "
        "and gaps."
    ),
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.get("/api/frameworks", response_model=list[FrameworkInfo])
def list_frameworks() -> list[FrameworkInfo]:
    frameworks = load_frameworks()
    return [
        FrameworkInfo(
            id=fw.id,
            name=fw.name,
            short_name=fw.short_name,
            version=fw.version,
            description=fw.description,
            reference_url=fw.reference_url,
            control_count=len(fw.controls),
        )
        for fw in frameworks.values()
    ]


def _resolve_frameworks(frameworks: str | None) -> list[str]:
    available = list(load_frameworks().keys())
    if not frameworks or frameworks.strip().lower() in ("", "all"):
        return available
    requested = [f.strip() for f in frameworks.split(",") if f.strip()]
    invalid = [f for f in requested if f not in available]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown framework id(s): {', '.join(invalid)}. "
            f"Available: {', '.join(available)}",
        )
    return requested


async def _read_upload(file: UploadFile) -> tuple[str, bytes]:
    data = await file.read()
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {config.MAX_UPLOAD_BYTES} bytes.",
        )
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    return file.filename or "document", data


def _run_analysis(filename: str, text: str, framework_ids: list[str]) -> AnalysisResponse:
    engine = get_engine()
    try:
        result = engine.analyze(text, framework_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result.document_name = filename
    return result


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(
    file: UploadFile = File(...),
    frameworks: str | None = Form(default=None),
) -> AnalysisResponse:
    """Analyse an uploaded policy document and return the coverage mapping."""
    framework_ids = _resolve_frameworks(frameworks)
    filename, data = await _read_upload(file)
    try:
        text = extract_text(filename, data)
    except ExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _run_analysis(filename, text, framework_ids)


@app.post("/api/analyze/text", response_model=AnalysisResponse)
async def analyze_text(
    text: str = Form(...),
    frameworks: str | None = Form(default=None),
    name: str = Form(default="pasted-policy.txt"),
) -> AnalysisResponse:
    """Analyse pasted policy text (useful for quick checks and the demo)."""
    framework_ids = _resolve_frameworks(frameworks)
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text provided.")
    return _run_analysis(name, text, framework_ids)


@app.post("/api/report")
async def report(
    file: UploadFile = File(...),
    frameworks: str | None = Form(default=None),
    fmt: str = Form(default="markdown"),
) -> Response:
    """Return a downloadable Markdown or JSON report."""
    framework_ids = _resolve_frameworks(frameworks)
    filename, data = await _read_upload(file)
    try:
        text = extract_text(filename, data)
    except ExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    result = _run_analysis(filename, text, framework_ids)

    if fmt == "json":
        return Response(
            content=result.model_dump_json(indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=ai-governance-report.json"},
        )
    md = to_markdown(result)
    return PlainTextResponse(
        content=md,
        headers={"Content-Disposition": "attachment; filename=ai-governance-report.md"},
    )


# Serve the single-page UI from the static directory (mounted last so /api wins).
app.mount("/", StaticFiles(directory=str(config.STATIC_DIR), html=True), name="static")
