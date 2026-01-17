import pyautogui
import os
import datetime
import time
from pywinauto import Application, Desktop

def focus_filemaker():
    print("Searching for FileMaker by process...")
    try:
        # FileMakerのプロセスに接続を試みる
        # タイトルではなく実行ファイル名で特定
        app = Application(backend="win32").connect(path="FileMaker Pro.exe")
        
        # プロセスに属する全ウィンドウを取得
        windows = app.windows()
        
        if windows:
            # 最前面にふさわしいメインのダイアログまたはウィンドウを探す
            for win in windows:
                if win.is_visible():
                    print(f"Focusing: {win.window_text()}")
                    win.set_focus()
                    # ダイアログ（データベースの管理など）を考慮して少し待つ
                    win.wait('ready', timeout=2)
                    time.sleep(1)
                    return True
        else:
            print("No visible windows found for FileMaker process.")
    except Exception as e:
        print(f"Focus error (Process connection): {e}")
        # フォールバック: Desktop全体から検索（ただしタイトルが'ClubMaker'でないもの）
        try:
            desktop = Desktop(backend="win32")
            for win in desktop.windows():
                title = win.window_text()
                if ("FileMaker" in title or "データベースの管理" in title) and "CLUB MAKER" not in title.upper():
                    print(f"Fallback focusing: {title}")
                    win.set_focus()
                    time.sleep(1)
                    return True
        except:
            pass
    return False

def capture_screen(save_dir="public/screenshots"):
    # キャプチャ前にFileMakerを前面へ
    focus_filemaker()
    
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    filepath = os.path.join(save_dir, filename)
    
    screenshot = pyautogui.screenshot()
    screenshot.save(filepath)
    print(f"Screenshot saved to: {filepath}")
    return filepath

if __name__ == "__main__":
    capture_screen()
