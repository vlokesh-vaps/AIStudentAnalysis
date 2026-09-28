import io
import re

import pandas as pd

ALIASES = {"student name", "name of student", "candidate name", "studentname", "student", "name"}
EXCLUDED = {"sl", "no", "id", "rank", "total", "avg", "average", "grade", "result", "class",
            "section", "division", "percentage", "attendance", "remarks", "pass", "fail", "promoted"}
ABSENT = {"ab", "absent", "-", "na", "nil", "abst"}
NUMBER = re.compile(r"([0-9]+(?:\.[0-9]+)?)")


def _text(value):
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _detect_header(df):
    for row_index in range(min(50, len(df))):
        for col_index, value in enumerate(df.iloc[row_index].tolist()):
            if _text(value).lower() in ALIASES:
                return row_index, col_index
    for row_index in range(min(50, len(df))):
        values = [_text(v) for v in df.iloc[row_index].tolist()]
        joined = " ".join(values).lower()
        if "name" in joined and any(word in joined for word in ("total", "class", "english")):
            name_col = next((i for i, v in enumerate(values) if "name" in v.lower()), None)
            if name_col is not None:
                return row_index, name_col
    return None, None


def parse_dataframe(df):
    if df is None or df.empty:
        return []
    header_row, name_col = _detect_header(df)
    if header_row is None:
        return []
    headers = [_text(v) for v in df.iloc[header_row].tolist()]
    if name_col is None:
        name_col = 1 if headers and any(token in headers[0].lower() for token in ("sl", "no")) else 0
    subject_cols = []
    for col, raw in enumerate(headers):
        if col == name_col:
            continue
        normalized = raw.lower().strip()
        stripped = re.sub(r"[^a-z]", "", normalized)
        words = set(re.findall(r"[a-z]+", normalized))
        excluded = stripped in {re.sub(r"[^a-z]", "", x) for x in EXCLUDED} or bool(words & EXCLUDED)
        if not excluded and any(normalized == f"{word} no" or normalized == f"{word}." or normalized == f"student {word}" for word in EXCLUDED):
            excluded = True
        if not excluded and len(stripped) > 2:
            subject_cols.append((col, raw))

    students = []
    for _, row in df.iloc[header_row + 1:].iterrows():
        name = _text(row.iloc[name_col]) if name_col < len(row) else ""
        lowered = name.lower()
        if not name or "total" in lowered or "class average" in lowered:
            continue
        subjects = []
        for col, raw_subject in subject_cols:
            if col >= len(row):
                continue
            value = row.iloc[col]
            text = _text(value)
            if not text or text.lower() in ABSENT:
                continue
            match = NUMBER.search(text)
            if not match:
                continue
            score = float(match.group(1))
            if not 0 <= score <= 200:
                continue
            subject = re.sub(r"\([^)]*\)|\[[^]]*\]", "", raw_subject)
            subject = subject.split("|", 1)[0].strip()
            if len(subject) < 2:
                subject = f"Subject {col}"
            percentage = score / 2 if score > 100 else score
            subjects.append({"subject": subject, "score": score, "maxScore": 100, "percentage": round(percentage, 2)})
        if subjects:
            total = round(sum(s["score"] for s in subjects), 2)
            students.append({"name": name, "index": len(students), "subjects": subjects, "totalScore": total,
                             "averageScore": round(total / len(subjects), 2), "subjectCount": len(subjects)})
    return students


def parse_upload(file_storage, filename=None, pdf_extractor=None):
    filename = (filename or file_storage.filename or "").lower()
    data = file_storage.read()
    if filename.endswith(".csv"):
        return parse_dataframe(pd.read_csv(io.BytesIO(data), header=None, dtype=object))
    if filename.endswith((".xlsx", ".xls")):
        sheets = pd.read_excel(io.BytesIO(data), sheet_name=None, header=None, dtype=object, engine="openpyxl" if filename.endswith(".xlsx") else None)
        for frame in sheets.values():
            parsed = parse_dataframe(frame)
            if parsed:
                return parsed
        return []
    if filename.endswith(".pdf"):
        import pdfplumber
        frames = []
        text_parts = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                text_parts.append(page.extract_text() or "")
                table = page.extract_table()
                if table:
                    frames.append(pd.DataFrame(table))
        for frame in frames:
            parsed = parse_dataframe(frame)
            if parsed:
                return parsed
        text = "\n".join(text_parts).strip()
        if text and pdf_extractor:
            return pdf_extractor(text[:30000])
        return []
    raise ValueError("Unsupported file type. Upload CSV, XLSX, XLS, or PDF.")
