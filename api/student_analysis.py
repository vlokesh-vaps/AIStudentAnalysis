from flask import current_app, request
from flask_restx import Namespace, Resource, fields

from services.ai import analyze_student_performance
from services.ai_errors import AIServiceError

ns = Namespace("student_analysis", path="/analyze/student", description="Individual student analysis")
subject_input = ns.model("StudentReportSubject", {
    "subject": fields.String(example="English"), "score": fields.Float(example=85),
    "maxScore": fields.Integer(example=100), "percentage": fields.Float(example=85),
})
student_input = ns.model("StudentAnalysisInput", {
    "name": fields.String(required=True, example="Abhishek Kumar"),
    "averageScore": fields.Float(required=True, example=85.75), "totalScore": fields.Float(example=343),
    "subjects": fields.List(fields.Nested(subject_input), required=True,
                             example=[{"subject": "English", "score": 85, "maxScore": 100, "percentage": 85}]),
})
request_model = ns.model("StudentAnalysisRequest", {"student": fields.Nested(student_input, required=True)})
weakest_subject = ns.model("WeakestSubject", {
    "name": fields.String(example="Maths"), "score": fields.Float(example=62),
    "analysis": fields.String(example="Recent results suggest the core concepts need reinforcement."),
})
improvement_item = ns.model("ImprovementSubject", {
    "name": fields.String(example="Maths"), "score": fields.Float(example=62),
    "recommendation": fields.String(example="Practice targeted problems for 20 minutes each day."),
})
strong_subject = ns.model("StrongSubject", {
    "name": fields.String(example="English"), "score": fields.Float(example=88),
    "praise": fields.String(example="Strong comprehension and consistent results."),
})
predicted_subject = ns.model("PredictedSubjectScore", {
    "subject": fields.String(example="Maths"), "predictedScore": fields.Float(example=72),
    "potentialScore": fields.Float(example=84),
})
prediction = ns.model("PerformancePrediction", {
    "predictedScoreRange": fields.String(example="85% - 90%"), "confidenceLevel": fields.String(example="High"),
    "trajectory": fields.String(example="Improving"), "predictedSubjectScores": fields.List(fields.Nested(predicted_subject)),
    "keyRiskFactors": fields.List(fields.String), "growthOpportunities": fields.List(fields.String),
    "actionableMilestones": fields.List(fields.String),
})
response_model = ns.model("StudentAnalysisResponse", {
    "weakestSubject": fields.Nested(weakest_subject),
    "needsImprovement": fields.List(fields.Nested(improvement_item)),
    "strongSubjects": fields.List(fields.Nested(strong_subject)),
    "overallAssessment": fields.String, "improvementStrategy": fields.String,
    "performancePrediction": fields.Nested(prediction),
})


@ns.route("", strict_slashes=False)
class StudentAnalysis(Resource):
    @ns.expect(request_model, validate=True)
    @ns.response(200, "Student analysis", response_model)
    @ns.response(400, "Invalid student data")
    @ns.response(502, "AI analysis unavailable")
    def post(self):
        body = request.get_json(silent=True) or {}
        student = body.get("student")
        if not isinstance(student, dict) or not student.get("name") or not student.get("subjects"):
            return {"error": "Select a student with valid subject data."}, 400
        try:
            return analyze_student_performance(student)
        except AIServiceError as exc:
            current_app.logger.exception("Student analysis failed for %s", student.get("name"))
            return {"error": exc.user_message}, exc.status_code
