from datetime import date, timedelta
from typing import Set, List, Dict, Any

from app.domain.models import Student, Assignment
from app.domain.ds.assignment_heap import AssignmentMinHeap
from app.domain.ds.prereq_graph import PrereqGraph


class RiskEngine:
    """
    Çeşitli faktörlere dayalı öğrenci risk puanı hesaplama motoru.
    """
    
    def __init__(self, storage):
        """
        Risk motorunu depolama bağımlılığı ile başlat.
        
        Args:
            storage: Öğrenci ve ders verilerine erişmek için depolama modülü.
        """
        self.storage = storage
        self._prereq_graph = None
        self._init_prereq_graph()
    
    def _init_prereq_graph(self) -> None:
        """Ders kataloğundan ön koşul grafiğini başlat."""
        courses = self.storage.load_course_catalog()
        self._prereq_graph = PrereqGraph()
        
        for course in courses:
            self._prereq_graph.add_course(course["code"], course.get("prereq", []))
    
    def calculate(self, student: Student) -> float:
        """
        Bir öğrenci için genel risk puanını hesapla.
        
        Risk puanı, çeşitli risk faktörlerinin ağırlıklı toplamıdır:
        - Devamsızlık riski (%25)
        - Ödev riski (%25)
        - Ön koşul riski (%20)
        - GPA riski (%15)
        - Harf notu riski (%15)
        
        Returns:
            0.0 (risk yok) ile 1.0 (en yüksek risk) arasında bir risk puanı.
        """
        # Bireysel risk bileşenlerini hesapla
        absence_risk = self._calculate_absence_risk(student)
        assignment_risk = self._calculate_assignment_risk(student)
        prereq_risk = self._calculate_prereq_risk(student)
        gpa_risk = self._calculate_gpa_risk(student)
        grade_risk = self._calculate_grade_risk(student)
        
        # Her bileşene ağırlık uygula
        weighted_risk = (
            0.25 * absence_risk +
            0.25 * assignment_risk +
            0.20 * prereq_risk +
            0.15 * gpa_risk +
            0.15 * grade_risk
        )
        
        return min(1.0, max(0.0, weighted_risk))
    
    def _calculate_absence_risk(self, student: Student) -> float:
        """
        Öğrenci devamsızlıklarına dayalı riski hesapla.
        
        Her bit bir devamsızlığı temsil eden absence_bits alanını kullanır.
        Risk, devamsızlık sayısı izin verilen maksimuma yaklaştıkça artar.
        """
        # absence_bits içindeki 1 bitlerin sayısını say
        absence_count = bin(student.absence_bits).count('1')
        
        # İzin verilen maksimum devamsızlık (genellikle bir dönemde 14)
        max_absences = 14
        
        # Riski, devamsızlıkların izin verilen maksimuma oranı olarak hesapla
        if max_absences == 0:
            return 0.0
            
        risk = absence_count / max_absences
        
        # Devamsızlıklar limite yaklaştıkça riski vurgulamak için doğrusal olmayan bir ölçeklendirme uygula
        if risk > 0.7:
            # Limit yaklaştıkça riski daha hızlı artır
            risk = 0.7 + (risk - 0.7) * 1.5
            
        return min(1.0, max(0.0, risk))
    
    def _calculate_assignment_risk(self, student: Student) -> float:
        """
        Kaçırılan veya yaklaşan ödevlere dayalı riski hesapla.
        
        Şunları dikkate alır:
        - Kaçırılan ödevlerin oranı
        - Yaklaşan son teslim tarihlerinin yakınlığı
        """
        if not student.assignments:
            return 0.0
            
        # Kaçırılan ödevleri say
        total_assignments = len(student.assignments)
        missed_assignments = sum(1 for a in student.assignments 
                               if not a.done and a.deadline < date.today())
        
        # Kaçırılan ödevlerden riski hesapla (ödev riskinin %50'si)
        missed_risk = missed_assignments / total_assignments if total_assignments > 0 else 0.0
        
        # Yaklaşan son teslim tarihlerinden riski hesapla (ödev riskinin %50'si)
        heap = AssignmentMinHeap.from_assignments(student.assignments)
        upcoming = heap.get_due_soon(days=7)
        
        # Son teslim tarihi riskini, ödevlerin ne kadar yakın olduğuna göre hesapla
        today = date.today()
        deadline_risk = 0.0
        
        for assignment in upcoming:
            if assignment.done:
                continue
                
            days_left = (assignment.deadline - today).days
            # Daha yakın son teslim tarihleri için daha yüksek risk
            if days_left <= 1:
                deadline_risk += 1.0
            elif days_left <= 3:
                deadline_risk += 0.7
            elif days_left <= 5:
                deadline_risk += 0.4
            else:
                deadline_risk += 0.2
        
        # Son teslim tarihi riskini normalize et
        max_deadline_risk = len(upcoming)
        if max_deadline_risk > 0:
            deadline_risk = deadline_risk / max_deadline_risk
        
        # Kaçırılan ve son teslim tarihi risklerini birleştir
        return 0.5 * missed_risk + 0.5 * deadline_risk
    
    def _calculate_prereq_risk(self, student: Student) -> float:
        """
        Ön koşul sorunlarına dayalı riski hesapla.
        
        Öğrencinin ön koşulları tamamlamadan dersler alıp almadığını kontrol eder.
        """
        if not self._prereq_graph:
            return 0.0
            
        # Öğrencinin tamamladığı tüm dersleri al
        completed_courses = set()
        current_courses = set()
        
        for term in student.terms:
            # Her dönem için tamamlanmış dersleri kontrol et
            for course_enrollment in term.courses:
                if course_enrollment.completed:
                    # Sadece başarıyla tamamlanmış dersleri (FF hariç) listeye ekle
                    if not course_enrollment.grade or course_enrollment.grade.upper() != "FF":
                        completed_courses.add(course_enrollment.code)
                else:
                    # Mevcut (tamamlanmamış) dersleri listeye ekle
                    current_courses.add(course_enrollment.code)
        
        # Mevcut dersler için ön koşulları kontrol et
        missing_prereqs = 0
        total_prereqs = 0
        
        for course_code in current_courses:
            prereqs = self._prereq_graph.get_prerequisites(course_code)
            total_prereqs += len(prereqs)
            missing = self._prereq_graph.find_missing_prerequisites(course_code, completed_courses)
            missing_prereqs += len(missing)
        
        # Eksik ön koşullara dayalı riski hesapla
        if total_prereqs == 0:
            return 0.0
            
        return min(1.0, missing_prereqs / total_prereqs)
    
    def _calculate_grade_risk(self, student: Student) -> float:
        """
        Harf notlarına dayalı riski hesapla.
        
        Şunları dikkate alır:
        - FF ile tamamlanan dersler (başarısız)
        - Düşük notlu dersler
        """
        # Notlandırma sistemi: AA=4.0, BA=3.5, BB=3.0, CB=2.5, CC=2.0, DC=1.5, DD=1.0, FF=0.0
        grade_points = {
            "AA": 0.0,  # Risk yok
            "BA": 0.1,
            "BB": 0.2,
            "CB": 0.3,
            "CC": 0.4,
            "DC": 0.6,
            "DD": 0.8,
            "FF": 1.0   # Tam risk
        }
        
        total_completed = 0
        total_risk = 0.0
        
        for term in student.terms:
            for course in term.courses:
                if course.completed and course.grade:
                    total_completed += 1
                    grade = course.grade.upper()
                    total_risk += grade_points.get(grade, 0.5)  # Bilinmeyen notlar için orta risk
        
        if total_completed == 0:
            return 0.0
        
        return total_risk / total_completed
    
    def _calculate_gpa_risk(self, student: Student) -> float:
        """
        GPA'ya dayalı riski hesapla.
        
        Düşük GPA daha yüksek risk gösterir.
        """
        # GPA'nın 4.0 ölçeğinde olduğunu varsay
        # GPA düştükçe risk artar
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