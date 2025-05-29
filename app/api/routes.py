from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Dict, Any, Optional
from datetime import date
import json

from app.domain.models import Student, Term, Course, Assignment, CourseEnrollment
from app.domain.risk import RiskEngine
from app.infrastructure import storage
from app.domain.ds.undo_stack import UndoStack

# Create router
router = APIRouter(tags=["students"])

# In-memory Trie for course autocomplete
course_trie = {}

# In-memory undo stacks for each student
student_undo_stacks: Dict[int, UndoStack[Student]] = {}


def get_risk_engine() -> RiskEngine:
    """Dependency for risk engine."""
    return RiskEngine(storage)


def get_student_undo_stack(student_id: int) -> UndoStack[Student]:
    """Get or create an undo stack for a student."""
    if student_id not in student_undo_stacks:
        student_undo_stacks[student_id] = UndoStack[Student]()
    return student_undo_stacks[student_id]


@router.get("/students/", response_model=List[Dict[str, Any]])
async def list_students() -> List[Dict[str, Any]]:
    """Get a list of all students."""
    students = list(storage.iter_all_students())
    return [student.model_dump() for student in students]


@router.post("/students/", status_code=status.HTTP_201_CREATED)
async def create_student(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new student."""
    # Generate a new student ID
    student_id = storage.next_student_id()
    
    # Create student object with the generated ID
    student_data["id"] = student_id
    
    # Convert assignments if they exist
    if "assignments" in student_data:
        for i, assignment in enumerate(student_data["assignments"]):
            if isinstance(assignment, dict) and "deadline" in assignment:
                # Convert string date to date object
                if isinstance(assignment["deadline"], str):
                    assignment["deadline"] = date.fromisoformat(assignment["deadline"])
    
    student = Student.model_validate(student_data)
    
    # Save to storage
    storage.save_student(student)
    
    # Initialize undo stack for this student
    get_student_undo_stack(student_id).push(student)
    
    return {"id": student_id, "message": "Student created successfully"}


@router.get("/students/{student_id}")
async def get_student(student_id: int) -> Dict[str, Any]:
    """Get student details."""
    student = storage.load_student(student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found"
        )
    
    return student.model_dump()


@router.post("/students/{student_id}")
async def update_student(student_id: int, student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update student details."""
    # Check if student exists
    existing_student = storage.load_student(student_id)
    if existing_student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found"
        )
    
    # Ensure ID is not changed
    student_data["id"] = student_id
    
    # Convert assignments if they exist
    if "assignments" in student_data:
        for i, assignment in enumerate(student_data["assignments"]):
            if isinstance(assignment, dict) and "deadline" in assignment:
                # Convert string date to date object
                if isinstance(assignment["deadline"], str):
                    assignment["deadline"] = date.fromisoformat(assignment["deadline"])
    
    # Update student
    student = Student.model_validate(student_data)
    
    # Save to undo stack
    get_student_undo_stack(student_id).push(student)
    
    # Save to storage
    storage.save_student(student)
    
    return {"id": student_id, "message": "Student updated successfully"}


@router.get("/students/{student_id}/risk")
async def calculate_risk(
    student_id: int, 
    risk_engine: RiskEngine = Depends(get_risk_engine)
) -> Dict[str, Any]:
    """Calculate risk score for a student."""
    student = storage.load_student(student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found"
        )
    
    risk_score = risk_engine.calculate(student)
    
    # Determine risk level based on score
    risk_level = "LOW"
    if risk_score > 0.75:
        risk_level = "HIGH"
    elif risk_score > 0.5:
        risk_level = "MEDIUM"
    
    return {
        "student_id": student_id,
        "name": student.name,
        "risk_score": round(risk_score, 2),
        "risk_level": risk_level
    }


