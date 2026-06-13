import subprocess
import sys
import time
import os

def main():
    print("Starting Resume Intelligence System...")
    # Determine python command
    python_cmd = sys.executable
    
    # Start backend
    backend_env = os.environ.copy()
    backend_proc = subprocess.Popen(
        [python_cmd, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        env=backend_env
    )
    
    # Wait briefly for backend to initialize
    time.sleep(2)
    
    # Start frontend
    frontend_proc = subprocess.Popen(
        [python_cmd, "-m", "streamlit", "run", "frontend/app.py", "--server.port", "8501"]
    )
    
    try:
        # Keep running
        while True:
            time.sleep(1)
            # Check if either process died
            if backend_proc.poll() is not None:
                print("Backend process terminated.")
                break
            if frontend_proc.poll() is not None:
                print("Frontend process terminated.")
                break
    except KeyboardInterrupt:
        print("\nShutting down services...")
    finally:
        backend_proc.terminate()
        frontend_proc.terminate()
        backend_proc.wait()
        frontend_proc.wait()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
