import networkx as nx
from typing import Dict, List, Set, Optional


class PrereqGraph:
    """
    A directed graph representing course prerequisites.
    Uses networkx.DiGraph as the underlying data structure.
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
    
    def add_course(self, course_code: str, prereqs: List[str] = None) -> None:
        """Add a course to the graph with its prerequisites."""
        if not self.graph.has_node(course_code):
            self.graph.add_node(course_code)
            
        if prereqs:
            for prereq in prereqs:
                if not self.graph.has_node(prereq):
                    self.graph.add_node(prereq)
                self.graph.add_edge(prereq, course_code)
    
    def get_prerequisites(self, course_code: str) -> Set[str]:
        """Get all prerequisites for a course (direct and indirect)."""
        if not self.graph.has_node(course_code):
            return set()
            
        return set(nx.ancestors(self.graph, course_code))
    
    def get_direct_prerequisites(self, course_code: str) -> Set[str]:
        """Get only direct prerequisites for a course."""
        if not self.graph.has_node(course_code):
            return set()
            
        return set(self.graph.predecessors(course_code))
    
    def check_can_take_course(self, course_code: str, completed_courses: Set[str]) -> bool:
        """Check if a student can take a course based on completed prerequisites."""
        prereqs = self.get_prerequisites(course_code)
        return prereqs.issubset(completed_courses)
    
    def find_missing_prerequisites(self, course_code: str, completed_courses: Set[str]) -> Set[str]:
        """Find prerequisites that are still missing."""
        prereqs = self.get_prerequisites(course_code)
        return prereqs - completed_courses
    
    def detect_cycles(self) -> List[List[str]]:
        """Detect cycles in the prerequisite graph (which would be an error)."""
        return list(nx.simple_cycles(self.graph))
    
    def build_from_courses(self, courses_dict: Dict[str, List[str]]) -> None:
        """Build the graph from a dictionary of courses and their prerequisites."""
        for course_code, prereqs in courses_dict.items():
            self.add_course(course_code, prereqs) 