@router.post("/students/{student_id}/courses")
async def add_course(
    student_id: int, 
    course_data: Dict[str, Any],
    risk_engine: RiskEngine = Depends(get_risk_engine)
) -> Dict[str, Any]:
    """Add a course to a student's current term."""
    student = storage.load_student(student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found"
        )
    
    # Get undo stack for this student
    undo_stack = get_student_undo_stack(student_id)
    
    # Save current state to undo stack
    undo_stack.push(student.model_copy(deep=True))
    
    # Get course code and completion status
    course_code = course_data.get("code")
    completed = course_data.get("completed", False)
    grade = course_data.get("grade")
    
    if not course_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course code is required"
        )
    
    # Check if the course exists in catalog
    courses = storage.load_course_catalog()
    course_exists = False
    course_prereqs = []
    
    for course in courses:
        if course.get("code") == course_code:
            course_exists = True
            course_prereqs = course.get("prereq", [])
            break
    
    if not course_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Course {course_code} not found in course catalog"
        )
    
    # Check prerequisites if not completed
    if not completed and course_prereqs:
        # Collect completed courses and failed courses
        completed_courses = set()
        failed_courses = set()
        
        for term in student.terms:
            for course_enrollment in term.courses:
                if course_enrollment.completed:
                    if course_enrollment.grade and course_enrollment.grade.upper() == "FF":
                        failed_courses.add(course_enrollment.code)
                    else:
                        completed_courses.add(course_enrollment.code)
        
        # Check if all prerequisites are completed and not failed
        missing_prereqs = []
        failed_prereqs = []
        
        for prereq in course_prereqs:
            if prereq not in completed_courses:
                missing_prereqs.append(prereq)
            if prereq in failed_courses:
                failed_prereqs.append(prereq)
        
        if missing_prereqs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing prerequisites for {course_code}: {', '.join(missing_prereqs)}"
            )
        
        if failed_prereqs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed prerequisites for {course_code}: {', '.join(failed_prereqs)}. You must pass these courses before taking {course_code}."
            )
    
    # Get or create current term
    current_year = date.today().year
    current_month = date.today().month
    
    # Determine current semester based on month
    if 1 <= current_month <= 6:
        current_semester = 1  # Spring
    elif 7 <= current_month <= 8:
        current_semester = 3  # Summer
    else:
        current_semester = 2  # Fall
    
    # Find current term or create it
    current_term = None
    for term in student.terms:
        if term.year == current_year and term.semester == current_semester:
            current_term = term
            break
    
    if current_term is None:
        current_term = Term(year=current_year, semester=current_semester)
        student.terms.append(current_term)
    
    # Check if course already exists in current term
    course_exists = False
    for course in current_term.courses:
        if course.code == course_code:
            # Update existing course
            course.completed = completed
            if grade is not None:
                course.grade = grade
            course_exists = True
            break
    
    # Add course to current term if not already present
    if not course_exists:
        new_course = CourseEnrollment(
            code=course_code,
            completed=completed,
            grade=grade
        )
        current_term.courses.append(new_course)
    
    # Save updated student
    storage.save_student(student)
    
    return {
        "student_id": student_id,
        "message": f"Course {course_code} added successfully",
        "current_term": current_term.model_dump()
    }


@router.delete("/students/{student_id}/courses/{course_code}")
async def remove_course(
    student_id: int, 
    course_code: str
) -> Dict[str, Any]:
    """Remove a course from a student's current term."""
    student = storage.load_student(student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found"
        )
    
    # Get undo stack for this student
    undo_stack = get_student_undo_stack(student_id)
    
    # Save current state to undo stack
    undo_stack.push(student.model_copy(deep=True))
    
    # Find current term
    current_year = date.today().year
    current_month = date.today().month
    
    # Determine current semester based on month
    if 1 <= current_month <= 6:
        current_semester = 1  # Spring
    elif 7 <= current_month <= 8:
        current_semester = 3  # Summer
    else:
        current_semester = 2  # Fall
    
    # Find current term
    current_term = None
    for term in student.terms:
        if term.year == current_year and term.semester == current_semester:
            current_term = term
            break
    
    if current_term is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Current term not found"
        )
    
    # Find and remove course
    course_found = False
    for i, course in enumerate(current_term.courses):
        if course.code == course_code:
            current_term.courses.pop(i)
            course_found = True
            break
    
    if not course_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course {course_code} not found in current term"
        )
    
    # Save updated student
    storage.save_student(student)
    
    return {
        "student_id": student_id,
        "message": f"Course {course_code} removed successfully",
        "current_term": current_term.model_dump()
    }


