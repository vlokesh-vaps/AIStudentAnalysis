import json
import logging
import re

from flask import current_app, has_app_context
from groq import Groq

from services.ai_errors import AIServiceError, friendly_error

logger = logging.getLogger(__name__)
MODEL = "openai/gpt-oss-20b"
SYSTEM = "You are an expert educational analyst. Always respond with valid JSON only, no additional text."


def _api_key():
    key = current_app.config.get("GROQ_API_KEY", "") if has_app_context() else ""
    if not key:
        raise AIServiceError("GROQ_API_KEY is not configured. Add it to your .env file and restart the app.", 503)
    return key


def _json_response(content):
    content = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", content, flags=re.I)
    match = re.search(r"\{[\s\S]*\}", content)
    return json.loads(match.group(0) if match else content)


def _call_groq(prompt, temperature, max_tokens, system=SYSTEM):
    try:
        client = Groq(api_key=_api_key(), timeout=60.0)
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        return _json_response(response.choices[0].message.content or "")
    except AIServiceError:
        raise
    except Exception as exc:
        raise friendly_error(exc) from exc


def analyze_class_performance(class_data):
    prompt = f'''You are an educational performance analyst. Analyze this class performance data and identify weak and top performers.

Class Data:
{json.dumps(class_data, indent=2, ensure_ascii=False)}

Provide detailed analysis in JSON format:
{{
  "weakPerformers": [{{"name": "...", "averageScore": number, "totalScore": number, "analysis": "...", "recommendations": "..."}}],
  "topPerformers": [{{"name": "...", "averageScore": number, "totalScore": number, "analysis": "...", "praise": "..."}}],
  "classOverview": "..."
}}

Identify exactly 5 weak performers and 5 top performers. Focus on overall performance, consistency, and specific subject strengths/weaknesses.'''
    result = _call_groq(prompt, 0.7, 3000)
    result.setdefault("weakPerformers", [])
    result.setdefault("topPerformers", [])
    result.setdefault("classOverview", "")
    return result


def analyze_student_performance(student):
    report = {"studentInfo": {"name": student.get("name"), "averageScore": student.get("averageScore"),
                               "totalScore": student.get("totalScore")}, "subjects": student.get("subjects", [])}
    prompt = f'''You are an educational performance analyst and predictive AI strategist. Analyze the following student report data and provide a detailed analysis along with AI-driven Performance Prediction for upcoming terms.

Student Report Data:
{json.dumps(report, indent=2, ensure_ascii=False)}

Please analyze this data and provide:
1. Weakest Subject: identify the subject with the lowest performance and explain why
2. Subjects Needing Improvement: list 2-3 subjects that need attention with specific recommendations
3. Strong Subjects: identify subjects where the student is performing well
4. Overall Assessment: overall performance summary with actionable advice
5. Improvement Strategy: a focused study plan
6. Performance Prediction: predict future exam performance, target score range, trajectory status ("Improving" | "Stable" | "At Risk" | "High Growth Potential"), predicted vs potential subject scores, key risk factors, and actionable milestones.

Format your response as JSON with this structure:
{{"weakestSubject": {{"name": "...", "score": number, "analysis": "..."}}, "needsImprovement": [{{"name": "...", "score": number, "recommendation": "..."}}], "strongSubjects": [{{"name": "...", "score": number, "praise": "..."}}], "overallAssessment": "...", "improvementStrategy": "...", "performancePrediction": {{"predictedScoreRange": "e.g., 85% - 90%", "confidenceLevel": "High (based on score consistency)", "trajectory": "High Growth Potential", "predictedSubjectScores": [{{"subject": "...", "predictedScore": number, "potentialScore": number}}], "keyRiskFactors": ["..."], "growthOpportunities": ["..."], "actionableMilestones": ["..."]}}}}'''
    result = _call_groq(prompt, 0.7, 2000)
    result.setdefault("performancePrediction", {})
    return result


def extract_students_from_pdf_text(text):
    prompt = f'''Extract student performance data from the provided text which was converted from a PDF school report. The text contains a table or list with student names, subjects, and marks.

Text to analyze:
{text[:30000]}

Instructions:
1. Identify each student and their respective scores in various subjects.
2. For each student, find their name and a list of subjects with their numeric scores.
3. If a cell contains both a score and a grade (e.g., "88 A"), extract ONLY the numeric score (88).
4. Calculate 'totalScore', 'averageScore' (total / count), and 'subjectCount' for each student.
5. Provide the output in a clean JSON format.

Return ONLY a JSON object with this structure:
{{"students": [{{"name": "string", "subjects": [{{"subject": "string", "score": number, "maxScore": 100, "percentage": number}}], "totalScore": number, "averageScore": number, "subjectCount": number}}]}}

Ensure all scores are numbers. If a score is missing or invalid, skip that subject for that student.'''
    result = _call_groq(prompt, 0.1, 4000,
                        "You are a precise data extraction expert. Always respond with valid JSON only.")
    students = result.get("students", [])
    cleaned = []
    for item in students:
        subjects = []
        for subject in item.get("subjects", []):
            try:
                score = float(subject["score"])
                if not 0 <= score <= 200:
                    continue
                subjects.append({"subject": str(subject.get("subject", "Subject")), "score": score,
                                 "maxScore": int(subject.get("maxScore", 100)),
                                 "percentage": float(subject.get("percentage", score if score <= 100 else score / 2))})
            except (KeyError, TypeError, ValueError):
                continue
        if item.get("name") and subjects:
            total = round(sum(s["score"] for s in subjects), 2)
            cleaned.append({"name": str(item["name"]), "index": len(cleaned), "subjects": subjects,
                            "totalScore": total, "averageScore": round(total / len(subjects), 2),
                            "subjectCount": len(subjects)})
    return cleaned
