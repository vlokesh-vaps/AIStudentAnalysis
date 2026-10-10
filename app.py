import logging
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from flask_restx import Api, Resource
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.middleware.proxy_fix import ProxyFix

from api.class_analysis import ns as class_ns
from api.student_analysis import ns as student_ns
from api.upload import ns as upload_ns
from config import Config


class PrefixMiddleware:
    """WSGI middleware ensuring proper URL prefix handling.
    
    Ensures that:
    1. Deployments with a URL prefix (e.g. /student-analysis) set SCRIPT_NAME correctly.
    2. PATH_INFO starting with the prefix is stripped so inner routes match.
    3. Requests to the mount point without a trailing slash redirect to canonical trailing slash.
    4. Duplicated prefixes (e.g. /student-analysis/student-analysis) are normalized.
    5. Both stripped (rewritten) and non-stripped proxy configurations are supported.
    """

    def __init__(self, wsgi_app, prefix=""):
        self.wsgi_app = wsgi_app
        self.default_prefix = prefix.rstrip("/") if prefix else ""

    def __call__(self, environ, start_response):
        prefix = (
            environ.get("HTTP_X_FORWARDED_PREFIX")
            or environ.get("HTTP_X_SCRIPT_NAME")
            or environ.get("SCRIPT_NAME")
            or self.default_prefix
        ).strip().rstrip("/")
        if prefix and not prefix.startswith("/"):
            prefix = f"/{prefix}"

        script_name = environ.get("SCRIPT_NAME", "").rstrip("/")
        path_info = environ.get("PATH_INFO", "")

        if prefix:
            # Strip accidental repeated prefix (e.g. /student-analysis/student-analysis/...)
            while path_info.startswith(prefix + prefix + "/"):
                path_info = path_info[len(prefix):]

            if path_info == prefix:
                # Redirect bare prefix to trailing slash with preserved scheme and host
                scheme = environ.get("wsgi.url_scheme", "http")
                host = environ.get("HTTP_HOST") or environ.get("SERVER_NAME", "localhost")
                query = environ.get("QUERY_STRING", "")
                target = f"{scheme}://{host}{prefix}/" + (f"?{query}" if query else "")
                start_response("308 Permanent Redirect", [("Location", target), ("Content-Length", "0")])
                return [b""]
            elif path_info.startswith(prefix + "/"):
                environ["SCRIPT_NAME"] = prefix
                environ["PATH_INFO"] = path_info[len(prefix):]
            elif not script_name.endswith(prefix):
                environ["SCRIPT_NAME"] = prefix

        return self.wsgi_app(environ, start_response)


def create_app(config_object=Config):
    config_object.validate()

    app = Flask(__name__)
    app.config.from_object(config_object)

    # Configure logging
    log_level = getattr(logging, app.config.get("LOG_LEVEL", "INFO"), logging.INFO)
    logging.basicConfig(level=log_level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    app.logger.setLevel(log_level)

    # Allow endpoints to match with or without trailing slash
    app.url_map.strict_slashes = False

    # CORS configuration
    cors_origins = app.config.get("CORS_ORIGINS", "*")
    if cors_origins == "*":
        CORS(app)
    else:
        allowed = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
        CORS(app, origins=allowed)

    # Swagger / OpenAPI documentation availability
    doc_path = "/swagger" if app.config.get("ENABLE_DOCS", True) else False

    api_prefix = app.config.get("API_PREFIX", "/api")
    api = Api(
        app,
        version="1.0",
        title="AI Student Performance Analyzer API",
        description="Upload class reports and generate AI-assisted performance insights.",
        doc=doc_path,
        prefix=api_prefix,
    )
    api.add_namespace(upload_ns)
    api.add_namespace(class_ns)
    api.add_namespace(student_ns)

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            docs_enabled=bool(app.config.get("ENABLE_DOCS", True)),
        )

    @api.route("/health", strict_slashes=False)
    class Health(Resource):
        @api.doc(description="Check that the API is running.", responses={200: "API is healthy"})
        def get(self):
            return {"status": "ok"}

    @api.errorhandler(RequestEntityTooLarge)
    @app.errorhandler(413)
    def too_large(_error):
        limit_mb = app.config.get("MAX_UPLOAD_SIZE_MB", 25)
        return {"error": f"The uploaded file is too large. Maximum allowed size is {limit_mb} MB."}, 413

    # WSGI Middlewares:
    # 1. PrefixMiddleware handles SCRIPT_NAME and path stripping for URL prefix deployments
    app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix=app.config.get("APPLICATION_ROOT", ""))

    # 2. ProxyFix handles trusted forwarded headers (X-Forwarded-For, X-Forwarded-Proto, X-Forwarded-Host, X-Forwarded-Port, X-Forwarded-Prefix)
    trusted_proxies = app.config.get("TRUSTED_PROXIES", 0)
    if trusted_proxies > 0:
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=trusted_proxies,
            x_proto=trusted_proxies,
            x_host=trusted_proxies,
            x_port=trusted_proxies,
            x_prefix=trusted_proxies,
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host=app.config.get("HOST", "0.0.0.0"),
        port=app.config["PORT"],
        debug=app.config["DEBUG"],
    )
