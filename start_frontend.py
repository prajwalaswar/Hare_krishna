# start_frontend.py - Start the Streamlit frontend
import subprocess
import sys
import os

def start_frontend():
    """Start the Streamlit frontend"""
    print("🚀 Starting SOAP Note App Frontend...")
    
    # Change to frontend directory
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    
    try:
        # Start streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "app.py", 
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ], cwd=frontend_dir)
    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped")
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")

if __name__ == "__main__":
    start_frontend()
