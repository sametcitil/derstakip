import heapq
from datetime import date, datetime
from typing import List, Tuple, Optional

from app.domain.models import Assignment


class AssignmentMinHeap:
    """
    Ödevler için son teslim tarihine göre sıralanmış bir min-heap.
    Temel implementasyon olarak Python'un heapq modülünü kullanır.
    """
    
    def __init__(self):
        # Ödevleri tutacak boş heap listesi oluştur
        self._heap = []
    
    def add(self, assignment: Assignment) -> None:
        """Heap'e yeni bir ödev ekle."""
        # Tarihi karşılaştırılabilir formata çevir ve anahtar olarak kullan
        deadline_key = assignment.deadline.toordinal()
        heapq.heappush(self._heap, (deadline_key, assignment))
    
    def peek(self) -> Optional[Assignment]:
        """En yakın teslim tarihli ödevi silmeden getir."""
        if not self._heap:
            return None
        return self._heap[0][1]
    
    def pop(self) -> Optional[Assignment]:
        """En yakın teslim tarihli ödevi sil ve döndür."""
        if not self._heap:
            return None
        return heapq.heappop(self._heap)[1]
    
    def is_empty(self) -> bool:
        """Heap'in boş olup olmadığını kontrol et."""
        return len(self._heap) == 0
    
    def size(self) -> int:
        """Heap'teki ödev sayısını döndür."""
        return len(self._heap)
    
    def get_all_sorted(self) -> List[Assignment]:
        """Tüm ödevleri teslim tarihine göre sıralı olarak getir."""
        # Orijinal heap'i değiştirmemek için kopya oluştur
        heap_copy = self._heap.copy()
        result = []
        
        while heap_copy:
            result.append(heapq.heappop(heap_copy)[1])
            
        return result
    
    def get_due_soon(self, days: int = 7) -> List[Assignment]:
        """Belirtilen gün sayısı içinde teslim edilmesi gereken ödevleri getir."""
        today = date.today()
        cutoff = today.toordinal() + days
        
        result = []
        for deadline_key, assignment in self._heap:
            if deadline_key <= cutoff:
                result.append(assignment)
        
        # Teslim tarihine göre sırala
        result.sort(key=lambda a: a.deadline)
        return result
    
    @classmethod
    def from_assignments(cls, assignments: List[Assignment]) -> 'AssignmentMinHeap':
        """Ödev listesinden yeni bir heap oluştur."""
        heap = cls()
        for assignment in assignments:
            heap.add(assignment)
        return heap 