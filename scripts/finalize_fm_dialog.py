from pywinauto import Application, Desktop
import pyautogui
import time
import sys

def finalize_filemaker_dialog():
    """FileMakerの『データベースの管理』ダイアログでOKを押して保存終了する"""
    print("--- Finalize & Save FileMaker Changes ---")
    try:
        # 1. 警告ポップアップ（破棄・重複など）の徹底排除
        desktop = Desktop(backend="uia")
        retries = 3
        while retries > 0:
            try:
                # 「FileMaker Pro」というタイトルの小窓を探す
                popups = [w for w in desktop.windows(title="FileMaker Pro", control_type="Window", top_level_only=True) if w.is_visible()]
                if popups:
                    popup = popups[0]
                    text = "".join([t.window_text() for t in popup.descendants(control_type="Text")])
                    print(f"  > Popup detected: '{text[:30]}...'")
                    
                    if "破棄" in text or "Discard" in text:
                        # 破棄ダイアログが出ているなら「キャンセル」して本画面に戻る
                        btn = popup.child_window(title_re="キャンセル|Cancel", control_type="Button")
                        if btn.exists(): btn.click_input()
                        else: pyautogui.press('esc')
                    else:
                        # 重複警告などは Enter または Esc で閉じる
                        pyautogui.press('enter')
                    time.sleep(0.5)
                else: break
            except: break
            retries -= 1

        # 2. メインダイアログ（データベースの管理）を探す
        # fm_utils の循環参照を避けるため自前で探す
        all_windows = Desktop(backend="win32").windows()
        dialogs = [w for w in all_windows if w.is_visible() and any(k in w.window_text() for k in ["データベースの管理", "Manage Database"])]
        
        if not dialogs:
            print("  > Manage Database dialog not found. Done.")
            return True
            
        target_win = dialogs[0]
        target_win.set_focus()
        print(f"  > Finalizing: {target_win.window_text()}")
        
        # 3. OKボタンのクリック
        # UIA が最も確実だが、念のため複数の方法を試す
        try:
            uia_win = Desktop(backend="uia").window(handle=target_win.handle)
            # OKボタンは通常一番右下
            ok_btn = uia_win.child_window(title="OK", control_type="Button")
            if ok_btn.exists():
                ok_btn.click_input()
                print("  > Clicked 'OK' button via UIA.")
                time.sleep(1.0)
                return True
        except Exception as e:
            print(f"  > UIA OK click failed: {e}")

        # フォールバック: ショートカットキー・Enter
        print("  > Falling back to Enter key for OK.")
        pyautogui.press('enter')
        time.sleep(1.0)
        return True
        
    except Exception as e:
        print(f"  > ERROR in finalize: {e}")
        return False

if __name__ == "__main__":
    success = finalize_filemaker_dialog()
    sys.exit(0 if success else 1)
