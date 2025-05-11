from pathlib import Path
import json
import os
from filelock import FileLock
from typing import Iterator, Optional

from app.domain.models import Student, Assignment


DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DATA_DIR.mkdir(exist_ok=True)


def _file_path(student_id: int) -> Path:
    return DATA_DIR / f"student_{student_id}.json"


def load_student(student_id: int) -> Optional[Student]:
    fp = _file_path(student_id)
    if not fp.exists():
        return None
    with fp.open() as f:
        data = json.load(f)
        
    # Convert assignment dict to Assignment objects
    if "assignments" in data:
        for i, assignment in enumerate(data["assignments"]):
            if isinstance(assignment, dict):
                data["assignments"][i] = Assignment.model_validate(assignment)
    
    return Student.model_validate(data)


def save_student(student: Student) -> None:
    fp = _file_path(student.id)
    lock = FileLock(str(fp) + ".lock")
    with lock, fp.open("w") as f:
        json.dump(student.model_dump(mode="json"), f, indent=2)


def next_student_id() -> int:
    # ID üretmek için basit artan sayaç dosyası
    seq = DATA_DIR / "id_seq.txt"
    seq.touch(exist_ok=True)
    lock = FileLock(str(seq) + ".lock")
    with lock:
        val = int(seq.read_text() or "0") + 1
        seq.write_text(str(val))
    return val


def iter_all_students() -> Iterator[Student]:
    for fp in DATA_DIR.glob("student_*.json"):
        with fp.open() as f:
            yield Student.model_validate(json.load(f))


def save_course_catalog(courses: list) -> None:
    catalog_path = DATA_DIR / "course_catalog.json"
    lock = FileLock(str(catalog_path) + ".lock")
    with lock, catalog_path.open("w") as f:
        json.dump(courses, f, indent=2)


def load_course_catalog() -> list:
    catalog_path = DATA_DIR / "course_catalog.json"
    if not catalog_path.exists():
        return []
    with catalog_path.open() as f:
        return json.load(f) 