@router.post("/students/{student_id}/undo")
async def undo_student_change(student_id: int) -> Dict[str, Any]:
    """Undo the last change to a student."""
    undo_stack = get_student_undo_stack(student_id)
    
    if not undo_stack.can_undo():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No changes to undo"
        )
    
    # Undo the last change
    previous_state = undo_stack.undo()
    if previous_state:
        # Save the previous state
        storage.save_student(previous_state)
        return {
            "student_id": student_id,
            "message": "Change undone successfully"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to undo change"
        )


@router.post("/students/{student_id}/redo")
async def redo_student_change(student_id: int) -> Dict[str, Any]:
    """Redo the last undone change to a student."""
    undo_stack = get_student_undo_stack(student_id)
    
    if not undo_stack.can_redo():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No changes to redo"
        )
    
    # Redo the last undone change
    new_state = undo_stack.redo()
    if new_state:
        # Save the new state
        storage.save_student(new_state)
        return {
            "student_id": student_id,
            "message": "Change redone successfully"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to redo change"
        )


@router.get("/courses/autocomplete")
async def autocomplete_course(
    query: str = Query(..., min_length=1)
) -> List[Dict[str, Any]]:
    """Autocomplete course codes based on prefix."""
    # Load course catalog if trie is empty
    if not course_trie:
        _load_course_trie()
    
    # Boş trie durumunda tekrar yüklemeyi dene
    if not course_trie:
        _load_course_trie()
    
    # Search for matches
    results = _search_trie(query.upper())
    
    # Eğer hala sonuç yoksa ve query tek harf ise, tüm kurları döndür
    if not results and len(query) <= 2:
        courses = storage.load_course_catalog()
        return courses[:10]  # İlk 10 kursu döndür
    
    return results[:10]  # Limit to 10 results


def _load_course_trie() -> None:
    """Load course catalog into trie for autocomplete."""
    global course_trie
    course_trie.clear()  # Var olan verileri temizle
    
    courses = storage.load_course_catalog()
    
    # Kurs kataloğunu kontrol et, boşsa örnek veri oluştur
    if not courses:
        from app.main import _create_sample_course_catalog
        _create_sample_course_catalog()
        courses = storage.load_course_catalog()
    
    for course in courses:
        code = course.get("code", "")
        if code:
            _insert_into_trie(code, course)


def _insert_into_trie(code: str, course: Dict[str, Any]) -> None:
    """Insert a course into the trie."""
    global course_trie
    node = course_trie
    
    for char in code:
        if char not in node:
            node[char] = {}
        node = node[char]
    
    # Mark end of word and store course data
    if "_courses" not in node:
        node["_courses"] = []
    node["_courses"].append(course)


def _search_trie(prefix: str) -> List[Dict[str, Any]]:
    """Search the trie for courses with the given prefix."""
    global course_trie
    node = course_trie
    
    # Navigate to prefix node
    for char in prefix:
        if char not in node:
            return []
        node = node[char]
    
    # Collect all courses under this prefix
    results = []
    _collect_courses(node, results)
    return results


def _collect_courses(node: Dict[str, Any], results: List[Dict[str, Any]]) -> None:
    """Recursively collect all courses under a node."""
    if "_courses" in node:
        results.extend(node["_courses"])
    
    for char, child_node in node.items():
        if char != "_courses":
            _collect_courses(child_node, results)


