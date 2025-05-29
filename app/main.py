import logging
from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from app.api.routes import router as api_router
from app.services.scheduler import start_scheduler
from app.infrastructure import storage

# .env dosyasından çevre değişkenlerini yükle
load_dotenv()

# Loglama yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# FastAPI uygulamasını oluştur
app = FastAPI(
    title="Course Risk API",
    description="API for tracking student course risks",
    version="0.1.0",
)

# CORS middleware ekle - farklı kaynaklardan gelen isteklere izin ver
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Geliştirme için; üretimde kısıtlanmalıdır
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API rotalarını dahil et
app.include_router(api_router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Ana sayfa karşılama sayfası."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ders Takip API</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }
            h1 {
                color: #333;
                border-bottom: 1px solid #ddd;
                padding-bottom: 10px;
            }
            .endpoints {
                background-color: #f5f5f5;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }
            a {
                color: #0066cc;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <h1>Ders Takip API</h1>
        <p>Öğrencinin ders, ödev, devamsızlık ve ön koşul verilerini tutup risk puanı üreten REST servisi.</p>
        
        <div class="endpoints">
            <h2>API Dökümantasyonu</h2>
            <p>API'yi test etmek için <a href="/docs">Swagger UI</a> veya <a href="/redoc">ReDoc</a> kullanabilirsiniz.</p>
            
            <h2>Temel Endpointler</h2>
            <ul>
                <li><code>POST /api/students/</code> - Yeni öğrenci oluştur</li>
                <li><code>GET /api/students/{id}/risk</code> - Öğrenci risk puanını hesapla</li>
                <li><code>POST /api/students/{id}/courses</code> - Öğrenciye kurs ekle</li>
                <li><code>DELETE /api/students/{id}/courses/{code}</code> - Öğrenciden kurs sil</li>
                <li><code>GET /api/courses/autocomplete</code> - Kurs adı otomatik tamamlama</li>
            </ul>
        </div>
    </body>
    </html>
    """


@app.on_event("startup")
async def startup_event():
    """Uygulama başlangıcında çalışan fonksiyon."""
    logger.info("Starting up Course Risk API")
    
    # Veri dizininin varlığını kontrol et, yoksa oluştur
    data_dir = os.getenv("DATA_DIR", "./data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Zamanlayıcıyı başlat (gece risk hesaplamaları için)
    start_scheduler(app)
    
    # Örnek ders kataloğunu oluştur (eğer yoksa)
    if not os.path.exists(os.path.join(data_dir, "course_catalog.json")):
        _create_sample_course_catalog()
    
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Uygulama kapatılırken kaynakları temizle."""
    logger.info("Shutting down Course Risk API")
    
    # Zamanlayıcıyı kapat (eğer varsa)
    if hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown()
        logger.info("Scheduler shut down")


def _create_sample_course_catalog():
    """Test için örnek ders kataloğu oluştur."""
    sample_courses = [
        {
            "code": "YMH101",
            "title": "Yazılım Mühendisliği Temelleri I",
            "credit": 3,
            "prereq": []
        },
        {
            "code": "YMH102",
            "title": "Programlama I",
            "credit": 4,
            "prereq": []
        },
        {
            "code": "YMH103",
            "title": "Veri Yapıları I",
            "credit": 3,
            "prereq": []
        },
        {
            "code": "YMH201",
            "title": "Yazılım Mühendisliği Temelleri II",
            "credit": 3,
            "prereq": ["YMH101"]
        },
        {
            "code": "YMH202",
            "title": "Programlama II",
            "credit": 4,
            "prereq": ["YMH102"]
        },
        {
            "code": "YMH203",
            "title": "Veri Yapıları II",
            "credit": 3,
            "prereq": ["YMH103"]
        },
        {
            "code": "YMH301",
            "title": "Yazılım Projesi I",
            "credit": 4,
            "prereq": ["YMH201"]
        },
        {
            "code": "YMH302",
            "title": "İleri Programlama",
            "credit": 4,
            "prereq": ["YMH202"]
        },
        {
            "code": "YMH303",
            "title": "Algoritma Analizi",
            "credit": 3,
            "prereq": ["YMH203"]
        }
    ]
    
    storage.save_course_catalog(sample_courses)
    logger.info("Created sample course catalog")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 