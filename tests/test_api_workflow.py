import io
import json
import pytest
from app import create_app
from config import Config
from services.stats import build_class_payload, subject_statistics


@pytest.fixture
def client():
    app = create_app(Config)
    return app.test_client()


def test_cors_headers(client):
    res = client.get("/api/health", headers={"Origin": "http://192.168.1.50:3000"})
    assert res.status_code == 200
    assert res.headers.get("Access-Control-Allow-Origin") in ("*", "http://192.168.1.50:3000")


def test_custom_lan_host_header(client):
    headers = {"HTTP_HOST": "192.168.1.100:8051"}
    res = client.get("/", environ_overrides=headers)
    assert res.status_code == 200
    assert "AI Performance Analysis" in res.data.decode("utf-8")


def test_class_payload_generation():
    students = [
        {"name": "Student A", "averageScore": 95, "totalScore": 380, "subjects": [{"subject": "Math", "score": 95}]},
        {"name": "Student B", "averageScore": 60, "totalScore": 240, "subjects": [{"subject": "Math", "score": 60}]},
        {"name": "Student C", "averageScore": 75, "totalScore": 300, "subjects": [{"subject": "Math", "score": 75}]},
    ]
    payload = build_class_payload(students)
    assert payload["totalStudents"] == 3
    assert payload["topPerformers"][0]["name"] == "Student A"
    assert payload["weakPerformers"][0]["name"] == "Student B"


def test_subject_statistics():
    students = [
        {"name": "Student A", "subjects": [{"subject": "Math", "score": 90}, {"subject": "English", "score": 80}]},
        {"name": "Student B", "subjects": [{"subject": "Math", "score": 70}, {"subject": "English", "score": 80}]},
    ]
    df = subject_statistics(students)
    assert df.loc["Math"]["mean"] == 80.0
    assert df.loc["English"]["mean"] == 80.0


def test_upload_file_too_large():
    class SmallLimitConfig(Config):
        MAX_UPLOAD_SIZE_MB = 1
        MAX_CONTENT_LENGTH = 100  # 100 bytes

    app = create_app(SmallLimitConfig)
    small_client = app.test_client()

    large_content = b"Student Name,Math\n" + (b"A" * 500)
    data = {"file": (io.BytesIO(large_content), "large.csv")}
    res = small_client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert res.status_code == 413
    assert "too large" in res.json.get("error", "").lower()
