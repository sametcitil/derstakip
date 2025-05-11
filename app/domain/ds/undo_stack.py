from collections import deque
from typing import TypeVar, Generic, Deque, Optional, Callable

T = TypeVar('T')


class UndoStack(Generic[T]):
    """
    A stack for undo/redo operations.
    Uses two collections.deque instances to track undo and redo history.
    """
    
    def __init__(self, max_size: int = 100):
        self._undo_stack: Deque[T] = deque(maxlen=max_size)
        self._redo_stack: Deque[T] = deque(maxlen=max_size)
    
    def push(self, state: T) -> None:
        """Push a new state onto the undo stack and clear the redo stack."""
        self._undo_stack.append(state)
        self._redo_stack.clear()
    
    def undo(self) -> Optional[T]:
        """
        Pop the most recent state from the undo stack and push it to the redo stack.
        Returns the previous state or None if there's no state to undo.
        """
        if not self._undo_stack:
            return None
        
        state = self._undo_stack.pop()
        self._redo_stack.append(state)
        
        # Return the previous state (now at the top of the undo stack)
        if self._undo_stack:
            return self._undo_stack[-1]
        return None
    
    def redo(self) -> Optional[T]:
        """
        Pop the most recent state from the redo stack and push it to the undo stack.
        Returns the redone state or None if there's no state to redo.
        """
        if not self._redo_stack:
            return None
        
        state = self._redo_stack.pop()
        self._undo_stack.append(state)
        
        return state
    
    def can_undo(self) -> bool:
        """Check if there are states that can be undone."""
        return len(self._undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if there are states that can be redone."""
        return len(self._redo_stack) > 0
    
    def clear(self) -> None:
        """Clear both undo and redo stacks."""
        self._undo_stack.clear()
        self._redo_stack.clear()
    
    def current_state(self) -> Optional[T]:
        """Get the current state without modifying the stacks."""
        if not self._undo_stack:
            return None
        return self._undo_stack[-1] 