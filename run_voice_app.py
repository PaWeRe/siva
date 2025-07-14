#!/usr/bin/env python3
"""Run both the FastAPI backend and voice client server."""

import subprocess
import sys
import time
import os
from pathlib import Path


def run_backend():
    """Run the FastAPI backend."""
    print("🚀 Starting FastAPI backend...")
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "localhost",
            "--port",
            "8000",
            "--reload",
        ],
        cwd=Path(__file__).parent,
    )


def run_client_server():
    """Run the voice client server."""
    print("🌐 Starting voice client server...")
    return subprocess.Popen(
        [sys.executable, "serve_client.py"], cwd=Path(__file__).parent
    )


def main():
    """Main function to coordinate both servers."""
    print("🎤 SIVA Voice Application Launcher")
    print("=" * 40)

    # Check if .env file exists
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        print("⚠️  Warning: .env file not found. Make sure you have:")
        print("   - OPENAI_API_KEY (for chat + STT)")
        print("   - CARTESIA_API_KEY (for TTS)")
        print()

    try:
        # Start backend
        backend_process = run_backend()

        # Wait a moment for backend to start
        print("⏳ Waiting for backend to start...")
        time.sleep(3)

        # Start client server
        client_process = run_client_server()

        print("\n✅ Both servers are running!")
        print("🔗 Voice Client: http://localhost:3000/voice_client.html")
        print("🔗 Backend API: http://localhost:8000")
        print("\nPress Ctrl+C to stop both servers")

        # Wait for processes
        try:
            backend_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping servers...")
            backend_process.terminate()
            client_process.terminate()

            # Wait for processes to clean up
            backend_process.wait()
            client_process.wait()

            print("👋 All servers stopped")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
