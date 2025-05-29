from flask import Blueprint, render_template, redirect, url_for, flash, request
from web_app.api import api_get, api_post, api_delete
from web_app.forms import AddCourseForm, EditAbsenceForm, AddAssignmentForm, CreateStudentForm
from datetime import datetime

bp = Blueprint("students", __name__, url_prefix="/students")


@bp.route("/")
def list_students():
    """Öğrenci listesini göster."""
    try:
        # FastAPI'den öğrenci listesini al
        # Not: Bu endpoint'i FastAPI'de oluşturmamız gerekecek
        students = api_get("/students")
        return render_template("index.html", students=students)
    except Exception as e:
        flash(f"Öğrenci listesi alınamadı: {str(e)}", "error")
        return render_template("index.html", students=[])


@bp.route("/create", methods=["GET", "POST"])
def create_student():
    """Yeni öğrenci oluştur."""
    form = CreateStudentForm()
    if form.validate_on_submit():
        try:
            # FastAPI'ye öğrenci oluşturma isteği gönder
            student_data = {
                "name": form.name.data,
                "gpa": float(form.gpa.data) if form.gpa.data else 0.0,
            }
            response = api_post("/students/", json=student_data)
            flash(f"Öğrenci oluşturuldu: {form.name.data}", "success")
            return redirect(url_for(".detail", sid=response["id"]))
        except Exception as e:
            flash(f"Öğrenci oluşturulamadı: {str(e)}", "error")
    
    return render_template("forms/create_student.html", form=form)


@bp.route("/<int:sid>")
def detail(sid):
    """Öğrenci detaylarını göster."""
    try:
        # FastAPI'den öğrenci bilgilerini al
        student = api_get(f"/students/{sid}")
        risk = api_get(f"/students/{sid}/risk")
        
        return render_template(
            "student_detail.html", 
            student=student, 
            risk=risk.get("risk_score", 0.0),
            risk_level=risk.get("risk_level", "LOW")
        )
    except Exception as e:
        flash(f"Öğrenci bilgileri alınamadı: {str(e)}", "error")
        return redirect(url_for(".list_students"))


@bp.route("/<int:sid>/add-course", methods=["GET", "POST"])
def add_course(sid):
    """Öğrenciye ders ekle."""
    form = AddCourseForm()
    
    # Mevcut kurs listesini almak için API'yi çağır
    try:
        # Kurs kataloğunu al
        available_courses = []
        # Boş query parametresi hata verebilir, dolayısıyla düzeltelim
        course_catalog = api_get("/courses/autocomplete?query=Y")
        
        # Form için kurs seçimlerini hazırla
        for course in course_catalog:
            available_courses.append((course["code"], f"{course['code']} - {course.get('title', '')}"))
        
        # Kurslara göre form alanını güncelle
        if available_courses:
            form.code.choices = available_courses
        else:
            # Eğer API'den kurs listesi alınamazsa, sabit bir liste kullan
            form.code.choices = [
                ('YMH101', 'YMH101 - Yazılım Mühendisliği Temelleri I'),
                ('YMH102', 'YMH102 - Programlama I'),
                ('YMH103', 'YMH103 - Veri Yapıları I'),
                ('YMH201', 'YMH201 - Yazılım Mühendisliği Temelleri II'),
                ('YMH202', 'YMH202 - Programlama II'),
                ('YMH203', 'YMH203 - Veri Yapıları II'),
                ('YMH301', 'YMH301 - Yazılım Projesi I'),
                ('YMH302', 'YMH302 - İleri Programlama'),
                ('YMH303', 'YMH303 - Algoritma Analizi')
            ]
    except Exception as e:
        # Kurs listesi alınamazsa varsayılan listeyi kullan
        form.code.choices = [
            ('YMH101', 'YMH101 - Yazılım Mühendisliği Temelleri I'),
            ('YMH102', 'YMH102 - Programlama I'),
            ('YMH103', 'YMH103 - Veri Yapıları I'),
            ('YMH201', 'YMH201 - Yazılım Mühendisliği Temelleri II'),
            ('YMH202', 'YMH202 - Programlama II'),
            ('YMH203', 'YMH203 - Veri Yapıları II'),
            ('YMH301', 'YMH301 - Yazılım Projesi I'),
            ('YMH302', 'YMH302 - İleri Programlama'),
            ('YMH303', 'YMH303 - Algoritma Analizi')
        ]
        print(f"Ders listesi alınamadı: {e}")
    
    if form.validate_on_submit():
        try:
            # FastAPI'ye ders ekleme isteği gönder
            api_post(f"/students/{sid}/courses", json={
                "code": form.code.data,
                "completed": form.completed.data,
                "grade": form.grade.data if form.grade.data else None
            })
            flash(f"Ders eklendi: {form.code.data}", "success")
            return redirect(url_for(".detail", sid=sid))
        except Exception as e:
            error_msg = str(e)
            # API'den gelen hata mesajlarını daha kullanıcı dostu hale getir
            if "detail" in error_msg:
                try:
                    import json
                    error_data = json.loads(error_msg)
                    if "detail" in error_data:
                        error_msg = error_data["detail"]
                except:
                    pass
            
            # Ön koşul hatalarını kontrol et
            if "Missing prerequisites" in error_msg or "Failed prerequisites" in error_msg:
                flash(f"Ön koşul sorunu: {error_msg}", "error")
            else:
                flash(f"Ders eklenemedi: {error_msg}", "error")
    
    return render_template("forms/add_course.html", form=form, student_id=sid)


