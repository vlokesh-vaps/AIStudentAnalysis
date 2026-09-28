import pandas as pd

from services.parser import parse_dataframe


def test_exact_header_and_grade_suffix():
    frame = pd.DataFrame([
        ["Exam report", None, None, None],
        ["Student Name", "English", "Hindi", "Total"],
        ["Asha Rao", "88 A", 79, 167],
        ["Ravi Das", 70, "81 B", 151],
    ])
    students = parse_dataframe(frame)
    assert [item["name"] for item in students] == ["Asha Rao", "Ravi Das"]
    assert students[0]["subjects"][0]["score"] == 88
    assert students[0]["averageScore"] == 83.5


def test_fallback_header_and_absent_values():
    frame = pd.DataFrame([
        ["Name", "English", "Science", "Class Total"],
        ["Mina Shah", "AB", "74", "74"],
        ["Dev Patel", "absent", "82", "82"],
    ])
    students = parse_dataframe(frame)
    assert len(students) == 2
    assert [student["subjectCount"] for student in students] == [1, 1]
    assert students[0]["subjects"][0]["subject"] == "Science"


def test_out_of_200_marks_get_percentage_heuristic():
    frame = pd.DataFrame([["Student Name", "Mathematics", "English"], ["Noor", 156, 88]])
    student = parse_dataframe(frame)[0]
    assert student["subjects"][0]["score"] == 156
    assert student["subjects"][0]["percentage"] == 78


def test_unparseable_data_returns_empty_list():
    assert parse_dataframe(pd.DataFrame([["Report", "Marks"], ["Asha", 90]])) == []
