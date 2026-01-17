from pywinauto import Application, Desktop
import pyautogui
import pyperclip
import time
import sys
import os

import ctypes

def set_input_block(block=True):
    """ユーザーの入力をロック/解除する（Windows API）"""
    try:
        # ※ BlockInputは管理者権限で実行されていない場合は動作しません
        res = ctypes.windll.user32.BlockInput(block)
        if res == 0 and block:
            print("WARNING: Could not block input. Please run as Administrator if you want to prevent manual interference.")
        else:
            print(f"Input {'Locked' if block else 'Unblocked'}")
    except Exception as e:
        print(f"BlockInput error: {e}")

def focus_filemaker_dialog():
    """『データベースの管理』ダイアログを特定する。警告モーダルが出ていれば排除を試みる。"""
    print("Finding FileMaker dialog with recovery...")
    try:
        from pywinauto import Application, Desktop
        
        # リトライループ
        for attempt in range(3):
            all_windows = Desktop(backend="win32").windows()
            
            # 1. 目的のダイアログを探す
            mng_dialogs = [w for w in all_windows if w.is_visible() and ("データベースの管理" in w.window_text() or "Manage Database" in w.window_text())]
            
            if mng_dialogs:
                target = mng_dialogs[0]
                # もし「他のウィンドウ」が手前にある場合、それは恐らくエラーダイアログ
                # 但し自分自身より手前にあるものを特定するのは難しいため、
                # FileMakerプロセスの別ウィンドウ（小さな警告等）がないかチェック
                fm_windows = [w for w in all_windows if w.is_visible() and "FileMaker" in w.window_text() and w not in mng_dialogs]
                
                if fm_windows:
                    print(f"  > Notice: Potential modal detected: {fm_windows[0].window_text()}")
                    fm_windows[0].set_focus()
                    time.sleep(0.3)
                    pyautogui.press('esc')
                    time.sleep(0.5)
                    continue # 再検索

                print(f"  > Targeting: {target.window_text()}")
                target.set_focus()
                time.sleep(1.0)
                
                # フィールド名入力欄へ移動 (Alt+F: フィールド名)
                pyautogui.hotkey('alt', 'f')
                time.sleep(0.5)
                return True
            else:
                # 警告ダイアログだけが出ているケースへの対策
                fm_others = [w for w in all_windows if w.is_visible() and "FileMaker" in w.window_text()]
                if fm_others:
                    print(f"  > Managing dialog lost. Found: {fm_others[0].window_text()}. Trying to Esc...")
                    fm_others[0].set_focus()
                    time.sleep(0.3)
                    pyautogui.press('esc')
                    time.sleep(0.5)
                else:
                    print("  > FileMaker window not found at all.")
                    return False
        return False
    except Exception as e:
        print(f"Error focusing FileMaker: {e}")
        return False

def create_field_gui(name, field_type="Text", comment=""):
    print(f"--- GUI Robust Generate: {name} ---")
    
    # 入力をロック
    set_input_block(True)
    
    try:
        if not focus_filemaker_dialog():
            return False

        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5

        # 1. 既存文字のクリア
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('backspace')
        time.sleep(0.3)
        
        # 2. フィールド名入力
        pyperclip.copy(name)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.3)
        
        # 3. 型選択 (計算/集計のみ明示的に行う、他はデフォルト＝テキストに期待)
        # ユーザー要望に従い、極力シンプルにする
        if field_type in ["Calculation", "Summary", "計算", "集計"]:
            pyautogui.press('tab')
            time.sleep(0.2)
            key = "c" if field_type in ["Calculation", "計算"] else "s"
            pyautogui.write(key)
            time.sleep(0.2)
        
        # 4. 作成(Alt+E)
        pyautogui.hotkey('alt', 'e')
        print(f"  > Sent Create (Alt+E)")
        
        # 5. 計算ダイアログ等の特別な後処理
        if field_type in ["Calculation", "計算"]:
            time.sleep(1.5)
            # 数式入力を求められたら空文字を入れる
            pyperclip.copy('""')
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.3)
            pyautogui.press('enter')
            print("  > Closed calculation dialog.")
        elif field_type in ["Summary", "集計"]:
            time.sleep(1.5)
            pyautogui.press('enter')
            print("  > Closed summary dialog.")

        time.sleep(0.8)
        return True
    finally:
        set_input_block(False)

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        name = sys.argv[1]
        field_type = sys.argv[2] if len(sys.argv) > 2 else "Text"
        comment = sys.argv[3] if len(sys.argv) > 3 else "ClubMakerによる自動生成"
        
        success = create_field_gui(name, field_type, comment)
        sys.exit(0 if success else 1)
    else:
        print("Usage: python create_field_gui.py <name> [type] [comment]")
        sys.exit(1)
