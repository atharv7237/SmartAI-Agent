"""
Python API Server & Static File Host for AI Tool-Calling Agent Frontend.
Uses Python built-in ThreadingHTTPServer (Zero external dependencies).
"""

import os
import sys
import json
import time
import mimetypes
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from agent import AIAgent
from tools import TOOL_DEFINITIONS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [Server] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("Server")

# Determine frontend directory path
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")

# Global Agent instance for the server
agent_instance = AIAgent()


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Multi-threaded HTTP Server to handle simultaneous requests cleanly."""
    daemon_threads = True


class AgentRequestHandler(SimpleHTTPRequestHandler):
    """
    Handles REST API endpoints and serves static frontend files.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def _send_json(self, status_code: int, data: Dict[str, Any]) -> None:
        """Send JSON response with proper headers and CORS."""
        response_bytes = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self) -> None:
        """Handle CORS pre-flight requests."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        """Handle GET requests for APIs and static files."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        # API: Status & Tools
        if path == "/api/status":
            status_data = {
                "status": "online",
                "model": agent_instance.model,
                "configured": agent_instance.is_configured(),
                "mock_mode": agent_instance.mock_mode,
                "tools_count": len(TOOL_DEFINITIONS),
                "tools": [
                    {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t.get("parameters", {})
                    }
                    for t in TOOL_DEFINITIONS
                ]
            }
            self._send_json(200, status_data)
            return

        # API: Demo prompts
        elif path == "/api/demo":
            demo_data = [
                {
                    "id": "calc-1",
                    "category": "Calculator",
                    "icon": "🧮",
                    "title": "Calculate Percentage",
                    "prompt": "What is 25% of 800?"
                },
                {
                    "id": "calc-2",
                    "category": "Calculator",
                    "icon": "🧮",
                    "title": "Solve Arithmetic",
                    "prompt": "What is 1234 + 5678?"
                },
                {
                    "id": "weather-1",
                    "category": "Weather",
                    "icon": "🌤️",
                    "title": "Check Weather",
                    "prompt": "What's the weather in Mumbai?"
                },
                {
                    "id": "text-1",
                    "category": "Text Utility",
                    "icon": "📝",
                    "title": "Reverse Text",
                    "prompt": 'Reverse the text "Hello World"'
                },
                {
                    "id": "text-2",
                    "category": "Text Utility",
                    "icon": "📝",
                    "title": "Count Words",
                    "prompt": 'Count the words in "AI is changing the world."'
                },
                {
                    "id": "curr-1",
                    "category": "Currency",
                    "icon": "💱",
                    "title": "Convert Currency",
                    "prompt": "Convert 100 USD to INR"
                },
                {
                    "id": "edge-1",
                    "category": "Edge Case",
                    "icon": "🛡️",
                    "title": "Division by Zero",
                    "prompt": "What is 25 divided by 0?"
                }
            ]
            self._send_json(200, {"success": True, "prompts": demo_data})
            return

        # Serve Frontend Static Assets
        # Map root / to /index.html
        if path == "/":
            self.path = "/index.html"

        return super().do_GET()

    def do_POST(self) -> None:
        """Handle POST requests."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        # Read JSON body
        content_length = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        try:
            req_data = json.loads(post_body) if post_body else {}
        except Exception:
            self._send_json(400, {"success": False, "error": "Invalid JSON format."})
            return

        # API: Chat with Agent
        if path == "/api/chat":
            message = req_data.get("message", "").strip()
            if not message:
                self._send_json(400, {"success": False, "error": "Message parameter is required."})
                return

            # Allow client to override mock mode per request if specified
            override_mock = req_data.get("mock_mode")
            prev_mock = agent_instance.mock_mode
            if override_mock is not None:
                agent_instance.mock_mode = bool(override_mock)

            start_t = time.time()
            try:
                result = agent_instance.run(message, verbose=True)
                elapsed_ms = int((time.time() - start_t) * 1000)

                response_payload = {
                    "success": result.get("success", True),
                    "response": result.get("response", ""),
                    "tool_called": result.get("tool_called"),
                    "tool_args": result.get("tool_args"),
                    "tool_result": result.get("tool_result"),
                    "is_mock": bool(result.get("is_mock", agent_instance.mock_mode)),
                    "model": agent_instance.model,
                    "elapsed_ms": elapsed_ms
                }
                self._send_json(200, response_payload)
            except Exception as e:
                logger.error(f"Error processing chat request: {e}", exc_info=True)
                self._send_json(500, {
                    "success": False,
                    "error": "Internal server error processing request.",
                    "details": str(e)
                })
            finally:
                if override_mock is not None:
                    agent_instance.mock_mode = prev_mock
            return

        # API: Reset Conversation History
        elif path == "/api/reset":
            agent_instance.reset_conversation()
            self._send_json(200, {"success": True, "message": "Conversation history reset."})
            return

        # API: Toggle Server Mode (Mock vs Live)
        elif path == "/api/mode":
            new_mock = req_data.get("mock_mode")
            if new_mock is not None:
                agent_instance.mock_mode = bool(new_mock)
            self._send_json(200, {
                "success": True,
                "mock_mode": agent_instance.mock_mode,
                "mode_label": "Development / Mock (0 Quota)" if agent_instance.mock_mode else "Live Gemini LLM"
            })
            return

        else:
            self._send_json(404, {"success": False, "error": f"Endpoint '{path}' not found."})


def run_server(port: int = 8000, host: str = "127.0.0.1", mock_mode: Optional[bool] = None) -> None:
    """Start the HTTP Server."""
    if mock_mode is not None:
        agent_instance.mock_mode = mock_mode

    server_address = (host, port)
    httpd = ThreadedHTTPServer(server_address, AgentRequestHandler)

    mode_str = "DEV / MOCK (Zero Quota)" if agent_instance.mock_mode else f"LIVE GEMINI ({agent_instance.model})"
    print(f"\n=======================================================")
    print(f"  ✦ SmartAgent Frontend & API Server Running")
    print(f"  🌐 Local URL:  http://localhost:{port}")
    print(f"  ⚙️  Mode:       {mode_str}")
    print(f"=======================================================\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server gracefully...")
        httpd.server_close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SmartAgent Web Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind server (default: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--mock", action="store_true", help="Start server in zero-quota Mock/Development Mode")
    args = parser.parse_args()

    run_server(port=args.port, host=args.host, mock_mode=True if args.mock else None)
