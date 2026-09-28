from flask import current_app, request
from flask_restx import Namespace, Resource, fields

from services.ai import analyze_class_performance
from services.ai_errors import AIServiceError
from services.stats import build_class_payload

ns = Namespace("class_analysis", path="/analyze/class", description="Class performance analysis")
subject_input = ns.model("ClassStudentSubject", {
    "subject": fields.String(example="English"), "score": fields.Float(example=85),
    "maxScore": fields.Integer(example=100), "percentage": fields.Float(example=85),
})
student_input = ns.model("AnalysisStudent", {
    "name": fields.String(required=True, example="Abhishek Kumar"),
    "index": fields.Integer(example=0), "totalScore": fields.Float(example=343),
    "averageScore": fields.Float(required=True, example=85.75),
    "subjectCount": fields.Integer(example=4), "subjects": fields.List(fields.Nested(subject_input)),
})
request_model = ns.model("ClassAnalysisRequest", {"students": fields.List(fields.Nested(student_input), required=True)})
performer = ns.model("ClassPerformer", {
    "name": fields.String(example="Abhishek Kumar"), "averageScore": fields.Float(example=85.75),
    "totalScore": fields.Float(example=343), "analysis": fields.String(example="Consistent results across subjects."),
    "praise": fields.String, "recommendations": fields.String,
})
response_model = ns.model("ClassAnalysisResponse", {
    "weakPerformers": fields.List(fields.Nested(performer)),
    "topPerformers": fields.List(fields.Nested(performer)), "classOverview": fields.String,
})


@ns.route("")
class ClassAnalysis(Resource):
    @ns.expect(request_model, validate=True)
    @ns.response(200, "Class analysis", response_model)
    @ns.response(400, "Invalid student data")
    @ns.response(502, "AI analysis unavailable")
    def post(self):
        body = request.get_json(silent=True) or {}
        students = body.get("students") or []
        if not students:
            return {"error": "Please upload valid student data before analyzing the class."}, 400
        try:
            return analyze_class_performance(build_class_payload(students))
        except AIServiceError as exc:
            current_app.logger.exception("Class analysis failed")
            return {"error": exc.user_message}, exc.status_code
