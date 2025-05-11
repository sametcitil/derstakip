# Ders Takip

Öğrencinin ders, ödev, devamsızlık ve ön koşul verilerini tutup risk puanı üreten REST servisi.

## Kurulum

```bash
# Python kurulumu
pyenv install 3.12.2
pyenv virtualenv 3.12.2 course-risk
pyenv local course-risk

# Bağımlılıklar
pip install poetry
poetry install
```

## Geliştirme

```bash
# Pre-commit hooks kurulumu
pre-commit install

# Uygulamayı çalıştırma
poetry run uvicorn app.main:app --reload
```

## API Endpoints

- `POST /students/`: Yeni öğrenci oluştur
- `GET /students/{id}/risk`: Öğrenci risk puanını hesapla
- `POST /students/{id}/courses`: Öğrenciye kurs ekle
- `DELETE /students/{id}/courses/{code}`: Öğrenciden kurs sil
- `GET /courses/autocomplete`: Kurs adı otomatik tamamlama 