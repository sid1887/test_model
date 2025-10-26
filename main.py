"""
Cumpair: Open-Source AI Product Analysis & Price Comparison System
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.api.routes import analysis, analysis_new, comparison, health, price_comparison, metrics, seed, user, retailers, ai, health_services
from app.api.routes import alerts, smart_lists  # New feature routes
from app.api.routes import analytics_features  # Analytics & forecasting
from app.core.monitoring import setup_monitoring
from app.core.middleware import setup_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application lifecycle"""
    # Initialize database
    await init_db()

    # Initialize AI models
    try:
        from app.services.ai_models import ModelManager, ProductAnalyzer
        print("ðŸ¤– Initializing AI models...")

        # Create global AI instances
        app.state.model_manager = ModelManager()
        success = await app.state.model_manager.initialize_models()

        if success:
            app.state.product_analyzer = ProductAnalyzer(app.state.model_manager)
            print("âœ… AI models initialized successfully!")
        else:
            print("âš ï¸ AI models failed to initialize - some features may be limited")
            app.state.model_manager = None
            app.state.product_analyzer = None

    except Exception as e:
        print(f"âŒ AI model initialization error: {e}")
        app.state.model_manager = None
        app.state.product_analyzer = None

    # Initialize CLIP service
    try:
        from app.services.clip_search import clip_service
        await clip_service.initialize()
    except Exception as e:
        print(f"Warning: Could not initialize CLIP service: {e}")
    
    # Initialize HuggingFace connector
    try:
        from app.services.huggingface_connector import get_hf_connector
        hf = get_hf_connector()
        print(f"🤗 HuggingFace connector initialized (configured: {hf.is_configured()})")
    except Exception as e:
        print(f"Warning: Could not initialize HF connector: {e}")
    
    # Initialize Voice STT service
    try:
        from app.services.voice_stt import get_stt_service
        stt = await get_stt_service()
        print(f"🎤 Voice STT service initialized (provider: {stt.provider})")
    except Exception as e:
        print(f"Warning: Could not initialize Voice STT: {e}")
    
    # Initialize Image Processor
    try:
        from app.services.image_processor import get_image_processor
        processor = await get_image_processor()
        print(f"🖼️  Image Processor initialized")
    except Exception as e:
        print(f"Warning: Could not initialize Image Processor: {e}")

    yield

    # Cleanup if needed
    pass

# Create FastAPI app
app = FastAPI(
    title="Cumpair",
    description="Open-Source AI Product Analysis & Price Comparison System",
    version="1.0.0",
    lifespan=lifespan
)


# Setup monitoring
setup_monitoring(app)

# Setup security and error handling middleware
setup_middleware(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(health_services.router, tags=["health-services"])
app.include_router(metrics.router, tags=["monitoring"])
app.include_router(seed.router, tags=["seed"])
app.include_router(user.router, tags=["user"])
app.include_router(retailers.router, tags=["retailers"])
app.include_router(ai.router, tags=["ai"])
app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])
app.include_router(analysis_new.router, prefix="/api/v1", tags=["analysis-ai"])
app.include_router(comparison.router, prefix="/api/v1", tags=["comparison"])
app.include_router(price_comparison.router, tags=["price-comparison"])

# Include new feature routes
app.include_router(alerts.router, tags=["price-alerts"])
app.include_router(smart_lists.router, tags=["smart-lists"])
app.include_router(analytics_features.router, tags=["analytics-features"])

# Include analytics router for enhanced data pipelines and pricing analytics
try:
    from app.api.routes.analytics import router as analytics_router
    app.include_router(analytics_router, tags=["analytics"])
    print("âœ… Analytics routes loaded successfully")
except Exception as e:
    print(f"⚠️ Failed to load analytics routes: {e}")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with React-based UI"""
    try:
        # Serve the React frontend
        with open("app/static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # Fallback to basic HTML if React frontend not found
        return """
        <html>
            <head>
                <title>Cumpair - Product Analysis & Price Comparison</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                    .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                    .btn { background: #007bff; color: white; border: none; padding: 12px 24px; cursor: pointer; border-radius: 5px; font-size: 16px; }
                    .btn:hover { background: #0056b3; }
                    .alert { padding: 15px; margin: 20px 0; border-radius: 5px; background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>ðŸ” Cumpair</h1>
                    <p>AI-Powered Product Analysis & Price Comparison System</p>

                    <div class="alert">
                        <strong>Welcome!</strong> The enhanced React frontend is not available.
                        Please use the API endpoints directly or check the setup.
                    </div>

                    <h3>Available API Endpoints:</h3>
                    <ul>
                        <li><a href="/docs">ðŸ“š Interactive API Documentation (Swagger)</a></li>
                        <li><a href="/api/v1/health">ðŸ’š Health Check</a></li>
                        <li><strong>POST /api/v1/real-time-search</strong> - Real-time price search</li>
                        <li><strong>POST /api/v1/search-by-image</strong> - CLIP-based image search</li>
                        <li><strong>POST /api/v1/hybrid-search</strong> - Combined text + image search</li>
                        <li><strong>POST /api/v1/analyze</strong> - Upload image for AI analysis</li>
                    </ul>

                    <h3>Quick Test:</h3>
                    <p>Try a simple text search:</p>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; font-family: monospace;">
curl -X POST "http://localhost:8000/api/v1/real-time-search" \\<br>
     -H "Content-Type: application/json" \\<br>
     -d '{"query": "iPhone 15", "sites": ["amazon", "walmart", "ebay"]}'
                    </div>
                </div>
            </body>
        </html>
        """

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=settings.debug
    )
