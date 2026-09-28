from flask import Flask, jsonify, render_template
from flask_cors import CORS
from flask_restx import Api, Resource

from api.class_analysis import ns as class_ns
from api.student_analysis import ns as student_ns
from api.upload import ns as upload_ns
from config import Config


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    CORS(app)

    api = Api(app, version="1.0", title="AI Student Performance Analyzer API",
              description="Upload class reports and generate AI-assisted performance insights.",
              doc="/swagger", prefix="/api")
    api.add_namespace(upload_ns)
    api.add_namespace(class_ns)
    api.add_namespace(student_ns)

    @app.get("/")
    def index():
        return render_template("index.html")

    @api.route("/health")
    class Health(Resource):
        @api.doc(description="Check that the API is running.", responses={200: "API is healthy"})
        def get(self):
            return {"status": "ok"}

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify({"error": "The uploaded file is too large."}), 413

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=app.config["PORT"], debug=app.config["DEBUG"])
