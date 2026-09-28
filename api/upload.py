from flask import current_app, request
from flask_restx import Namespace, Resource, fields
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from services.ai import extract_students_from_pdf_text
from services.parser import parse_upload
from services.ai_errors import AIServiceError

ns = Namespace("upload", path="/upload", description="Class report upload")
student_subject = ns.model("StudentSubject", {
    "subject": fields.String(example="English"), "score": fields.Float(example=85),
    "maxScore": fields.Integer(example=100), "percentage": fields.Float(example=85),
})
student_model = ns.model("Student", {
    "name": fields.String(example="Abhishek Kumar"), "index": fields.Integer(example=0),
    "subjects": fields.List(fields.Nested(student_subject)), "totalScore": fields.Float(example=343),
    "averageScore": fields.Float(example=85.75), "subjectCount": fields.Integer(example=4),
})
upload_response = ns.model("UploadResponse", {"students": fields.List(fields.Nested(student_model))})


@ns.route("")
class Upload(Resource):
    @ns.doc(consumes=["multipart/form-data"], description="Parse a CSV, Excel, or PDF class report.")
    @ns.expect(ns.parser().add_argument("file", location="files", type=FileStorage, required=True,
                                        help="CSV, XLSX, XLS, or PDF report"))
    @ns.response(200, "Parsed students", upload_response)
    @ns.response(400, "Invalid upload or no student records found", ns.model("Error", {"error": fields.String(example="No valid student data found. Please check the file format.")}))
    def post(self):
        uploaded = request.files.get("file")
        if not uploaded or not uploaded.filename:
            return {"error": "Please select a file to upload."}, 400
        filename = secure_filename(uploaded.filename)
        try:
            students = parse_upload(uploaded, filename, pdf_extractor=extract_students_from_pdf_text)
        except AIServiceError as exc:
            current_app.logger.exception("PDF extraction failed")
            return {"error": exc.user_message}, exc.status_code
        except Exception:
            current_app.logger.exception("File parsing failed: %s", filename)
            return {"error": "Unable to read this file. Please check its format and try again."}, 400
        if not students:
            return {"error": "No valid student data found. Please check the file format."}, 400
        return {"students": students}
