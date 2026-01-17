import os
import sys
import time
import subprocess
import pygetwindow as gw
from pywinauto import Application

def launch_filemaker(executable_path):
    print(f"Checking for FileMaker Pro process...")
    try:
        # 1. 既に起動しているかプロセスでチェック
        from pywinauto import Application, Desktop
        try:
            app = Application(backend="win32").connect(path="FileMaker Pro.exe")
            print("FileMaker is already running. Bringing to front...")
            # 全ウィンドウから一番手前にある可視ウィンドウを取得
            dlg = app.top_window()
            if dlg.exists() and dlg.is_visible():
                dlg.set_focus()
                return True
        except:
            # プロセスがまだない場合は次へ
            pass

        # 2. 存在しない場合は起動
        if not os.path.exists(executable_path):
            print(f"Error: FileMaker executable not found at {executable_path}")
            return False

        print(f"Launching FileMaker from {executable_path}...")
        subprocess.Popen([executable_path])
        
        # 起動を待つ
        retries = 30
        while retries > 0:
            try:
                app = Application(backend="win32").connect(path="FileMaker Pro.exe")
                dlg = app.top_window()
                if dlg.exists() and dlg.is_visible():
                    print("FileMaker started and window found.")
                    dlg.set_focus()
                    return True
            except:
                pass
            time.sleep(1)
            retries -= 1
        
        print("Timeout waiting for FileMaker to start.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

if __name__ == "__main__":
    default_path = r"C:\Program Files\FileMaker\FileMaker Pro\FileMaker Pro.exe"
    # Allow path override via argument
    if len(sys.argv) > 1:
        default_path = sys.argv[1]
    
    success = launch_filemaker(default_path)
    sys.exit(0 if success else 1)
