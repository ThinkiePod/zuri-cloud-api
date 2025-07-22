# Zuri Device Management API

A comprehensive FastAPI-based system for managing Zuri devices with versioned API endpoints, real-time WebSocket communication, and device client integration.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Mobile Apps   │    │   Hosted API     │    │  Device Client  │
│                 │    │                  │    │  (Raspberry Pi) │
│ • React Native  │◄──►│ • FastAPI        │◄──►│ • Local Server  │
│ • Authentication│    │ • WebSockets     │    │ • Content Sync  │
│ • Device Control│    │ • SQLite/Postgres│    │ • Audio Control │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Features

### Hosted API Server

- **Versioned API** (v1 deprecated, v2 current)
- **Device Management** - Registration, heartbeat, pairing
- **Content Library** - Audio content management with filtering
- **Real-time Control** - WebSocket communication for instant commands
- **Analytics** - Usage tracking and device statistics
- **WiFi Provisioning** - Track device network setup

### Device Client (Raspberry Pi)

- **Lightweight Client** - Connects to hosted API
- **Content Synchronization** - Automatic download and caching
- **Audio Playback** - Local content playback with volume control
- **Hardware Integration** - LED control, battery monitoring
- **Command Execution** - Remote commands from API

## 📋 Prerequisites

- Python 3.13+
- SQLite (development) or PostgreSQL (production)
- For Pi Client: Raspberry Pi with audio output

## 🛠️ Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd zuri-cloud-api
```

### 2. Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or using the project dependencies
pip install -e .

======================================================================
# Using uv
pip install uv # Install uv if not already installed

# Install project dependencies
uv add <package_name>

# Or install from pyproject.toml
uv sync
```

### 3. Environment Setup

Create a `.env` file:

```bash
# Database
DATABASE_URL=sqlite:///./zuri_hosted.db

# For Pi Client
ZURI_API_URL=https://your-api-domain.com
# or for local development
ZURI_API_URL=http://localhost:8000

# Internal API security
INTERNAL_SECRET_KEY=your-internal-secret
```

### 4. Database Setup

```bash
# Initialize database
alembic upgrade head
```

## 🚀 Running the Application

### Hosted API Server

```bash
# Development
python core.py # Using python
uv run core.py # using uv

# Production
uvicorn main:app --host 0.0.0.0 --port 8000
# Or using uvicorn directly
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Device Client (Raspberry Pi)

```bash
python lightweight_pi_client.py

===== OR ======

uv run python lightweight_pi_client.py
```

## 📡 API Endpoints

Base URL: `/api/v2`

### Device Management

- `POST /devices/register` - Register new device
- `POST /devices/{device_id}/heartbeat` - Device heartbeat
- `GET /devices` - List all devices
- `POST /devices/{device_id}/pair` - Pair device with user
- `PATCH /devices/{device_id}/wifi` - Update WiFi status

### Content Management

- `GET /content/library` - Get content library (with filters)
- `POST /content/library` - Add content
- `DELETE /content/library/{content_id}` - Remove content

### Device Control

- `POST /devices/{device_id}/command` - Send device command
- `POST /playback/play` - Play content
- `POST /playback/stop` - Stop playback
- `POST /devices/{device_id}/settings` - Update device settings

### Analytics & System

- `POST /analytics/usage` - Log usage data
- `GET /analytics/usage/{device_id}` - Get device analytics
- `GET /health` - Health check
- `GET /stats` - System statistics

### WebSocket Endpoints

- `WS /ws/device/{device_id}` - Device real-time communication
- `WS /ws/mobile` - Mobile app real-time updates

## 📱 API Usage Examples

### Register Device

```bash
curl -X POST "http://localhost:8000/api/v2/devices/register" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "ZR-ABC123",
    "device_name": "Living Room Zuri",
    "ip_address": "192.168.1.100"
  }'
```

### Send Device Command

```bash
curl -X POST "http://localhost:8000/api/v2/devices/ZR-ABC123/command" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "play",
    "params": {"content_id": "story_001", "volume": 0.8}
  }'
```

### Get Content Library

```bash
curl "http://localhost:8000/api/v2/content/library?content_type=story&age_min=3&age_max=7"
```

## 🔄 API Versioning

The application supports multiple API versions:

- **v1** `(/api/v1/*)` - **DEPRECATED** - Legacy endpoints with deprecation headers
- **v2** `(/api/v2/*)` - **CURRENT** - Latest stable API

### Migration from v1 to v2

All v1 endpoints return deprecation headers. Update your clients to use v2 endpoints with the same functionality but improved error handling and validation.

## 🗄️ Database Schema

### Core Tables

- **devices** - Device registration and status
- **content** - Audio content library
- **device_commands** - Command queue for devices
- **usage_analytics** - Device usage tracking

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Check current version
alembic current

# Rollback to previous version
alembic downgrade -1
```

## 🔧 Configuration

### Device Settings Schema

```json
{
  "voice_tone": "calm",
  "voice_speed": 1.0,
  "volume": 0.8,
  "led_color": "#5E9CF3",
  "led_brightness": 0.7,
  "led_pattern": "steady"
}
```

### Content Library Filters

- `content_type`: story, phonics, affirmation, routine
- `age_min`/`age_max`: Age range filtering
- `premium_only`: Premium content flag

## 🔌 WebSocket Communication

### Device WebSocket Messages

```js
// Command from API to device
{
  "id": "cmd_123",
  "command": "play",
  "params": {"content_id": "story_001", "volume": 0.8}
}

// Response from device to API
{
  "type": "command_result",
  "command_id": "cmd_123",
  "success": true
}
```

## 📊 Monitoring & Health

### Health Check

```bash
curl http://localhost:8000/api/v2/health
```

### System Statistics

```bash
curl http://localhost:8000/api/v2/stats
```

## 🚀 Deployment

### Production Considerations

1. Use PostgreSQL instead of SQLite
2. Set up environment variables for sensitive data
3. Configure reverse proxy (nginx)
4. Enable HTTPS/SSL certificates
5. Set up monitoring and logging

### Docker Deployment

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY . .
RUN pip install -e .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🧪 Testing

### Manual Testing

1. Start the API server: `python core.py` or `uv run core.py`
2. Visit documentation: `http://localhost:8000/api/v2/docs`
3. Register a test device
4. Send commands via API

### Pi Client Testing

1. Start API server locally: `python core.py` or `uv run core.py`
2. Run Pi client: `python lightweight_pi_client.py` or `uv run lightweight_pi_client.py`
3. Check device appears in `/devices` endpoint
4. Send commands to device

### 🤝 Contributing

1. Follow the existing code structure
2. Add new endpoints to appropriate version router
3. Update database models if needed
4. Test WebSocket functionality
5. Update documentation

## 📄 License

[We Add license information here]

## 🔗 Links

- [API Documentation (Swagger)](http://localhost:8000/api/v2/docs)
- [API Documentation (ReDoc)](http://localhost:8000/api/v2/redoc)
- [Health Check](http://localhost:8000/api/v2/health)

## 📞 Support

For technical support or questions, please open an issue in the [GitHub Issue Tracker](../../issues).
