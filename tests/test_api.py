import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_list_frameworks():
    r = client.get("/api/frameworks")
    assert r.status_code == 200
    data = r.json()
    ids = {f["id"] for f in data}
    assert {"eu_ai_act", "iso_42001", "nist_ai_rmf"} <= ids


def test_analyze_text():
    r = client.post(
        "/api/analyze/text",
        data={
            "text": "We maintain a risk management system and data governance with human oversight.",
            "frameworks": "eu_ai_act",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["total_controls"] > 0
    assert body["frameworks"][0]["framework_id"] == "eu_ai_act"


def test_analyze_file_upload():
    content = b"Our AI policy covers risk management, data governance and human oversight."
    files = {"file": ("policy.txt", io.BytesIO(content), "text/plain")}
    r = client.post("/api/analyze", files=files, data={"frameworks": "all"})
    assert r.status_code == 200
    assert r.json()["document_name"] == "policy.txt"


def test_analyze_invalid_framework():
    r = client.post(
        "/api/analyze/text",
        data={"text": "hello", "frameworks": "nope"},
    )
    assert r.status_code == 400


def test_unsupported_file_type():
    files = {"file": ("policy.exe", io.BytesIO(b"data"), "application/octet-stream")}
    r = client.post("/api/analyze", files=files)
    assert r.status_code == 422


def test_report_markdown():
    content = b"We maintain a risk management system and data governance."
    files = {"file": ("policy.txt", io.BytesIO(content), "text/plain")}
    r = client.post("/api/report", files=files, data={"frameworks": "eu_ai_act", "fmt": "markdown"})
    assert r.status_code == 200
    assert "AI Governance Coverage Report" in r.text


def test_report_json():
    content = b"We maintain a risk management system and data governance."
    files = {"file": ("policy.txt", io.BytesIO(content), "text/plain")}
    r = client.post("/api/report", files=files, data={"frameworks": "eu_ai_act", "fmt": "json"})
    assert r.status_code == 200
    assert r.json()["frameworks"][0]["framework_id"] == "eu_ai_act"
