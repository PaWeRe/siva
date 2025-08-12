#!/usr/bin/env python3
"""Simple HTTP server to serve the voice client HTML file."""

import http.server
import socketserver
import os
import webbrowser
import threading
import time

PORT = 3000
# Updated directory to point to frontend folder
DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Add CORS headers to allow WebSocket connections
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        super().end_headers()


def open_browser():
    """Open browser after a short delay to ensure server is running."""
    time.sleep(1)
    webbrowser.open(f"http://localhost:{PORT}/voice_client.html")


if __name__ == "__main__":
    # Start browser in background thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()

    # Start server
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🌐 Voice Client Server running at http://localhost:{PORT}")
        print(f"📁 Serving files from: {DIRECTORY}")
        print(f"🎤 Open http://localhost:{PORT}/voice_client.html to start")
        print("\nPress Ctrl+C to stop the server")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")
