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
- `GET /students/{id}/assignments`: Öğrencinin tüm ödevlerini listele
- `POST /students/{id}/assignments`: Öğrenciye yeni ödev ekle
- `DELETE /students/{id}/assignments/{index}`: Öğrencinin belirli bir ödevini sil
- `PATCH /students/{id}/assignments/{index}`: Öğrencinin belirli bir ödevini güncelle (tamamlandı/tamamlanmadı)

## Risk Hesaplama

Risk puanı beş ana bileşenden oluşur:

1. **Devamsızlık Riski (25%)**: Öğrencinin kaç derse gelmediğinin bir ölçüsü
2. **Ödev Riski (25%)**: Kaçırılan ödevler ve yaklaşan teslim tarihleri
3. **Ön Koşul Riski (20%)**: Öğrencinin, ön koşulları tamamlamadan almaya çalıştığı dersler
4. **GPA Riski (15%)**: Öğrencinin genel not ortalamasına dayalı risk
5. **Harf Notu Riski (15%)**: Öğrencinin aldığı derslerin harf notlarına (AA-FF) dayalı risk

Detaylı formül için bkz. [Risk Formülü](docs/risk_formula.txt)

## Çalıştırma

```bash
python -m uvicorn app.main:app --reload
# veya
python run.py