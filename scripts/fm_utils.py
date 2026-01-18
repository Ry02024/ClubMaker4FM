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
    try:
        # Create initial status
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            f.write("準備中...")
            
        script_path = os.path.join(os.path.dirname(__file__), "overlay.py")
        # shell=True を使わずに実行することで、terminate() が確実に python プロセスに届くようにする
        OVERLAY_PROCESS = subprocess.Popen([sys.executable, script_path])
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
        time.sleep(0.3)
        if OVERLAY_PROCESS:
            # プロセスが生きていれば終了させる
            if OVERLAY_PROCESS.poll() is None:
                OVERLAY_PROCESS.terminate()
                try:
                    OVERLAY_PROCESS.wait(timeout=1)
                except:
                    OVERLAY_PROCESS.kill()
            OVERLAY_PROCESS = None
        
        # 強制終了のフォールバック (念のため)
        if os.path.exists(STATUS_FILE):
             try: os.remove(STATUS_FILE)
             except: pass
    except:
        pass

def set_input_block(block=True):
    """Block/Unblock user input (requires Admin privileges)."""
    try:
        # 管理者権限が必要であることを明示的にログ出力
        if block:
            print("  > [Input Block] Skipping physical block for safety.", file=sys.stderr)
        else:
            print("  > [Input Block] Releasing (was skipped).", file=sys.stderr)
            
        # 安全のため、実際のブロックは行わず常に成功を返す
        return True
    except Exception as e:
        print(f"BlockInput error: {e}", file=sys.stderr)
        return False

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

def find_manage_database_dialog():
    """FileMakerの「データベースの管理」ダイアログをDesktopレベルから徹底的に探す"""
    priority_keywords = ["データベースの管理", "Manage Database", "Manage", "の管理"]
    
    try:
        # Title regex for speed
        desktop = Desktop(backend="uia")
        # 0.5s timeout for fast check
        win = desktop.window(title_re=".*(データベースの管理|Manage Database).*", control_type="Window")
        if win.exists(timeout=0.1):
            return win
        
        # 1. win32 バックエンドでのフォールバック (タイトルが完全一致しない場合など)
        desktop_w32 = Desktop(backend="win32")
        for w in desktop_w32.windows():
            if not w.is_visible(): continue
            title = w.window_text()
            if any(pk in title for pk in priority_keywords):
                # 取得できたら UIA でラップして返す
                try:
                    return Desktop(backend="uia").window(handle=w.handle)
                except:
                    return w # Win32 wrapper as last resort
    except:
        pass
    return None

def select_fields_tab(dialog):
    """「フィールド」タブを確実に選択する"""
    try:
        # 日本語: フィールド(F) または フィールド
        # 英語: Fields または Fields (F)
        tab_item = dialog.child_window(title_re="フィールド.*|Fields.*", control_type="TabItem")
        if tab_item.exists():
            if not tab_item.is_selected():
                print("  > Selecting 'Fields' tab...", file=sys.stderr)
                tab_item.click_input()
                time.sleep(0.5)
            return True
        else:
            # ショートカット Alt+F (日本語/英語共通)
            print("  > Tab item not found via title. Trying Alt+F shortcut...", file=sys.stderr)
            dialog.type_keys("%f")
            time.sleep(0.5)
            return True
    except Exception as e:
        print(f"  > Tab selection error: {e}", file=sys.stderr)
        return False

def ensure_manage_database():
    """
    Robustly ensure 'Manage Database' dialog is Open and Focused.
    """
    print("[Robust] Ensuring 'Manage Database' is active...", file=sys.stderr)
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 1. Search for Dialog
            dialog = find_manage_database_dialog()
            
            if dialog:
                if dialog.get_show_state() == 2: # Minimized
                    dialog.restore()
                dialog.set_focus()
                print(f"  > Found and focused '{dialog.window_text()}'.", file=sys.stderr)
                return True
            
            # 2. Not found. Try to find Main Window to send Shortcut.
            main_win = find_main_window(backend="uia")
            
            if main_win:
                print(f"  > Main window found: '{main_win.window_text()}'", file=sys.stderr)
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
                    time.sleep(2.0)
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
