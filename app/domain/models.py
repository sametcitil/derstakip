from pydantic import BaseModel
from datetime import date
from typing import List, Dict, Any, Optional


class Course(BaseModel):
    """
    Ders modeli - bir dersin temel bilgilerini içerir.
    """
    code: str        # Ders kodu (örn. CS101)
    title: str       # Ders başlığı
    credit: int      # Ders kredisi
    prereq: List[str] = []  # Ön koşul ders kodları listesi


class CourseEnrollment(BaseModel):
    """
    Bir öğrencinin aldığı dersi ve tamamlama durumunu temsil eder.
    """
    code: str               # Ders kodu
    completed: bool = False  # Dersin tamamlanma durumu
    grade: Optional[str] = None  # Ders notu (opsiyonel)


class Term(BaseModel):
    """
    Dönem modeli - bir akademik dönemi temsil eder.
    """
    year: int                # Akademik yıl
    semester: int            # 1: bahar, 2: güz, 3: yaz
    courses: List[CourseEnrollment] = []  # Dönemde alınan dersler


class Assignment(BaseModel):
    """
    Ödev modeli - öğrencinin tamamlaması gereken ödevleri temsil eder.
    """
    deadline: date    # Son teslim tarihi
    done: bool = False  # Ödevin tamamlanma durumu


class Student(BaseModel):
    """
    Öğrenci modeli - bir öğrencinin tüm akademik bilgilerini içerir.
    """
    id: int                           # Öğrenci numarası
    name: str                         # Öğrenci adı
    gpa: float = 0.0                  # Genel not ortalaması
    absence_bits: int = 0             # 14 bit devamsızlık bilgisi (her bit bir devamsızlığı temsil eder)
    terms: List[Term] = []            # Öğrencinin kayıtlı olduğu dönemler
    assignments: List[Assignment] = [] # Öğrencinin ödevleri 