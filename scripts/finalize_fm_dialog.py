from pywinauto import Application, Desktop
import pyautogui
import time
import sys

def finalize_filemaker_dialog():
    """FileMakerの『データベースの管理』ダイアログでOKを押して保存終了する"""
    print("Finalizing FileMaker Database Management dialog...")
    try:
        # Desktop経由でウィンドウを探す
        all_windows = Desktop(backend="win32").windows()
        dialogs = [w for w in all_windows if w.is_visible() and ("データベースの管理" in w.window_text() or "Manage Database" in w.window_text())]
        
        if not dialogs:
            print("Target 'Manage Database' dialog not found. Skipping finalization.")
            return True
            
        target = dialogs[0]
        print(f"Targeting window for finalization: {target.window_text()}")
        
        target.set_focus()
        time.sleep(0.5)
        
        # OKボタン (Enter)
        pyautogui.press('enter')
        time.sleep(0.5)
        
        print("Sent 'Enter' (OK) to save and close.")
        return True
    except Exception as e:
        print(f"Error finalizing FileMaker: {e}")
        return False

if __name__ == "__main__":
    success = finalize_filemaker_dialog()
    sys.exit(0 if success else 1)
