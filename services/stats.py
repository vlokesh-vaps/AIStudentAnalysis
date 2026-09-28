import numpy as np
import pandas as pd


def build_class_payload(students):
    rows = [{"name": item.get("name", ""), "totalScore": float(item.get("totalScore", 0) or 0),
             "averageScore": float(item.get("averageScore", 0) or 0),
             "subjectCount": int(item.get("subjectCount", len(item.get("subjects", []))) or 0),
             "subjects": item.get("subjects", [])} for item in students]
    df = pd.DataFrame(rows)
    if df.empty:
        return {"totalStudents": 0, "topPerformers": [], "weakPerformers": []}
    # Stable sorting preserves upload order for ties; ties can otherwise reorder between pandas versions.
    top = df.sort_values("averageScore", ascending=False, kind="stable").head(5)
    weak = df.sort_values("averageScore", ascending=True, kind="stable").head(5)
    return {"totalStudents": int(len(df)), "topPerformers": top.replace({np.nan: None}).to_dict("records"),
            "weakPerformers": weak.replace({np.nan: None}).to_dict("records")}


def subject_statistics(students):
    records = [{"subject": s.get("subject"), "score": s.get("score")}
               for student in students for s in student.get("subjects", [])]
    if not records:
        return pd.DataFrame(columns=["mean", "std", "min", "max"])
    return pd.DataFrame(records).groupby("subject")["score"].agg(["mean", "std", "min", "max"])
