#!/usr/bin/env python3
"""
SIVA Demo Launcher

A simple launcher script to run the different SIVA framework demos.
"""

import sys
import subprocess
import os
from pathlib import Path


def check_server_running():
    """Check if the SIVA server is running."""
    try:
        import requests

        response = requests.get("http://localhost:8000/", timeout=5)
        return response.status_code == 200
    except:
        return False


def start_server():
    """Start the SIVA server."""
    print("🚀 Starting SIVA server...")
    print("This will start the FastAPI backend and voice client server.")
    print("Press Ctrl+C to stop the server when done.")
    print()

    try:
        subprocess.run([sys.executable, "run_voice_app.py"])
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")


def run_demo(demo_name):
    """Run a specific demo."""
    demo_files = {
        "1": "patient_intake_demo.py",
        "2": "clinical_pearls_demo.py",
        "3": "unified_demo.py",
        "4": "learning_demo.py",
    }

    if demo_name not in demo_files:
        print(f"❌ Unknown demo: {demo_name}")
        return

    demo_file = demo_files[demo_name]

    if not Path(demo_file).exists():
        print(f"❌ Demo file not found: {demo_file}")
        return

    print(f"🎬 Running {demo_file}...")
    print()

    try:
        subprocess.run([sys.executable, demo_file])
    except KeyboardInterrupt:
        print("\n👋 Demo stopped.")


def show_menu():
    """Show the demo selection menu."""
    print("🧠 SIVA Framework Demo Launcher")
    print("=" * 50)
    print()

    if not check_server_running():
        print("⚠️  SIVA server is not running.")
        print("You need to start the server first to run the demos.")
        print()
        print("Options:")
        print("  s - Start SIVA server")
        print("  q - Quit")
        print()

        choice = input("Enter your choice: ").lower().strip()

        if choice == "s":
            start_server()
        elif choice == "q":
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice.")

        return

    print("✅ SIVA server is running!")
    print()
    print("Available demos:")
    print("  1 - Patient Intake Learning Progression Demo")
    print("  2 - Clinical Pearls Experience-Based Evidence Demo")
    print("  3 - Unified Framework Demo (Both applications)")
    print("  4 - Original Learning Demo")
    print()
    print("Other options:")
    print("  s - Start/restart SIVA server")
    print("  d - Open dashboard in browser")
    print("  v - Open voice client in browser")
    print("  q - Quit")
    print()

    choice = input("Enter your choice: ").lower().strip()

    if choice in ["1", "2", "3", "4"]:
        run_demo(choice)
    elif choice == "s":
        start_server()
    elif choice == "d":
        print("🌐 Opening dashboard...")
        import webbrowser

        webbrowser.open("http://localhost:8000/dashboard")
    elif choice == "v":
        print("🎤 Opening voice client...")
        import webbrowser

        webbrowser.open("http://localhost:3000/voice_client.html")
    elif choice == "q":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice.")


def main():
    """Main function."""
    print("Welcome to the SIVA Framework Demo Launcher!")
    print()

    while True:
        try:
            show_menu()

            # Ask if user wants to continue
            print()
            continue_choice = input("Run another demo? (y/n): ").lower().strip()
            if continue_choice != "y":
                print("👋 Thanks for using SIVA!")
                break

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            break


if __name__ == "__main__":
    main()
