import logging
from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from app.api.routes import router as api_router
from app.services.scheduler import start_scheduler
from app.infrastructure import storage

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Course Risk API",
    description="API for tracking student course risks",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with welcome page."""
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
    """Initialize application on startup."""
    logger.info("Starting up Course Risk API")
    
    # Ensure data directory exists
    data_dir = os.getenv("DATA_DIR", "./data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Start scheduler
    start_scheduler(app)
    
    # Create sample course catalog if it doesn't exist
    if not os.path.exists(os.path.join(data_dir, "course_catalog.json")):
        _create_sample_course_catalog()
    
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down Course Risk API")
    
    # Shutdown scheduler if it exists
    if hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown()
        logger.info("Scheduler shut down")


def _create_sample_course_catalog():
    """Create a sample course catalog for testing."""
    sample_courses = [
        {
            "code": "CS101",
            "title": "Introduction to Computer Science",
            "credit": 3,
            "prereq": []
        },
        {
            "code": "CS102",
            "title": "Data Structures",
            "credit": 4,
            "prereq": ["CS101"]
        },
        {
            "code": "CS201",
            "title": "Algorithms",
            "credit": 4,
            "prereq": ["CS102"]
        },
        {
            "code": "CS301",
            "title": "Database Systems",
            "credit": 3,
            "prereq": ["CS201"]
        },
        {
            "code": "MATH101",
            "title": "Calculus I",
            "credit": 4,
            "prereq": []
        },
        {
            "code": "MATH102",
            "title": "Calculus II",
            "credit": 4,
            "prereq": ["MATH101"]
        }
    ]
    
    storage.save_course_catalog(sample_courses)
    logger.info("Created sample course catalog")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 