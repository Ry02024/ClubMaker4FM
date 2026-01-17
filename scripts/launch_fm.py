import os
import sys
import time
import subprocess
import pygetwindow as gw
from pywinauto import Application

def launch_filemaker(executable_path):
    if not os.path.exists(executable_path):
        print(f"Error: FileMaker executable not found at {executable_path}")
        return False

    try:
        # Launch the application
        subprocess.Popen([executable_path])
        print(f"Launching FileMaker from {executable_path}...")
        
        # Wait for the window to appear
        retries = 20
        while retries > 0:
            windows = gw.getWindowsWithTitle('FileMaker Pro')
            if windows:
                fm_window = windows[0]
                print(f"Found FileMaker window. Activating...")
                try:
                    # Attempt to bring to foreground using pywinauto for more reliability
                    app = Application().connect(path=executable_path)
                    app.top_window().set_focus()
                except Exception as e:
                    print(f"Warning: pywinauto focus failed, falling back to pygetwindow: {e}")
                    fm_window.activate()
                
                return True
            time.sleep(0.5)
            retries -= 1
        
        print("Timeout waiting for FileMaker window.")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

if __name__ == "__main__":
    default_path = r"C:\Program Files\FileMaker\FileMaker Pro\FileMaker Pro.exe"
    # Allow path override via argument
    if len(sys.argv) > 1:
        default_path = sys.argv[1]
    
    success = launch_filemaker(default_path)
    sys.exit(0 if success else 1)
