import asyncio
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from db import Base, SessionLocal, engine
from models.v2 import Device
from routers import v1, v2, internal

load_dotenv()

# Create tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(cleanup_offline_devices())
    print("Zuri Combined API started successfully!")
    print("Swagger UI available at: http://localhost:8000/docs")
    print("ReDoc available at: http://localhost:8000/redoc")
    yield

# Background task to mark offline devices
async def cleanup_offline_devices():
    while True:
        db = SessionLocal()
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        
        offline_devices = db.query(Device).filter(
            Device.last_seen < cutoff_time,
            Device.is_online == True
        ).all()
        
        for device in offline_devices:
            device.is_online = False
        
        db.commit()
        db.close()
        
        await asyncio.sleep(300)  # Check every 5 minutes


app = FastAPI(
    title="Zuri Hosted API",
    description="""
## 🧠 Overview
Complete API for managing Zuri devices, content, and WiFi provisioning.

## 🚀 Features
- Device registration and management
- Content library management
- Remote device control
- WiFi provisioning tracking
- Real-time WebSocket communication
- Usage analytics

## 🔐 Authentication
This API currently doesn't require authentication for testing purposes.  
In production, all endpoints should be protected.

## 🧪 Example cURL
```bash
curl -X GET "http://localhost:8000/api/devices" -H "accept: application/json"
    """,
    version="2.0.0",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan
    )

app.mount("/images", StaticFiles(directory="images"), name="images")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include versioned routers
app.include_router(v1.router, prefix="/api/v1")
app.include_router(v2.router, prefix="/api/v2")

app.include_router(internal.router)  # No prefix needed as it's in the router

# Add deprecation warning to all v1 endpoints
@app.middleware("http")
async def add_deprecation_header(request: Request, call_next):
    response = await call_next(request)
    # Only add header for deprecated routes (e.g. starting with /v1)
    if request.url.path.startswith("/v1"):
        response.headers["X-API-Deprecation-Warning"] = "API v1 is deprecated. Please migrate to v2"
    return response

# Redirect root to current version
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/api/v2")  # Redirect to latest version

# Version-specific docs
@app.get("/api/v1/docs", include_in_schema=False)
async def v1_docs():
    # Your existing custom_swagger_ui_html logic but for v1
    pass

@app.get("/api/v2/docs", include_in_schema=False) 
async def v2_docs():
    # Your existing custom_swagger_ui_html logic but for v2
    pass