from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, SubmitField, BooleanField
from wtforms.validators import DataRequired, NumberRange

class AddCourseForm(FlaskForm):
    """Öğrenciye ders ekleme formu."""
    code = StringField("Ders Kodu", validators=[DataRequired()])
    submit = SubmitField("Ekle")


class EditAbsenceForm(FlaskForm):
    """Öğrenci devamsızlık düzenleme formu."""
    absence_bits = IntegerField("Devamsızlık (Bit Değeri)", validators=[NumberRange(min=0)])
    submit = SubmitField("Kaydet")


class AddAssignmentForm(FlaskForm):
    """Öğrenciye ödev ekleme formu."""
    deadline = StringField("Son Tarih (YYYY-MM-DD)", validators=[DataRequired()])
    done = BooleanField("Tamamlandı")
    submit = SubmitField("Ekle")


class CreateStudentForm(FlaskForm):
    """Yeni öğrenci oluşturma formu."""
    name = StringField("Öğrenci Adı", validators=[DataRequired()])
    gpa = StringField("GPA", default="0.0")
    submit = SubmitField("Oluştur") 