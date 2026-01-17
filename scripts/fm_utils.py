import time
import sys
import ctypes
from pywinauto import Desktop, Application
import pyautogui
import subprocess
import os

# --- Overlay Utils ---
OVERLAY_PROCESS = None
STATUS_FILE = "overlay_status.txt"

def start_overlay():
    global OVERLAY_PROCESS
    try:
        # Create initial status
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            f.write("準備中...")
            
        script_path = os.path.join(os.path.dirname(__file__), "overlay.py")
        OVERLAY_PROCESS = subprocess.Popen(["python", script_path], shell=True)
    except Exception as e:
        print(f"Failed to start overlay: {e}", file=sys.stderr)

def update_overlay(message):
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            f.write(message)
    except Exception as e:
        print(f"Failed to update overlay: {e}", file=sys.stderr)

def stop_overlay():
    global OVERLAY_PROCESS
    try:
        update_overlay("EXIT") # Signal to self-destruct
        time.sleep(0.5)
        if OVERLAY_PROCESS:
            OVERLAY_PROCESS.terminate()
            OVERLAY_PROCESS = None
    except:
        pass

def set_input_block(block=True):
    """Block/Unblock user input (requires Admin privileges)."""
    try:
        res = ctypes.windll.user32.BlockInput(block)
        if res == 0 and block:
            print("WARNING: Could not block input. Run as Administrator.", file=sys.stderr)
    except Exception as e:
        print(f"BlockInput error: {e}", file=sys.stderr)

def find_main_window(backend="uia"):
    """Find the main FileMaker Pro window, handling custom app titles."""
    try:
        app = Application(backend=backend).connect(path="FileMaker Pro.exe")
        # Get all windows for this process
        windows = app.windows()
        for w in windows:
            t = w.window_text()
            # Avoid the Manage Database dialog itself
            if "Manage Database" in t or "データベースの管理" in t:
                continue
            # Usually the main window has a title (not empty)
            if t: 
                return w
    except:
        pass
    
    # Fallback: legacy title search
    try:
        desktop = Desktop(backend=backend)
        for w in desktop.windows():
            if "FileMaker Pro" in w.window_text():
                return w
    except:
        pass
    return None

def close_unwanted_dialogs():
    """Found any dialog that is NOT 'Manage Database'? Close it."""
    print("  > Checking for unwanted dialogs...", file=sys.stderr)
    try:
        desktop = Desktop(backend="win32") 
        windows = desktop.windows()
        
        target_keywords = ["データベースの管理", "Manage Database"]
        
        for w in windows:
            if not w.is_visible(): continue
            title = w.window_text()
            
            if not title or "FileMaker Pro" == title: continue
            
            if any(k in title for k in target_keywords):
                continue
            pass 
        pass

    except Exception as e:
        print(f"Error closing dialogs: {e}", file=sys.stderr)

def ensure_manage_database():
    """
    Robustly ensure 'Manage Database' dialog is Open and Focused.
    """
    print("[Robust] Ensuring 'Manage Database' is active...", file=sys.stderr)
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            # 1. Search for Dialog
            desktop_uia = Desktop(backend="uia")
            dialog = None
            
            for w in desktop_uia.windows():
                t = w.window_text()
                # Exact or substring match for target dialog
                if "データベースの管理" in t or "Manage Database" in t:
                    dialog = w
                    break
            
            if dialog:
                if dialog.get_show_state() == 2: # Minimized
                    dialog.restore()
                dialog.set_focus()
                print("  > Found and focused 'Manage Database'.", file=sys.stderr)
                return True
            
            # 2. Not found. Try to find Main Window to send Shortcut.
            main_win = find_main_window(backend="uia")
            
            if main_win:
                t = main_win.window_text()
                print(f"  > Main window found: '{t}'", file=sys.stderr)
                
                # If we are here, Dialog is NOT found.
                # So whatever top window we found is likely the Main Window or an obstruction.
                
                # Try to clean up obstructions (ESC) ONLY if we've tried sending shortcut before and failed?
                # Or just assume we can press ESC once safely?
                # Let's try sending ESC only if we are not on attempt 0 (give it a shot first)
                if attempt > 0:
                     print(f"  > Sending ESC to clear potential obstructions...", file=sys.stderr)
                     try:
                         main_win.set_focus()
                         time.sleep(0.2)
                         pyautogui.press('esc')
                         time.sleep(0.5)
                     except: pass

                # 3. Send Open Shortcut
                print("  > Sending Ctrl+Shift+D to open Manage Database...", file=sys.stderr)
                try:
                    main_win.set_focus()
                    time.sleep(0.2)
                    pyautogui.hotkey('ctrl', 'shift', 'd')
                    time.sleep(2.0) # Wait for animation/load
                except Exception as e:
                    print(f"  > Failed to focus/send keys: {e}", file=sys.stderr)
            else:
                 print("  > Could not find Main FileMaker Window.", file=sys.stderr)
                 
        except Exception as e:
            print(f"  > Attempt {attempt+1} error: {e}", file=sys.stderr)
            time.sleep(1)
            
    print("ERROR: Could not open Manage Database after retries.", file=sys.stderr)
    return False

if __name__ == "__main__":
    ensure_manage_database()
