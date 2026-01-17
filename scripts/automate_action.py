import sys
import time
import os
import pyautogui
import pygetwindow as gw
from click_button import click_template

from pywinauto import Application, Desktop

def focus_filemaker():
    print("Searching for FileMaker by process...")
    try:
        app = Application(backend="win32").connect(path="FileMaker Pro.exe")
        windows = app.windows()
        if windows:
            for win in windows:
                if win.is_visible():
                    print(f"Focusing: {win.window_text()}")
                    win.set_focus()
                    win.wait('ready', timeout=2)
                    time.sleep(1)
                    return True
        else:
            print("No visible windows found for FileMaker process.")
    except Exception as e:
        print(f"Focus error: {e}")
        # フォールバック
        try:
            desktop = Desktop(backend="win32")
            for win in desktop.windows():
                title = win.window_text()
                if ("FileMaker" in title or "データベースの管理" in title) and "CLUB MAKER" not in title.upper():
                    win.set_focus()
                    time.sleep(1)
                    return True
        except:
            pass
    return False

def automate_field_import(template_name):
    print(f"Starting automation for: {template_name}")
    
    # 1. FileMakerを前面に出す
    if not focus_filemaker():
        print("Error: FileMaker Pro window not found.")
        return False
    
    # 2. 画像認識でターゲット（例：[作成]ボタンや特定の入力エリア）を探してクリック
    # assets/ フォルダにテンプレート画像があることを想定
    template_path = os.path.join("assets", template_name)
    
    if click_template(template_path):
        print("Successfully clicked the target.")
        # 必要に応じて、クリック後のキー送信などを行う
        # pyautogui.hotkey('ctrl', 'v') 
        return True
    else:
        print("Failed to find the target UI element.")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        success = automate_field_import(sys.argv[1])
        sys.exit(0 if success else 1)
    else:
        print("Usage: python automate_action.py <template_image_name>")
        sys.exit(1)
