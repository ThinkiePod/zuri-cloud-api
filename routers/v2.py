from fastapi import APIRouter
from fastapi import HTTPException, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import  Session
from datetime import datetime, timedelta, timezone
import json
from typing import Dict, List, Optional

from db import SessionLocal, get_db
from models.v2 import Content, Device, DeviceCommand, UsageAnalytics
from schemas.v2 import ContentCreate, DeviceCommandRequest, DeviceHeartbeat, DeviceRegister, DeviceSettings, PlaybackCommand, UsageAnalyticsCreate, WiFiProvisionUpdate
from utils.helper import add_custom_color, load_navbar_and_footer_html


router = APIRouter(
    tags=["API v2 - Current"],
    responses={404: {"description": "Not found"}},
)

# Global state for WebSocket connections
device_connections: Dict[str, WebSocket] = {}
mobile_connections: List[WebSocket] = []

templates = Jinja2Templates(directory="templates")

# Device Management Endpoints
@router.post("/devices/register", tags=["Device Management"], summary="Register a new device")
async def register_device_v2(device_data: DeviceRegister, db: Session = Depends(get_db)):
    """Register a device with the hosted API"""
    device = db.query(Device).filter(Device.device_id == device_data.device_id).first()
    
    if device:
        # Update existing device
        device.device_name = device_data.device_name
        device.ip_address = device_data.ip_address
        device.firmware_version = device_data.firmware_version
        device.is_online = True
        device.last_seen = datetime.now(timezone.utc)
    else:
        # Create new device
        device = Device(
            device_id=device_data.device_id,
            device_name=device_data.device_name,
            ip_address=device_data.ip_address,
            firmware_version=device_data.firmware_version,
            is_online=True,
            last_seen=datetime.now(timezone.utc)
        )
        db.add(device)
    
    db.commit()
    return {"status": "registered", "device_id": device.device_id}

@router.post("/devices/{device_id}/heartbeat", tags=["Device Management"], summary="Device heartbeat")
async def device_heartbeat_v2(device_id: str, heartbeat: DeviceHeartbeat, db: Session = Depends(get_db)):
    """Receive heartbeat from device"""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device.battery_level = heartbeat.battery_level
    device.last_seen = datetime.now(timezone.utc)
    device.is_online = True
    
    if heartbeat.wifi_ssid:
        device.wifi_ssid = heartbeat.wifi_ssid
        if not device.wifi_provisioned:
            device.wifi_provisioned = True
            device.provisioned_at = datetime.now(timezone.utc)
    
    db.commit()
    
    # Send pending commands to device
    pending_commands = db.query(DeviceCommand).filter(
        DeviceCommand.device_id == device_id,
        DeviceCommand.status == "pending"
    ).all()
    
    commands_to_send = []
    for cmd in pending_commands:
        commands_to_send.append({
            "id": cmd.id,
            "command": cmd.command,
            "params": json.loads(cmd.params) if cmd.params else {}
        })
        cmd.status = "sent"
    
    db.commit()
    
    return {"status": "ok", "commands": commands_to_send}

