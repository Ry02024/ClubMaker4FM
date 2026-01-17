from pywinauto import Desktop, Application
import sys
import psutil

def diagnose():
    print("=== FileMaker Automation Diagnostic ===")
    
    # Check Process
    fm_procs = [p for p in psutil.process_iter(['name', 'pid']) if 'FileMaker' in p.info['name']]
    if not fm_procs:
        print("[FAIL] FileMaker Pro process NOT found.")
    else:
        print(f"[OK] FileMaker Pro processes found: {fm_procs}")

    # Check Windows (UIA)
    print("\n--- Visible Windows (UIA) ---")
    try:
        desktop = Desktop(backend="uia")
        found_fm_window = False
        for w in desktop.windows():
            title = w.window_text()
            if title:
                print(f" - '{title}'")
                if "FileMaker" in title:
                    found_fm_window = True
        
        if found_fm_window:
            print("[OK] Found at least one window with 'FileMaker' in title via UIA.")
        else:
            print("[FAIL] Could not find any FileMaker window via UIA.")
            
    except Exception as e:
        print(f"[ERROR] UIA enumeration failed: {e}")

    # Try connection
    print("\n--- Connection Test ---")
    try:
        app = Application(backend="uia").connect(path="FileMaker Pro.exe")
        print("[OK] Successfully connected to FileMaker Pro application.")
        top = app.top_window()
        print(f"Top window title: '{top.window_text()}'")
    except Exception as e:
        print(f"[FAIL] Failed to connect to application: {e}")

if __name__ == "__main__":
    diagnose()
