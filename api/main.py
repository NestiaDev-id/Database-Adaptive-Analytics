"""
FastAPI Backend for DB Analyst AI
Sistem Analisis Data Berbasis SQL dengan Multi-LLM Support
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.app.routes import chat, database

# Create FastAPI app
app = FastAPI(
    title="DB Analyst AI API",
    description="Backend API untuk sistem analisis, prediksi, dan rekomendasi data perusahaan",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(database.router, prefix="/api", tags=["Database"])


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "DB Analyst AI API"}


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to DB Analyst AI API",
        "docs": "/docs",
        "health": "/health"
    }
