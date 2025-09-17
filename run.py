#!/usr/bin/env python3
"""
MoM Agent - Minutes of Meeting Generator
Run this script to start the application
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import streamlit
        import requests
        print("All dependencies are installed")
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True

def main():
    """Main function to run the application"""
    print("Starting MoM Agent - Minutes of Meeting Generator")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Change to app directory
    app_dir = Path(__file__).parent / "app"
    os.chdir(app_dir)
    
    # Run streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "main.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--server.headless", "false"
        ])
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"Error running application: {e}")

if __name__ == "__main__":
    main()