@router.get("/devices", tags=["Device Management"], summary="List all devices")
async def get_devices_v2(user_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all devices (optionally filtered by user)"""
    query = db.query(Device)
    if user_id:
        query = query.filter(Device.user_id == user_id)
    
    devices = query.all()
    
    return [
        {
            "device_id": device.device_id,
            "device_name": device.device_name,
            "user_id": device.user_id,
            "is_online": device.is_online,
            "last_seen": device.last_seen,
            "battery_level": device.battery_level,
            "ip_address": device.ip_address,
            "firmware_version": device.firmware_version,
            "wifi_provisioned": device.wifi_provisioned,
            "wifi_ssid": device.wifi_ssid,
            "settings": json.loads(device.settings) if device.settings else {},
            "created_at": device.created_at
        }
        for device in devices
    ]

@router.post("/devices/{device_id}/pair", tags=["Device Management"], summary="Pair device with user")
async def pair_device_v2(device_id: str, user_data: dict, db: Session = Depends(get_db)):
    """Pair device with user"""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device.user_id = user_data.get("user_id")
    db.commit()
    
    return {"status": "paired", "device_id": device_id}

@router.patch("/devices/{device_id}/wifi", tags=["Device Management"], summary="Update WiFi provisioning status")
async def update_wifi_provisioning_v2(
    device_id: str,
    wifi_data: WiFiProvisionUpdate,
    db: Session = Depends(get_db)
):
    """Update device WiFi provisioning status."""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device.wifi_provisioned = True
    device.wifi_ssid = wifi_data.wifi_ssid
    device.provisioned_at = wifi_data.provisioned_at or datetime.utcnow()
    
    db.commit()
    
    return {"status": "updated", "device_id": device_id}

# Content Management
@router.get("/content/library", tags=["Content Management"], summary="Get content library")
async def get_content_library_v2(
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    age_min: Optional[int] = Query(None, description="Minimum age filter"),
    age_max: Optional[int] = Query(None, description="Maximum age filter"),
    premium_only: Optional[bool] = Query(None, description="Show premium content only"),
    db: Session = Depends(get_db)
):
    """Get content library"""
    query = db.query(Content)
    
    if content_type:
        query = query.filter(Content.type == content_type)
    
    if age_min:
        query = query.filter(Content.age_range_max >= age_min)
    
    if age_max:
        query = query.filter(Content.age_range_min <= age_max)
    
    if premium_only is not None:
        query = query.filter(Content.is_premium == premium_only)
    
    content_items = query.all()
    
    return [
        {
            "content_id": item.content_id,
            "title": item.title,
            "type": item.type,
            "age_range": f"{item.age_range_min}-{item.age_range_max}",
            "duration": item.duration,
            "file_url": item.file_url,
            "thumbnail_url": item.thumbnail_url,
            "file_size": item.file_size,
            "checksum": item.checksum,
            "description": item.description,
            "tags": json.loads(item.tags) if item.tags else [],
            "is_premium": item.is_premium,
            "created_at": item.created_at
        }
        for item in content_items
    ]

@router.post("/content/library", tags=["Content Management"], summary="Add content to library")
async def add_content_v2(content_data: ContentCreate, db: Session = Depends(get_db)):
    """Add content to library"""
    # Check if content already exists
    existing = db.query(Content).filter(Content.content_id == content_data.content_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Content ID already exists")
    
    content = Content(
        content_id=content_data.content_id,
        title=content_data.title,
        type=content_data.type,
        age_range_min=content_data.age_range_min,
        age_range_max=content_data.age_range_max,
        duration=content_data.duration,
        file_url=content_data.file_url,
        thumbnail_url=content_data.thumbnail_url,
        file_size=content_data.file_size,
        checksum=content_data.checksum,
        description=content_data.description,
        tags=json.dumps(content_data.tags),
        is_premium=content_data.is_premium
    )
    
    db.add(content)
    db.commit()
    
    return {"status": "added", "content_id": content.content_id}

@router.delete("/content/library/{content_id}", tags=["Content Management"], summary="Delete content")
async def delete_content_v2(content_id: str, db: Session = Depends(get_db)):
    """Delete content from library."""
    content = db.query(Content).filter(Content.content_id == content_id).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    db.delete(content)
    db.commit()
    
    return {"status": "deleted", "content_id": content_id}

# Device Control
@router.post("/devices/{device_id}/command", tags=["Device Control"], summary="Send command to device")
async def send_device_command_v2(
    device_id: str, 
    command_data: DeviceCommandRequest, 
    db: Session = Depends(get_db)
):
    """Send a command to a specific device."""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Create command
    command = DeviceCommand(
        device_id=device_id,
        command=command_data.command,
        params=json.dumps(command_data.params)
    )
    
    db.add(command)
    db.commit()
    
    # Try to send immediately via WebSocket if device is connected
    if device_id in device_connections:
        try:
            await device_connections[device_id].send_text(json.dumps({
                "id": command.id,
                "command": command.command,
                "params": command_data.params
            }))
            command.status = "sent"
            db.commit()
        except:
            pass  # Will be sent on next heartbeat
    
    return {"status": "queued", "command_id": command.id}

@router.post("/playback/play", tags=["Device Control"], summary="Play content on device")
async def play_content_v2(playback: PlaybackCommand, db: Session = Depends(get_db)):
    """Play specific content on a device."""
    return await send_device_command_v2(
        playback.device_id,
        DeviceCommandRequest(
            command="play",
            params={
                "content_id": playback.content_id,
                "volume": playback.volume
            }
        ),
        db
    )

@router.post("/playback/stop", tags=["Device Control"], summary="Stop playback")
async def stop_playback_v2(
    device_id: str = Query(..., description="Device ID to stop playback"),
    db: Session = Depends(get_db)
):
    """Stop playback on a device."""
    return await send_device_command_v2(
        device_id,
        DeviceCommandRequest(command="stop"),
        db
    )

@router.post("/devices/{device_id}/settings", tags=["Device Control"], summary="Update device settings")
async def update_device_settings_v2(
    device_id: str, 
    settings: DeviceSettings, 
    db: Session = Depends(get_db)
):
    """Update device settings."""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device.settings = settings.json()
    db.commit()
    
    # Send settings update command
    return await send_device_command_v2(
        device_id,
        DeviceCommandRequest(
            command="update_settings",
            params=settings.model_dump()
        ),
        db
    )

# Analytics
@router.post("/analytics/usage", tags=["Analytics"], summary="Log usage analytics")
async def log_usage_analytics_v2(
    analytics_data: UsageAnalyticsCreate, 
    db: Session = Depends(get_db)
):
    """Log device usage analytics."""
    analytics = UsageAnalytics(
        device_id=analytics_data.device_id,
        content_id=analytics_data.content_id,
        action=analytics_data.action,
        duration=analytics_data.duration,
        session_id=analytics_data.session_id
    )
    
    db.add(analytics)
    db.commit()
    
    return {"status": "logged", "timestamp": analytics.timestamp}

@router.get("/analytics/usage/{device_id}", tags=["Analytics"], summary="Get device usage analytics")
async def get_usage_analytics(
    device_id: str,
    days: int = Query(7, description="Number of days to retrieve"),
    db: Session = Depends(get_db)
):
    """Get usage analytics for a specific device."""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    analytics = db.query(UsageAnalytics).filter(
        UsageAnalytics.device_id == device_id,
        UsageAnalytics.timestamp >= start_date
    ).all()
    
    return [
        {
            "id": a.id,
            "content_id": a.content_id,
            "action": a.action,
            "duration": a.duration,
            "session_id": a.session_id,
            "timestamp": a.timestamp
        }
        for a in analytics
    ]

# WebSocket endpoints
@router.websocket("/ws/device/{device_id}")
async def device_websocket_v2(websocket: WebSocket, device_id: str):
    """WebSocket connection for devices."""
    await websocket.accept()
    device_connections[device_id] = websocket
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle device responses
            if message.get("type") == "command_result":
                # Update command status in database
                db = SessionLocal()
                command = db.query(DeviceCommand).filter(
                    DeviceCommand.id == message.get("command_id")
                ).first()
                if command:
                    command.status = "completed" if message.get("success") else "failed"
                    command.executed_at = datetime.utcnow()
                    db.commit()
                db.close()
                
    except WebSocketDisconnect:
        if device_id in device_connections:
            del device_connections[device_id]

@router.websocket("/ws/mobile")
async def mobile_websocket_v2(websocket: WebSocket):
    """WebSocket connection for mobile apps."""
    await websocket.accept()
    mobile_connections.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            # Handle mobile app messages if needed
            
    except WebSocketDisconnect:
        mobile_connections.remove(websocket)
        
# System endpoints
@router.get("/health", tags=["System"], summary="Health check")
async def health_check_v2():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc),
        "version": "2.0.0"
    }

@router.get("/stats", tags=["System"], summary="System statistics")
async def get_system_stats_v2(db: Session = Depends(get_db)):
    """Get system statistics."""
    total_devices = db.query(Device).count()
    online_devices = db.query(Device).filter(Device.is_online == True).count()
    provisioned_devices = db.query(Device).filter(Device.wifi_provisioned == True).count()
    total_content = db.query(Content).count()
    
    return {
        "devices": {
            "total": total_devices,
            "online": online_devices,
            "offline": total_devices - online_devices,
            "provisioned": provisioned_devices,
            "unprovisioned": total_devices - provisioned_devices
        },
        "content": {
            "total": total_content
        },
        "connections": {
            "device_websockets": len(device_connections),
            "mobile_websockets": len(mobile_connections)
        }
    }


@router.get("/", response_class=HTMLResponse, tags=["System"], summary="API Documentation Home", include_in_schema=False)
async def home_page_v2(request: Request):
    """Home page with API documentation and navigation."""
    navbar_html, footer_html = load_navbar_and_footer_html()
    return templates.TemplateResponse("home.html", {
        "request": request,
        "navbar_html": navbar_html,
        "footer_html": footer_html
    })

# Custom docs endpoints
@router.get("/docs", response_class=HTMLResponse, include_in_schema=False)
async def custom_swagger_ui_html_v2(request: Request):
    navbar_html, footer_html = load_navbar_and_footer_html()
    custom_css = add_custom_color("#f4edf8")
    
    return HTMLResponse(
        get_swagger_ui_html(
        openapi_url=request.app.openapi_url,
        title=request.app.title + " - Swagger UI",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    ).body.decode().replace(
        "<body>", 
        f"<body>{navbar_html}{custom_css}"
    ).replace(
            "</body>",
            f"{footer_html}</body>"
        )
    )
    
@router.get("/redoc", response_class=HTMLResponse, include_in_schema=False)
async def custom_redoc_html_v2(request: Request):
    navbar_html, footer_html = load_navbar_and_footer_html()
    custom_css = add_custom_color("#f4edf8")
    
    return HTMLResponse(
        get_redoc_html(
        openapi_url=request.app.openapi_url,
        title=request.app.title + " - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.2/bundles/redoc.standalone.js",
    ).body.decode().replace(
        "<body>", 
        f"<body>{navbar_html}{custom_css}"
    ).replace(
            "</body>",
            f"{footer_html}</body>"
        ))
