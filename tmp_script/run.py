#!/usr/bin/env python3
"""
Creative Master - Startup Script
"""

import subprocess
import sys
import os

def install_backend():
    print("Installing backend dependencies...")
    subprocess.run([
        sys.executable, "-m", "pip", "install", "-r", 
        "backend/requirements.txt"
    ], cwd=os.path.dirname(os.path.abspath(__file__)))

def install_frontend():
    print("Installing frontend dependencies...")
    subprocess.run(["npm", "install"], 
        cwd=os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend"))

def start_backend():
    print("Starting backend server...")
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "backend.main:app", "--reload", "--port", "8000"
    ], cwd=os.path.dirname(os.path.abspath(__file__)))

def start_frontend():
    print("Starting frontend server...")
    subprocess.run(["npm", "run", "dev"], 
        cwd=os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend"))

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Creative Master")
    parser.add_argument("command", choices=["install", "backend", "frontend", "all"])
    args = parser.parse_args()
    
    if args.command == "install":
        install_backend()
        install_frontend()
    elif args.command == "backend":
        start_backend()
    elif args.command == "frontend":
        start_frontend()
    elif args.command == "all":
        import threading
        backend_thread = threading.Thread(target=start_backend)
        frontend_thread = threading.Thread(target=start_frontend)
        backend_thread.start()
        frontend_thread.start()
        backend_thread.join()
        frontend_thread.join()

if __name__ == "__main__":
    main()
