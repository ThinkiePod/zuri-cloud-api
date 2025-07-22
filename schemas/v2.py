# Enhanced Pydantic models with examples for Swagger
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DeviceRegister(BaseModel):
    device_id: str = Field(..., example="ZR-ABC123", description="Unique device identifier")
    device_name: str = Field(..., example="Living Room Zuri", description="Human-readable device name")
    ip_address: str = Field(..., example="192.168.1.100", description="Device IP address")
    firmware_version: str = Field(default="1.0.0", example="1.0.0", description="Device firmware version")

class DeviceHeartbeat(BaseModel):
    battery_level: int = Field(..., example=85, description="Battery level percentage (0-100)")
    status: str = Field(default="online", example="online", description="Device status")
    wifi_ssid: Optional[str] = Field(None, example="HomeNetwork", description="Connected WiFi network")

class PlaybackCommand(BaseModel):
    device_id: str = Field(..., example="ZR-ABC123", description="Target device ID")
    content_id: str = Field(..., example="story_001", description="Content to play")
    action: str = Field(..., example="play", description="Action: play, pause, stop")
    volume: Optional[float] = Field(None, example=0.8, description="Volume level (0.0-1.0)")

class DeviceSettings(BaseModel):
    voice_tone: str = Field(default="calm", example="calm", description="Voice tone: calm or playful")
    voice_speed: float = Field(default=1.0, example=1.0, description="Voice speed multiplier")
    volume: float = Field(default=0.8, example=0.8, description="Volume level (0.0-1.0)")
    led_color: str = Field(default="#5E9CF3", example="#5E9CF3", description="LED color hex code")
    led_brightness: float = Field(default=0.7, example=0.7, description="LED brightness (0.0-1.0)")
    led_pattern: str = Field(default="steady", example="steady", description="LED pattern: steady, pulse, rainbow")

class ContentCreate(BaseModel):
    content_id: str = Field(..., example="story_001", description="Unique content identifier")
    title: str = Field(..., example="The Magic Garden", description="Content title")
    type: str = Field(..., example="story", description="Content type: story, phonics, affirmation, routine")
    age_range_min: int = Field(default=3, example=3, description="Minimum age")
    age_range_max: int = Field(default=7, example=7, description="Maximum age")
    duration: int = Field(..., example=300, description="Duration in seconds")
    file_url: str = Field(..., example="https://example.com/content/story_001.mp3", description="Audio file URL")
    thumbnail_url: Optional[str] = Field(None, example="https://example.com/thumbs/story_001.jpg")
    file_size: int = Field(default=0, example=1024000, description="File size in bytes")
    checksum: Optional[str] = Field(None, example="abc123def456", description="SHA256 checksum")
    description: Optional[str] = Field(None, example="A magical story about friendship")
    tags: Optional[List[str]] = Field(default=[], example=["adventure", "friendship"], description="Content tags")
    is_premium: bool = Field(default=False, example=False, description="Premium content flag")

class DeviceCommandRequest(BaseModel):
    command: str = Field(..., example="play", description="Command to execute")
    params: Optional[Dict[str, Any]] = Field(default={}, example={"content_id": "story_001", "volume": 0.8})

class UsageAnalyticsCreate(BaseModel):
    device_id: str = Field(..., example="ZR-ABC123")
    content_id: str = Field(..., example="story_001")
    action: str = Field(..., example="play", description="Action: play, pause, stop, complete")
    duration: int = Field(default=0, example=300, description="Duration in seconds")
    session_id: Optional[str] = Field(None, example="session_123")

class WiFiProvisionUpdate(BaseModel):
    wifi_ssid: str = Field(..., example="HomeNetwork")
    provisioned_at: Optional[datetime] = None