@bp.route("/<int:sid>/remove-course/<string:code>")
def remove_course(sid, code):
    """Öğrenciden ders sil."""
    try:
        # FastAPI'ye ders silme isteği gönder
        api_delete(f"/students/{sid}/courses/{code}")
        flash(f"Ders silindi: {code}", "success")
    except Exception as e:
        flash(f"Ders silinemedi: {str(e)}", "error")
    
    return redirect(url_for(".detail", sid=sid))


@bp.route("/<int:sid>/edit-absence", methods=["GET", "POST"])
def edit_absence(sid):
    """Öğrenci devamsızlık bilgisini düzenle."""
    form = EditAbsenceForm()
    
    # Mevcut öğrenci bilgilerini al
    try:
        student = api_get(f"/students/{sid}")
        
        if request.method == "GET":
            form.absence_bits.data = student.get("absence_bits", 0)
        
        if form.validate_on_submit():
            # Öğrenci bilgilerini güncelle
            student["absence_bits"] = form.absence_bits.data
            api_post(f"/students/{sid}", json=student)
            flash("Devamsızlık bilgisi güncellendi", "success")
            return redirect(url_for(".detail", sid=sid))
            
    except Exception as e:
        flash(f"Hata: {str(e)}", "error")
        return redirect(url_for(".detail", sid=sid))
    
    return render_template("forms/edit_absence.html", form=form, student=student)


@bp.route("/<int:sid>/add-assignment", methods=["GET", "POST"])
def add_assignment(sid):
    """Öğrenciye ödev ekle."""
    form = AddAssignmentForm()
    
    if form.validate_on_submit():
        try:
            # Öğrenci bilgilerini al
            student = api_get(f"/students/{sid}")
            
            # Yeni ödevi ekle
            new_assignment = {
                "deadline": form.deadline.data,
                "done": form.done.data
            }
            
            if "assignments" not in student:
                student["assignments"] = []
            
            student["assignments"].append(new_assignment)
            
            # Öğrenci bilgilerini güncelle
            api_post(f"/students/{sid}", json=student)
            
            flash("Ödev eklendi", "success")
            return redirect(url_for(".detail", sid=sid))
        except Exception as e:
            flash(f"Ödev eklenemedi: {str(e)}", "error")
    
    return render_template("forms/add_assignment.html", form=form, student_id=sid) 