#!/usr/bin/env python3
"""
ZenMon Agent Health Check Server
Provides HTTP endpoints for container health monitoring
"""

import http.server
import socketserver
import json
import threading
import time
import psutil
import os

class HealthHandler(http.server.BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        """Suppress HTTP access logs"""
        pass
        
    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/health":
            self._handle_health()
        elif self.path == "/info":
            self._handle_info()
        else:
            self._handle_not_found()
    
    def _handle_health(self):
        """Return health status with system metrics"""
        try:
            health_data = {
                "status": "healthy",
                "timestamp": time.time(),
                "hostname": os.uname().nodename,
                "os": self._get_os_info(),
                "agent_version": os.environ.get("ZENMON_AGENT_VERSION", "1.0.0"),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
                "uptime": time.time() - psutil.boot_time()
            }
            self._send_json_response(200, health_data)
        except Exception as e:
            error_data = {"status": "error", "message": str(e)}
            self._send_json_response(500, error_data)
    
    def _handle_info(self):
        """Return agent information"""
        try:
            info_data = {
                "hostname": os.uname().nodename,
                "operating_system": self._get_os_info(),
                "agent_version": os.environ.get("ZENMON_AGENT_VERSION", "1.0.0"),
                "service": "ZenMon Agent",
                "api_url": os.environ.get("ZENMON_API_URL", "not_set"),
                "host_id": os.environ.get("HOST_ID", "not_set")
            }
            self._send_json_response(200, info_data)
        except Exception as e:
            error_data = {"status": "error", "message": str(e)}
            self._send_json_response(500, error_data)
    
    def _handle_not_found(self):
        """Handle 404 responses"""
        error_data = {
            "status": "error",
            "message": "Endpoint not found",
            "available_endpoints": ["/health", "/info"]
        }
        self._send_json_response(404, error_data)
    
    def _send_json_response(self, status_code, data):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _get_os_info(self):
        """Get OS information"""
        try:
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            return line.split("=")[1].strip().strip('"')
            return f"{os.uname().sysname} {os.uname().release}"
        except:
            return "Unknown Linux"

def start_health_server(port=8080):
    """Start HTTP server"""
    with socketserver.TCPServer(("", port), HealthHandler) as httpd:
        print(f"Health server started on port {port}")
        httpd.serve_forever()

def main():
    port = int(os.environ.get("HEALTH_PORT", 8080))
    
    # Start in thread
    health_thread = threading.Thread(target=start_health_server, args=(port,), daemon=True)
    health_thread.start()
    
    # Keep alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Health server stopped")

if __name__ == "__main__":
    main()