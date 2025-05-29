from typing import TypeVar, Generic, Optional, Iterator, List

T = TypeVar('T')


class Node(Generic[T]):
    """Tek yönlü bağlı listede bir düğüm."""
    
    def __init__(self, value: T):
        self.value = value
        self.next: Optional[Node[T]] = None


class LinkedList(Generic[T]):
    """
    Basit bir tek yönlü bağlı liste uygulaması.
    """
    
    def __init__(self):
        self.head: Optional[Node[T]] = None  # Listenin başındaki düğüm
        self.tail: Optional[Node[T]] = None  # Listenin sonundaki düğüm
        self._size = 0  # Liste eleman sayısı
    
    def append(self, value: T) -> None:
        """Listenin sonuna bir değer ekler."""
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
        """Listenin başına bir değer ekler."""
        new_node = Node(value)
        
        if self.head is None:
            self.head = new_node
            self.tail = new_node
        else:
            new_node.next = self.head
            self.head = new_node
            
        self._size += 1
    
    def remove(self, value: T) -> bool:
        """Listeden belirtilen değerin ilk örneğini kaldırır. Başarılıysa True, değilse False döner."""
        if self.head is None:
            return False
            
        # Özel durum: Baş düğümü kaldırma
        if self.head.value == value:
            self.head = self.head.next
            self._size -= 1
            
            # Eğer liste artık boşsa, kuyruğu güncelle
            if self.head is None:
                self.tail = None
                
            return True
        
        # Değeri listenin geri kalanında ara
        current = self.head
        while current.next is not None:
            if current.next.value == value:
                # Düğümü kaldır
                current.next = current.next.next
                self._size -= 1
                
                # Eğer kuyruk düğümünü kaldırdıysak, kuyruğu güncelle
                if current.next is None:
                    self.tail = current
                    
                return True
            current = current.next
            
        return False
    
    def find(self, value: T) -> Optional[Node[T]]:
        """Verilen değeri içeren ilk düğümü bulur. Bulunamazsa None döner."""
        current = self.head
        while current is not None:
            if current.value == value:
                return current
            current = current.next
        return None
    
    def __iter__(self) -> Iterator[T]:
        """Listedeki değerler üzerinde iterasyon yapar."""
        current = self.head
        while current is not None:
            yield current.value
            current = current.next
    
    def __len__(self) -> int:
        """Listedeki eleman sayısını döndürür."""
        return self._size
    
    def is_empty(self) -> bool:
        """Listenin boş olup olmadığını kontrol eder."""
        return self.head is None
    
    def to_list(self) -> List[T]:
        """Bağlı listeyi Python listesine dönüştürür."""
        result = []
        current = self.head
        while current is not None:
            result.append(current.value)
            current = current.next
        return result 