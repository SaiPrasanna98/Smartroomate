#!/usr/bin/env python3
"""
SmartRoommate+ - AI-Powered Roommate Finder
Run this script to start the application
"""

import uvicorn
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

if __name__ == "__main__":
    print("Starting SmartRoommate+...")
    print("Open your browser to: http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        app_dir="backend"
    )
