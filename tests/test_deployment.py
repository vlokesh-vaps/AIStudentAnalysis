import io
import json
import pytest
from app import create_app
from config import Config


class PrefixTestConfig(Config):
    APPLICATION_ROOT = "/student-analysis"
    ENABLE_DOCS = True
    MAX_UPLOAD_SIZE_MB = 25
    TRUSTED_PROXIES = 1


class DocsDisabledConfig(Config):
    APPLICATION_ROOT = ""
    ENABLE_DOCS = False
    TRUSTED_PROXIES = 1


@pytest.fixture
def standard_client():
    app = create_app(Config)
    return app.test_client()


@pytest.fixture
def prefix_client():
    app = create_app(PrefixTestConfig)
    return app.test_client()


@pytest.fixture
def no_docs_client():
    app = create_app(DocsDisabledConfig)
    return app.test_client()


# 1. Local root URL loads
def test_local_root_url_loads(standard_client):
    response = standard_client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "AI Performance Analysis" in html
    assert '<meta name="app-base" content="">' in html
    assert "window.__APP_CONFIG__" in html
    assert "href=\"/swagger\"" in html or 'href="/swagger"' in html


# 2. LAN access is supported by the bind configuration
def test_lan_bind_configuration():
    assert Config.HOST in ("0.0.0.0", "")
    assert Config.PORT > 0


# 3. Static CSS and JavaScript return successful responses
def test_static_css_and_js_successful(standard_client):
    css_res = standard_client.get("/static/css/style.css")
    assert css_res.status_code == 200
    assert len(css_res.data) > 0

    js_res = standard_client.get("/static/js/app.js")
    assert js_res.status_code == 200
    assert "resolveApiUrl" in js_res.data.decode("utf-8")


# 4. Assets resolve correctly under URL prefix
def test_assets_under_prefix(prefix_client):
    # Static asset requested via prefix path
    css_res = prefix_client.get("/student-analysis/static/css/style.css")
    assert css_res.status_code == 200

    js_res = prefix_client.get("/student-analysis/static/js/app.js")
    assert js_res.status_code == 200

    # Index page renders base path and prefix links
    page_res = prefix_client.get("/student-analysis/")
    assert page_res.status_code == 200
    html = page_res.data.decode("utf-8")
    assert '<meta name="app-base" content="/student-analysis">' in html
    assert '"basePath": "/student-analysis"' in html
    assert 'href="/student-analysis/swagger"' in html


# 5. All frontend API requests target valid backend routes
def test_frontend_api_routes_exist(standard_client):
    # Health endpoint
    health_res = standard_client.get("/api/health")
    assert health_res.status_code == 200
    assert health_res.json == {"status": "ok"}

    # Upload endpoint with no file returns 400 (not 404)
    upload_res = standard_client.post("/api/upload")
    assert upload_res.status_code == 400

    # Class analysis endpoint with empty body returns 400 (not 404)
    class_res = standard_client.post(
        "/api/analyze/class",
        data=json.dumps({"students": []}),
        content_type="application/json"
    )
    assert class_res.status_code == 400

    # Student analysis endpoint with invalid student returns 400 (not 404)
    student_res = standard_client.post(
        "/api/analyze/student",
        data=json.dumps({"student": {}}),
        content_type="application/json"
    )
    assert student_res.status_code == 400


# 6. API requests work under configured URL prefix (both stripped and non-stripped)
def test_api_under_url_prefix(prefix_client):
    # Direct access with prefix in path
    res1 = prefix_client.get("/student-analysis/api/health")
    assert res1.status_code == 200
    assert res1.json == {"status": "ok"}

    # Reverse-proxy that stripped prefix but sent X-Forwarded-Prefix
    headers = {"HTTP_X_FORWARDED_PREFIX": "/student-analysis"}
    res2 = prefix_client.get("/api/health", environ_overrides=headers)
    assert res2.status_code == 200
    assert res2.json == {"status": "ok"}

    # Duplicate prefix normalization: /student-analysis/student-analysis/api/health
    res3 = prefix_client.get("/student-analysis/student-analysis/api/health")
    assert res3.status_code == 200


# 7. File uploads work and enforce size limits
def test_file_upload_csv(standard_client):
    csv_data = (
        "Student Name,English,Maths,Science\n"
        "Aarav Sharma,85,90,95\n"
        "Diya Patel,78,82,88\n"
    )
    file_bytes = io.BytesIO(csv_data.encode("utf-8"))
    data = {"file": (file_bytes, "report.csv")}
    response = standard_client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    students = response.json.get("students", [])
    assert len(students) == 2
    assert students[0]["name"] == "Aarav Sharma"
    assert students[0]["averageScore"] == 90.0


def test_file_upload_invalid_extension(standard_client):
    txt_data = io.BytesIO(b"random text")
    data = {"file": (txt_data, "notes.txt")}
    response = standard_client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert response.status_code == 400


# 8. Trailing slash and path redirects preserve expected path and scheme
def test_redirect_preserves_scheme_and_host(prefix_client):
    headers = {
        "HTTP_X_FORWARDED_PROTO": "https",
        "HTTP_X_FORWARDED_HOST": "example.com:8054",
        "HTTP_X_FORWARDED_PORT": "8054",
        "HTTP_X_FORWARDED_PREFIX": "/student-analysis"
    }
    # Requesting bare mount point should redirect to trailing slash with https and correct port
    response = prefix_client.get("/student-analysis", environ_overrides=headers)
    assert response.status_code in (301, 308)
    location = response.headers.get("Location")
    assert location == "https://example.com:8054/student-analysis/"


# 9. Documentation and OpenAPI routes work when enabled and disable when configured
def test_documentation_routes_enabled(prefix_client):
    headers = {
        "HTTP_X_FORWARDED_PROTO": "https",
        "HTTP_X_FORWARDED_HOST": "example.com:8054",
        "HTTP_X_FORWARDED_PREFIX": "/student-analysis"
    }
    doc_res = prefix_client.get("/student-analysis/swagger", environ_overrides=headers)
    assert doc_res.status_code == 200
    html = doc_res.data.decode("utf-8")
    assert "/student-analysis/api/swagger.json" in html

    specs_res = prefix_client.get("/student-analysis/api/swagger.json", environ_overrides=headers)
    assert specs_res.status_code == 200
    assert specs_res.json.get("basePath") == "/student-analysis/api"


def test_documentation_routes_disabled(no_docs_client):
    doc_res = no_docs_client.get("/swagger")
    assert doc_res.status_code == 404


# 10. HTTP and HTTPS reverse-proxy behavior without redirect loops
def test_reverse_proxy_https_behavior(prefix_client):
    headers = {
        "HTTP_X_FORWARDED_PROTO": "https",
        "HTTP_X_FORWARDED_HOST": "portal.school.edu",
        "HTTP_X_FORWARDED_PREFIX": "/student-analysis"
    }
    response = prefix_client.get("/student-analysis/", environ_overrides=headers)
    assert response.status_code == 200
    # No mixed-content http:// URLs in generated HTML
    html = response.data.decode("utf-8")
    assert "http://portal.school.edu" not in html


# 11. Trailing-slash flexibility on endpoints (both with and without trailing slash succeed)
def test_trailing_slash_flexibility(standard_client):
    res_no_slash = standard_client.get("/api/health")
    assert res_no_slash.status_code == 200

    res_with_slash = standard_client.get("/api/health/")
    assert res_with_slash.status_code == 200
