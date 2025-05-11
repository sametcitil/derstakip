import heapq
from datetime import date, datetime
from typing import List, Tuple, Optional

from app.domain.models import Assignment


class AssignmentMinHeap:
    """
    A min-heap for assignments, ordered by deadline.
    Uses Python's heapq module as the underlying implementation.
    """
    
    def __init__(self):
        self._heap = []
    
    def add(self, assignment: Assignment) -> None:
        """Add an assignment to the heap."""
        # Convert date to comparable format and use as key
        deadline_key = assignment.deadline.toordinal()
        heapq.heappush(self._heap, (deadline_key, assignment))
    
    def peek(self) -> Optional[Assignment]:
        """Get the assignment with the earliest deadline without removing it."""
        if not self._heap:
            return None
        return self._heap[0][1]
    
    def pop(self) -> Optional[Assignment]:
        """Remove and return the assignment with the earliest deadline."""
        if not self._heap:
            return None
        return heapq.heappop(self._heap)[1]
    
    def is_empty(self) -> bool:
        """Check if the heap is empty."""
        return len(self._heap) == 0
    
    def size(self) -> int:
        """Get the number of assignments in the heap."""
        return len(self._heap)
    
    def get_all_sorted(self) -> List[Assignment]:
        """Get all assignments sorted by deadline."""
        # Create a copy to avoid modifying the original heap
        heap_copy = self._heap.copy()
        result = []
        
        while heap_copy:
            result.append(heapq.heappop(heap_copy)[1])
            
        return result
    
    def get_due_soon(self, days: int = 7) -> List[Assignment]:
        """Get assignments due within the specified number of days."""
        today = date.today()
        cutoff = today.toordinal() + days
        
        result = []
        for deadline_key, assignment in self._heap:
            if deadline_key <= cutoff:
                result.append(assignment)
        
        # Sort by deadline
        result.sort(key=lambda a: a.deadline)
        return result
    
    @classmethod
    def from_assignments(cls, assignments: List[Assignment]) -> 'AssignmentMinHeap':
        """Create a heap from a list of assignments."""
        heap = cls()
        for assignment in assignments:
            heap.add(assignment)
        return heap 