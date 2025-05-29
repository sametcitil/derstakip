from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, SubmitField, BooleanField
from wtforms.validators import DataRequired, NumberRange, Optional

class AddCourseForm(FlaskForm):
    """Öğrenciye ders ekleme formu."""
    code = SelectField("Ders Kodu", validators=[DataRequired()], choices=[])
    completed = BooleanField("Tamamlandı")
    grade = SelectField("Not", choices=[
        ('', 'Not Seçiniz'),
        ('AA', 'AA (4.0)'),
        ('BA', 'BA (3.5)'),
        ('BB', 'BB (3.0)'),
        ('CB', 'CB (2.5)'),
        ('CC', 'CC (2.0)'),
        ('DC', 'DC (1.5)'),
        ('DD', 'DD (1.0)'),
        ('FF', 'FF (0.0 - Başarısız)')
    ], validators=[Optional()])
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