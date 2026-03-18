from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging
from pathlib import Path

from config import settings

# Import routers
from routers.auth import router as auth_router
from routers.invoices import router as invoices_router
from routers.ledger import router as ledger_router
from routers.reports import router as reports_router
from routers.dashboard import router as dashboard_router

# ERP Integration routers
from erp_integration.routers.erp_router import router as erp_router
from erp_integration.routers.webhooks import router as webhooks_router
from erp_integration.routers.metrics import router as metrics_router
from erp_integration.routers.websocket import router as websocket_router

# Rate limiting
from services.rate_limiter import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting CarbonTraceAI server...")
    
    # Create directories
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.REPORTS_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.REPORTS_DIR, "qr_codes"), exist_ok=True)
    
    logger.info("CarbonTraceAI server started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down CarbonTraceAI server...")

app = FastAPI(
    title="CarbonTraceAI",
    description="AI-powered carbon accounting and verification platform for African SMEs",
    version="2.0.0",
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.CORS_ORIGINS.split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for generated reports
reports_path = Path(settings.REPORTS_DIR)
os.makedirs(reports_path, exist_ok=True)
app.mount("/static/reports", StaticFiles(directory=str(reports_path)), name="reports")

# Include routers with /api prefix
app.include_router(auth_router, prefix="/api")
app.include_router(invoices_router, prefix="/api")
app.include_router(ledger_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")

# ERP Integration routers (already have /api prefix)
app.include_router(erp_router)
app.include_router(webhooks_router)
app.include_router(metrics_router)
app.include_router(websocket_router)

@app.get("/api")
async def root():
    return {
        "message": "Welcome to CarbonTraceAI API",
        "version": "2.0.0",
        "features": [
            "AI-Powered Invoice Intelligence",
            "Blockchain-Verified Carbon Ledger",
            "ESG Report Generator (ISSB/TCFD/GRI/CBAM)"
        ],
        "docs": "/docs"
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "CarbonTraceAI"}
