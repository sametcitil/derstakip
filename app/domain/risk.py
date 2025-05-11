from datetime import date, timedelta
from typing import Set, List, Dict, Any

from app.domain.models import Student, Assignment
from app.domain.ds.assignment_heap import AssignmentMinHeap
from app.domain.ds.prereq_graph import PrereqGraph


class RiskEngine:
    """
    Engine for calculating student risk based on various factors.
    """
    
    def __init__(self, storage):
        """
        Initialize the risk engine with storage dependency.
        
        Args:
            storage: The storage module for accessing student and course data.
        """
        self.storage = storage
        self._prereq_graph = None
        self._init_prereq_graph()
    
    def _init_prereq_graph(self) -> None:
        """Initialize the prerequisite graph from course catalog."""
        courses = self.storage.load_course_catalog()
        self._prereq_graph = PrereqGraph()
        
        for course in courses:
            self._prereq_graph.add_course(course["code"], course.get("prereq", []))
    
    def calculate(self, student: Student) -> float:
        """
        Calculate the overall risk score for a student.
        
        The risk score is a weighted sum of various risk factors:
        - Absence risk (30%)
        - Assignment risk (30%)
        - Prerequisite risk (25%)
        - GPA risk (15%)
        
        Returns:
            A risk score between 0.0 (no risk) and 1.0 (highest risk).
        """
        # Calculate individual risk components
        absence_risk = self._calculate_absence_risk(student)
        assignment_risk = self._calculate_assignment_risk(student)
        prereq_risk = self._calculate_prereq_risk(student)
        gpa_risk = self._calculate_gpa_risk(student)
        
        # Apply weights to each component
        weighted_risk = (
            0.30 * absence_risk +
            0.30 * assignment_risk +
            0.25 * prereq_risk +
            0.15 * gpa_risk
        )
        
        return min(1.0, max(0.0, weighted_risk))
    
    def _calculate_absence_risk(self, student: Student) -> float:
        """
        Calculate risk based on student absences.
        
        Uses the absence_bits field, where each bit represents an absence.
        The risk increases as the number of absences approaches the maximum allowed.
        """
        # Count the number of 1 bits in absence_bits
        absence_count = bin(student.absence_bits).count('1')
        
        # Maximum allowed absences (typically 14 in a semester)
        max_absences = 14
        
        # Calculate risk as a ratio of absences to maximum allowed
        if max_absences == 0:
            return 0.0
            
        risk = absence_count / max_absences
        
        # Apply a non-linear scaling to emphasize risk as absences approach the limit
        if risk > 0.7:
            # Increase risk more rapidly as it approaches the limit
            risk = 0.7 + (risk - 0.7) * 1.5
            
        return min(1.0, max(0.0, risk))
    
    def _calculate_assignment_risk(self, student: Student) -> float:
        """
        Calculate risk based on missed or upcoming assignments.
        
        Considers:
        - Proportion of missed assignments
        - Proximity of upcoming deadlines
        """
        if not student.assignments:
            return 0.0
            
        # Count missed assignments
        total_assignments = len(student.assignments)
        missed_assignments = sum(1 for a in student.assignments 
                               if not a.done and a.deadline < date.today())
        
        # Calculate risk from missed assignments (50% of assignment risk)
        missed_risk = missed_assignments / total_assignments if total_assignments > 0 else 0.0
        
        # Calculate risk from upcoming deadlines (50% of assignment risk)
        heap = AssignmentMinHeap.from_assignments(student.assignments)
        upcoming = heap.get_due_soon(days=7)
        
        # Calculate deadline risk based on how soon assignments are due
        today = date.today()
        deadline_risk = 0.0
        
        for assignment in upcoming:
            if assignment.done:
                continue
                
            days_left = (assignment.deadline - today).days
            # Higher risk for closer deadlines
            if days_left <= 1:
                deadline_risk += 1.0
            elif days_left <= 3:
                deadline_risk += 0.7
            elif days_left <= 5:
                deadline_risk += 0.4
            else:
                deadline_risk += 0.2
        
        # Normalize deadline risk
        max_deadline_risk = len(upcoming)
        if max_deadline_risk > 0:
            deadline_risk = deadline_risk / max_deadline_risk
        
        # Combine missed and deadline risks
        return 0.5 * missed_risk + 0.5 * deadline_risk
    
    def _calculate_prereq_risk(self, student: Student) -> float:
        """
        Calculate risk based on prerequisite issues.
        
        Checks if the student is taking courses without completing prerequisites.
        """
        if not self._prereq_graph:
            return 0.0
            
        # Get all courses the student has completed
        completed_courses = set()
        current_courses = set()
        
        for term in student.terms:
            # Assume courses in past terms are completed
            if term.year < date.today().year or (
                term.year == date.today().year and 
                ((term.semester == 1 and date.today().month > 6) or  # Spring term is over after June
                 (term.semester == 2 and date.today().month > 12) or  # Fall term is over after December
                 (term.semester == 3 and date.today().month > 8))     # Summer term is over after August
            ):
                completed_courses.update(term.courses)
            else:
                # Current term courses
                current_courses.update(term.courses)
        
        # Check prerequisites for current courses
        missing_prereqs = 0
        total_prereqs = 0
        
        for course in current_courses:
            prereqs = self._prereq_graph.get_prerequisites(course)
            total_prereqs += len(prereqs)
            missing = self._prereq_graph.find_missing_prerequisites(course, completed_courses)
            missing_prereqs += len(missing)
        
        # Calculate risk based on missing prerequisites
        if total_prereqs == 0:
            return 0.0
            
        return min(1.0, missing_prereqs / total_prereqs)
    
    def _calculate_gpa_risk(self, student: Student) -> float:
        """
        Calculate risk based on GPA.
        
        Lower GPA indicates higher risk.
        """
        # Assume GPA is on a 4.0 scale
        # Risk increases as GPA decreases
        if student.gpa >= 3.5:
            return 0.0
        elif student.gpa >= 3.0:
            return 0.2
        elif student.gpa >= 2.5:
            return 0.4
        elif student.gpa >= 2.0:
            return 0.6
        elif student.gpa >= 1.5:
            return 0.8
        else:
            return 1.0 