# start_backend.py - Start the FastAPI backend server
import subprocess
import sys
import os

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting SOAP Note App Backend...")
    
    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    
    try:
        # Start uvicorn server
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", "127.0.0.1",
            "--port", "8002",
            "--reload"
        ], cwd=backend_dir)
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped")
    except Exception as e:
        print(f"❌ Error starting backend: {e}")

if __name__ == "__main__":
    start_backend()
