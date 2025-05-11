from typing import TypeVar, Generic, Optional, Iterator, List

T = TypeVar('T')


class Node(Generic[T]):
    """A node in a singly linked list."""
    
    def __init__(self, value: T):
        self.value = value
        self.next: Optional[Node[T]] = None


class LinkedList(Generic[T]):
    """
    A simple singly linked list implementation.
    """
    
    def __init__(self):
        self.head: Optional[Node[T]] = None
        self.tail: Optional[Node[T]] = None
        self._size = 0
    
    def append(self, value: T) -> None:
        """Add a value to the end of the list."""
        new_node = Node(value)
        
        if self.head is None:
            self.head = new_node
            self.tail = new_node
        else:
            assert self.tail is not None
            self.tail.next = new_node
            self.tail = new_node
            
        self._size += 1
    
    def prepend(self, value: T) -> None:
        """Add a value to the beginning of the list."""
        new_node = Node(value)
        
        if self.head is None:
            self.head = new_node
            self.tail = new_node
        else:
            new_node.next = self.head
            self.head = new_node
            
        self._size += 1
    
    def remove(self, value: T) -> bool:
        """Remove the first occurrence of a value from the list."""
        if self.head is None:
            return False
            
        # Special case: removing the head
        if self.head.value == value:
            self.head = self.head.next
            self._size -= 1
            
            # If the list is now empty, update the tail
            if self.head is None:
                self.tail = None
                
            return True
        
        # Search for the value in the rest of the list
        current = self.head
        while current.next is not None:
            if current.next.value == value:
                # Remove the node
                current.next = current.next.next
                self._size -= 1
                
                # If we removed the tail, update it
                if current.next is None:
                    self.tail = current
                    
                return True
            current = current.next
            
        return False
    
    def find(self, value: T) -> Optional[Node[T]]:
        """Find the first node containing the given value."""
        current = self.head
        while current is not None:
            if current.value == value:
                return current
            current = current.next
        return None
    
    def __iter__(self) -> Iterator[T]:
        """Iterate through the values in the list."""
        current = self.head
        while current is not None:
            yield current.value
            current = current.next
    
    def __len__(self) -> int:
        """Get the number of elements in the list."""
        return self._size
    
    def is_empty(self) -> bool:
        """Check if the list is empty."""
        return self.head is None
    
    def to_list(self) -> List[T]:
        """Convert the linked list to a Python list."""
        result = []
        current = self.head
        while current is not None:
            result.append(current.value)
            current = current.next
        return result 