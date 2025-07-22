#!/usr/bin/env python3
"""
Lightweight Zuri Pi Client
Connects to hosted API and handles local device functions
"""

import asyncio
import json
import socket
import subprocess
import time
import uuid
import hashlib
import aiofiles
from pathlib import Path
from datetime import datetime
import requests
import websockets
from zeroconf import IPVersion, ServiceInfo, Zeroconf
import os
from dotenv import load_dotenv
import sqlite3

load_dotenv()

BASE_DIR = "/home/olawill/Documents/Zuri/pi"

class ZuriPiClient:
    def __init__(self):
        self.device_id = self._get_device_id()
        self.api_url = os.getenv("ZURI_API_URL", "https://api.zuri.com")
        self.ws_url = self.api_url.replace("http", "ws") + f"/ws/device/{self.device_id}"
        self.content_dir = Path(f"{BASE_DIR}/zuri_content")
        self.content_dir.mkdir(exist_ok=True)
        
        self.battery_level = 100
        self.is_playing = False
        self.current_content = None
        self.settings = {
            "voice_tone": "calm",
            "voice_speed": 1.0,
            "volume": 0.8,
            "led_color": "#5E9CF3",
            "led_brightness": 0.7
        }
        
        # Initialize local database for content cache
        self._init_local_db()
        
        # Initialize hardware
        self._init_hardware()

    def _get_device_id(self) -> str:
        """Get or generate device ID"""
        Path(BASE_DIR).mkdir(parents=True, exist_ok=True)
        device_id_file = f"{BASE_DIR}/.zuri_device_id"
        
        if os.path.exists(device_id_file):
            with open(device_id_file, 'r') as f:
                return f.read().strip()
        
        # Generate new device ID based on Pi serial
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('Serial'):
                        serial = line.split(':')[1].strip()
                        device_id = f"ZR-{serial[-6:].upper()}"
                        break
                else:
                    device_id = f"ZR-{hex(uuid.getnode())[2:].upper()[-6:]}"
        except:
            device_id = f"ZR-{hex(uuid.getnode())[2:].upper()[-6:]}"
        
        with open(device_id_file, 'w') as f:
            f.write(device_id)
        
        return device_id

    def _init_local_db(self):
        """Initialize local SQLite database"""
        conn = sqlite3.connect(f"{BASE_DIR}/zuri_local.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS local_content (
                content_id TEXT PRIMARY KEY,
                title TEXT,
                file_path TEXT,
                checksum TEXT,
                downloaded_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def _init_hardware(self):
        """Initialize hardware components"""
        try:
            # Initialize GPIO for LED control (placeholder)
            print("Initializing hardware components...")
            # In real implementation: setup GPIO pins, audio, etc.
        except Exception as e:
            print(f"Hardware initialization error: {e}")

    async def register_with_api(self):
        """Register device with hosted API"""
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            
            response = requests.post(
                f"{self.api_url}/devices/register",
                json={
                    "device_id": self.device_id,
                    "device_name": f"Zuri Device {self.device_id}",
                    "ip_address": local_ip,
                    "firmware_version": "1.0.0"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"Device {self.device_id} registered successfully")
                return True
            else:
                print(f"Registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Registration error: {e}")
            return False

    async def send_heartbeat(self):
        """Send periodic heartbeat to API"""
        try:
            response = requests.post(
                f"{self.api_url}/devices/{self.device_id}/heartbeat",
                json={
                    "battery_level": self.battery_level,
                    "status": "online",
                    "wifi_ssid": "TestNetwork"
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"💓 Heartbeat sent - Battery: {self.battery_level}%")
                
                # Process any pending commands
                if data.get("commands"):
                    for command in data["commands"]:
                        await self._execute_command(command)
            return True
                        
        except Exception as e:
            print(f"Heartbeat error: {e}")
            return False

    async def _execute_command(self, command):
        """Execute command from API"""
        command_id = command["id"]
        cmd_type = command["command"]
        params = command.get("params", {})
        
        print(f"🎯 Executing command: {cmd_type} with params: {params}")
        
        success = False
        
        try:
            if cmd_type == "play":
                success = await self._play_content(params.get("content_id"), params.get("volume"))
            elif cmd_type == "stop":
                success = self._stop_playback()
            elif cmd_type == "pause":
                success = self._pause_playback()
            elif cmd_type == "update_settings":
                success = self._update_settings(params)
            elif cmd_type == "sync_content":
                success = await self._sync_content()
            elif cmd_type == "set_led":
                success = self._set_led_color(params.get("color"), params.get("brightness"))
            
        except Exception as e:
            print(f"Command execution error: {e}")
        
        # Report command result back to API (if WebSocket is available)
        # For now, just log it
        print(f"Command {command_id} executed: {'success' if success else 'failed'}")

    async def _play_content(self, content_id: str, volume: float = None) -> bool:
        """Play content locally"""
        try:
            # Check if content exists locally
            content_path = self.content_dir / f"{content_id}.mp3"
            
            if not content_path.exists():
                # Download content first
                await self._download_content(content_id)
            
            if not content_path.exists():
                print(f"Content {content_id} not available")
                return False
            
            # Stop current playback
            if self.is_playing:
                self._stop_playback()
            
            # Set volume if specified
            if volume:
                self._set_volume(volume)
            
            # Play audio using system command
            subprocess.Popen([
                'mpg123', '--quiet', str(content_path)
            ])
            
            self.is_playing = True
            self.current_content = content_id
            
            # Simulate playback (Ubuntu doesn't have mpg123 by default)
            print(f"🎵 Simulating audio playback of {content_id}")
            self.is_playing = True
            self.current_content = content_id
            
            return True
            
        except Exception as e:
            print(f"Playback error: {e}")
            return False

    def _stop_playback(self) -> bool:
        """Stop current playback"""
        try:
            print("⏹️ Stopping playback")
            subprocess.run(['pkill', 'mpg123'], check=False)
            self.is_playing = False
            self.current_content = None
            print("Playback stopped")
            return True
        except Exception as e:
            print(f"Stop playback error: {e}")
            return False
        
    def _pause_playback(self) -> bool:
        """Simulate pausing playback"""
        try:
            print("⏸️ Pausing playback")
            return True
        except Exception as e:
            print(f"❌ Pause error: {e}")
            return False

    def _update_settings(self, new_settings: dict) -> bool:
        """Update device settings"""
        try:
            self.settings.update(new_settings)
            
            # Apply settings to hardware
            if "volume" in new_settings:
                self._set_volume(new_settings["volume"])
            
            if "led_color" in new_settings:
                self._set_led_color(
                    new_settings["led_color"],
                    new_settings.get("led_brightness", self.settings["led_brightness"])
                )
            
            print(f"⚙️ Settings updated: {new_settings}")
            return True
            
        except Exception as e:
            print(f"Settings update error: {e}")
            return False

    def _set_volume(self, volume: float):
        """Set system volume"""
        try:
            volume_percent = int(volume * 100)
            subprocess.run([
                'amixer', 'set', 'Master', f'{volume_percent}%'
            ], check=True)
        except Exception as e:
            print(f"Volume control error: {e}")

    def _set_led_color(self, color: str, brightness: float = 0.7) -> bool:
        """Set LED color (placeholder - implement with actual GPIO)"""
        try:
            print(f"Setting LED color to {color} with brightness {brightness}")
            # In real implementation: control GPIO pins for RGB LED
            return True
        except Exception as e:
            print(f"LED control error: {e}")
            return False

    async def _download_content(self, content_id: str):
        """Download content from API"""
        try:
            # Get content info from API
            response = requests.get(f"{self.api_url}/content/library")
            if response.status_code != 200:
                return False
            
            content_library = response.json()
            content_info = next((item for item in content_library if item["content_id"] == content_id), None)
            
            if not content_info:
                print(f"Content {content_id} not found in library")
                return False
            
            # Download file
            file_response = requests.get(content_info["file_url"], stream=True, timeout=60)
            file_response.raise_for_status()
            
            content_path = self.content_dir / f"{content_id}.mp3"
            
            async with aiofiles.open(content_path, 'wb') as f:
                for chunk in file_response.iter_content(chunk_size=8192):
                    await f.write(chunk)
            
            # Verify checksum if provided
            if content_info.get("checksum"):
                if self._verify_checksum(content_path, content_info["checksum"]):
                    print(f"Downloaded content: {content_info['title']}")
                    self._save_content_to_db(content_id, content_info["title"], str(content_path), content_info.get("checksum", ""))
                else:
                    content_path.unlink()  # Delete corrupted file
                    print(f"Checksum verification failed for {content_id}")
            
        except Exception as e:
            print(f"Download error for {content_id}: {e}")

    def _verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """Verify file checksum"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest() == expected_checksum
        except:
            return False

    def _save_content_to_db(self, content_id: str, title: str, file_path: str, checksum: str):
        """Save content info to local database"""
        conn = sqlite3.connect(f"{BASE_DIR}/zuri_local.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO local_content 
            (content_id, title, file_path, checksum, downloaded_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (content_id, title, file_path, checksum, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()

    async def _sync_content(self) -> bool:
        """Sync all available content"""
        try:
            response = requests.get(f"{self.api_url}/content/library")
            if response.status_code != 200:
                return False
            
            content_library = response.json()
            
            for content_item in content_library:
                content_id = content_item["content_id"]
                content_path = self.content_dir / f"{content_id}.mp3"
                
                # Download if not exists
                if not content_path.exists():
                    await self._download_content(content_id)
            
            print("Content sync completed")
            return True
            
        except Exception as e:
            print(f"Content sync error: {e}")
            return False

    def _update_battery(self):
        """Update battery level (placeholder)"""
        # In real implementation: read actual battery level
        self.battery_level = max(10, self.battery_level - 1)  # Simulate drain

    async def run(self):
        """Main client loop"""
        print(f"🚀 Starting Zuri Pi Client (Ubuntu) - Device ID: {self.device_id}")
        
        # Register with API
        if not await self.register_with_api():
            print("❌ Failed to register with API, retrying in 30 seconds...")
            await asyncio.sleep(30)
            return await self.run()
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        # Start battery monitor
        battery_task = asyncio.create_task(self._battery_monitor())
        
        print("✅ Pi Client running - Press Ctrl+C to stop")
        
        # Wait for tasks
        try:
            await asyncio.gather(heartbeat_task, battery_task)
        except KeyboardInterrupt:
            print("\n👋 Pi Client stopping...")

    async def _heartbeat_loop(self):
        """Heartbeat loop"""
        while True:
            await self.send_heartbeat()
            await asyncio.sleep(30)  # Heartbeat every 30 seconds

    async def _battery_monitor(self):
        """Battery monitoring loop"""
        while True:
            self._update_battery()
            await asyncio.sleep(300)  # Update every 5 minutes

if __name__ == "__main__":
    client = ZuriPiClient()
    asyncio.run(client.run())