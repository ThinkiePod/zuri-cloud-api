# Models
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text

from main import Base

class Device(Base):
    __tablename__ = "devices"
    __table_args__ = {"extend_existing": True}
    
    device_id = Column(String, primary_key=True)
    device_name = Column(String, nullable=False)
    user_id = Column(String, nullable=True)
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=datetime.now(timezone.utc))
    battery_level = Column(Integer, default=100)
    settings = Column(Text)  # JSON
    ip_address = Column(String, nullable=True)
    firmware_version = Column(String, default="1.0.0")
    wifi_provisioned = Column(Boolean, default=False)
    wifi_ssid = Column(String, nullable=True)
    provisioned_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

class Content(Base):
    __tablename__ = "content"
    __table_args__ = {"extend_existing": True}
    
    content_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    type = Column(String, nullable=False)
    age_range_min = Column(Integer, default=3)
    age_range_max = Column(Integer, default=7)
    duration = Column(Integer, nullable=False)  # seconds
    file_url = Column(String, nullable=False)
    thumbnail_url = Column(String, nullable=True)
    file_size = Column(Integer, default=0)
    checksum = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(Text)  # JSON array
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))


class DeviceCommand(Base):
    __tablename__ = "device_commands"
    __table_args__ = {"extend_existing": True}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String, nullable=False)
    command = Column(String, nullable=False)
    params = Column(Text)  # JSON
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    executed_at = Column(DateTime, nullable=True)
    status = Column(String, default="pending")  # pending, sent, completed, failed

class UsageAnalytics(Base):
    __tablename__ = "usage_analytics"
    __table_args__ = {"extend_existing": True}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String, nullable=False)
    content_id = Column(String, nullable=False)
    action = Column(String, nullable=False)  # play, pause, stop, complete
    duration = Column(Integer, default=0)
    session_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))
