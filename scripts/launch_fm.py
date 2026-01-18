import os
import sys
import time
import subprocess
from pywinauto import Application, Desktop
import fm_utils

def launch_filemaker(executable_path):
    print(f"--- Launch/Focus FileMaker Pro ---")
    
    try:
        # 1. すでにメインウィンドウが開いているかチェック
        main_win = fm_utils.find_main_window(backend="uia") or fm_utils.find_main_window(backend="win32")
             
        if main_win:
            print(f"FileMaker is already running: '{main_win.window_text()}'. Bringing to front...")
            try:
                # 安全な pywinauto メソッドを使用
                if main_win.get_show_state() == 2: # Minimized
                    main_win.restore()
                main_win.set_focus()
                return True
            except Exception as e:
                print(f"Warning: Failed to focus existing window: {e}")

        # 2. プロセスが存在するか接続試行 (ウィンドウがないだけの可能性)
        try:
            app = Application(backend="win32").connect(path="FileMaker Pro.exe")
            print("Connected to FileMaker process (connecting to top window).")
            dlg = app.top_window()
            if dlg.exists() and dlg.is_visible():
                dlg.set_focus()
                return True
        except:
            # 3. 存在しない場合は起動
            if not os.path.exists(executable_path):
                print(f"ERROR: FileMaker executable not found at: {executable_path}")
                # フォールバック: ショートカットなしの直接実行ファイル
                p = r"C:\Program Files\FileMaker\FileMaker Pro\FileMaker Pro.exe"
                if os.path.exists(p): executable_path = p
                else: return False

            print(f"Launching FileMaker: {executable_path}")
            # os.startfile は最も「ユーザーがアイコンをクリックした」時に近い挙動
            os.startfile(executable_path)
        
        # 4. 起動を待つ
        print("Waiting for FileMaker window to appear...")
        retries = 15
        while retries > 0:
            main_win = fm_utils.find_main_window(backend="uia") or fm_utils.find_main_window(backend="win32")
            if main_win and main_win.is_visible():
                print(f"FileMaker window found: '{main_win.window_text()}'")
                try:
                    main_win.set_focus()
                    return True
                except:
                    return True
            time.sleep(2.0)
            retries -= 1
        
        print("Timeout: Waiting for FileMaker window.")
        return False
        
    except Exception as e:
        print(f"Unexpected error in launch_fm: {e}")
        return False

if __name__ == "__main__":
    # デフォルトパス (スタートメニューのショートカットを優先)
    default_path = r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\FileMaker Pro.lnk"
    if not os.path.exists(default_path):
        default_path = r"C:\Program Files\FileMaker\FileMaker Pro\FileMaker Pro.exe"
        
    if len(sys.argv) > 1:
        default_path = sys.argv[1]
    
    success = launch_filemaker(default_path)
    if success:
        time.sleep(1.0)
    sys.exit(0 if success else 1)
