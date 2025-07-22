#!/usr/bin/env python3
"""
Zuri Hosted API Server
Centralized API that manages all devices and handles mobile app requests
Includes device management, content, WiFi provisioning tracking, and Swagger UI
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[".", "templates"]
    )