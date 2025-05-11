from pydantic import BaseModel
from datetime import date
from typing import List, Dict, Any, Optional


class Course(BaseModel):
    code: str
    title: str
    credit: int
    prereq: List[str] = []


class Term(BaseModel):
    year: int
    semester: int           # 1: bahar, 2: güz, 3: yaz
    courses: List[str] = [] # course codes


class Assignment(BaseModel):
    deadline: date
    done: bool = False


class Student(BaseModel):
    id: int
    name: str
    gpa: float = 0.0
    absence_bits: int = 0               # 14 bit devamsızlık
    terms: List[Term] = []
    assignments: List[Assignment] = [] 