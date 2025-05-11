import unittest
from datetime import date, timedelta
from unittest.mock import MagicMock

from app.domain.models import Student, Term, Assignment
from app.domain.risk import RiskEngine


class TestRiskEngine(unittest.TestCase):
    
    def setUp(self):
        # Create a mock storage
        self.mock_storage = MagicMock()
        
        # Set up sample course catalog
        self.mock_storage.load_course_catalog.return_value = [
            {
                "code": "CS101",
                "title": "Introduction to Computer Science",
                "credit": 3,
                "prereq": []
            },
            {
                "code": "CS102",
                "title": "Data Structures",
                "credit": 4,
                "prereq": ["CS101"]
            },
            {
                "code": "CS201",
                "title": "Algorithms",
                "credit": 4,
                "prereq": ["CS102"]
            }
        ]
        
        # Create risk engine with mock storage
        self.risk_engine = RiskEngine(self.mock_storage)
    
    def test_calculate_no_risk(self):
        # Create a student with no risk factors
        student = Student(
            id=1,
            name="John Doe",
            gpa=4.0,
            absence_bits=0,
            terms=[
                Term(
                    year=date.today().year - 1,
                    semester=1,
                    courses=["CS101"]
                ),
                Term(
                    year=date.today().year,
                    semester=1,
                    courses=["CS102"]
                )
            ],
            assignments=[]
        )
        
        # Calculate risk
        risk = self.risk_engine.calculate(student)
        
        # Should have very low risk
        self.assertLess(risk, 0.1)
    
    def test_calculate_high_risk(self):
        # Create a student with multiple risk factors
        today = date.today()
        
        student = Student(
            id=2,
            name="Jane Smith",
            gpa=1.2,  # Low GPA
            absence_bits=0b1111111111,  # Many absences
            terms=[
                Term(
                    year=today.year - 1,
                    semester=1,
                    courses=[]  # No completed courses
                ),
                Term(
                    year=today.year,
                    semester=1,
                    courses=["CS201"]  # Taking advanced course without prerequisites
                )
            ],
            assignments=[
                Assignment(
                    deadline=today - timedelta(days=5),
                    done=False  # Missed assignment
                ),
                Assignment(
                    deadline=today + timedelta(days=1),
                    done=False  # Upcoming deadline
                )
            ]
        )
        
        # Calculate risk
        risk = self.risk_engine.calculate(student)
        
        # Should have high risk
        self.assertGreater(risk, 0.7)
    
    def test_absence_risk(self):
        # Test absence risk calculation
        student = Student(
            id=3,
            name="Test Student",
            absence_bits=0b1111  # 4 absences
        )
        
        absence_risk = self.risk_engine._calculate_absence_risk(student)
        
        # 4 out of 14 absences should give moderate risk
        self.assertGreater(absence_risk, 0.2)
        self.assertLess(absence_risk, 0.4)
    
    def test_gpa_risk(self):
        # Test GPA risk levels
        gpa_tests = [
            (4.0, 0.0),  # No risk
            (3.2, 0.2),  # Low risk
            (2.2, 0.4),  # Medium risk
            (1.7, 0.6),  # High risk
            (1.0, 1.0)   # Very high risk
        ]
        
        for gpa, expected_risk in gpa_tests:
            student = Student(id=4, name="GPA Test", gpa=gpa)
            risk = self.risk_engine._calculate_gpa_risk(student)
            self.assertAlmostEqual(risk, expected_risk, places=1)


if __name__ == "__main__":
    unittest.main() 