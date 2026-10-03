import subprocess
import time
import sys

def main():
    print("Starting FastAPI...")
    api_process = subprocess.Popen(["uvicorn", "app.main:app", "--reload"])
    time.sleep(2)
    print("Starting Streamlit...")
    ui_process = subprocess.Popen(["streamlit", "run", "dashboard/streamlit_app.py"])
    
    try:
        api_process.wait()
        ui_process.wait()
    except KeyboardInterrupt:
        print("Shutting down...")
        api_process.terminate()
        ui_process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