@router.post("/students/{student_id}/assignments")
async def add_assignment(
    student_id: int, 
    assignment_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Add a new assignment to a student."""
    student = storage.load_student(student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found"
        )
    
    # Get undo stack for this student
    undo_stack = get_student_undo_stack(student_id)
    
    # Save current state to undo stack
    undo_stack.push(student.model_copy(deep=True))
    
    # Validate deadline
    if "deadline" not in assignment_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment deadline is required"
        )
    
    # Convert string date to date object if needed
    if isinstance(assignment_data["deadline"], str):
        try:
            assignment_data["deadline"] = date.fromisoformat(assignment_data["deadline"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    
    # Create new assignment
    new_assignment = Assignment(
        deadline=assignment_data["deadline"],
        done=assignment_data.get("done", False)
    )
    
    # Add to student's assignments
    student.assignments.append(new_assignment)
    
    # Save updated student
    storage.save_student(student)
    
    return {
        "student_id": student_id,
        "message": "Assignment added successfully",
        "assignment": {
            "deadline": new_assignment.deadline.isoformat(),
            "done": new_assignment.done
        }
    }


@router.delete("/students/{student_id}/assignments/{assignment_index}")
async def delete_assignment(
    student_id: int, 
    assignment_index: int
) -> Dict[str, Any]:
    """Delete an assignment by index."""
    student = storage.load_student(student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found"
        )
    
    # Check if assignment index is valid
    if assignment_index < 0 or assignment_index >= len(student.assignments):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment index {assignment_index} not found"
        )
    
    # Get undo stack for this student
    undo_stack = get_student_undo_stack(student_id)
    
    # Save current state to undo stack
    undo_stack.push(student.model_copy(deep=True))
    
    # Remove the assignment
    deleted_assignment = student.assignments.pop(assignment_index)
    
    # Save updated student
    storage.save_student(student)
    
    return {
        "student_id": student_id,
        "message": "Assignment deleted successfully",
        "deleted_assignment": {
            "deadline": deleted_assignment.deadline.isoformat(),
            "done": deleted_assignment.done
        }
    }


@router.patch("/students/{student_id}/assignments/{assignment_index}")
async def update_assignment_status(
    student_id: int, 
    assignment_index: int,
    update_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Update an assignment's completion status."""
    student = storage.load_student(student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found"
        )
    
    # Check if assignment index is valid
    if assignment_index < 0 or assignment_index >= len(student.assignments):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment index {assignment_index} not found"
        )
    
    # Get undo stack for this student
    undo_stack = get_student_undo_stack(student_id)
    
    # Save current state to undo stack
    undo_stack.push(student.model_copy(deep=True))
    
    # Update assignment status
    if "done" in update_data:
        student.assignments[assignment_index].done = bool(update_data["done"])
    
    # Update deadline if provided
    if "deadline" in update_data:
        if isinstance(update_data["deadline"], str):
            try:
                update_data["deadline"] = date.fromisoformat(update_data["deadline"])
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD"
                )
        student.assignments[assignment_index].deadline = update_data["deadline"]
    
    # Save updated student
    storage.save_student(student)
    
    return {
        "student_id": student_id,
        "message": "Assignment updated successfully",
        "updated_assignment": {
            "deadline": student.assignments[assignment_index].deadline.isoformat(),
            "done": student.assignments[assignment_index].done
        }
    }


@router.get("/students/{student_id}/assignments")
async def list_assignments(student_id: int) -> Dict[str, Any]:
    """Get all assignments for a student."""
    student = storage.load_student(student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found"
        )
    
    # Format assignments for response
    assignments = []
    for i, assignment in enumerate(student.assignments):
        assignments.append({
            "index": i,
            "deadline": assignment.deadline.isoformat(),
            "done": assignment.done
        })
    
    # Sort by deadline (earliest first)
    assignments.sort(key=lambda a: a["deadline"])
    
    return {
        "student_id": student_id,
        "name": student.name,
        "assignments": assignments
    } 