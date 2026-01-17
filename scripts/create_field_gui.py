from pywinauto import Application, Desktop
import pyautogui
import pyperclip
import time
import sys
import os

def focus_filemaker_dialog():
    """タイトルを問わず、FileMakerの最前面のウィンドウを特定する"""
    print("Searching for FileMaker windows...")
    try:
        # FileMakerプロセスに接続
        app = Application(backend="win32").connect(path="FileMaker Pro.exe")
        
        # プロセスに属する全ウィンドウを取得し、可視かつタイトルのあるものを探す
        windows = app.windows()
        visible_windows = [w for w in windows if w.is_visible() and w.window_text()]
        
        if not visible_windows:
            print("No visible FileMaker windows found.")
            return False
            
        # 最前面にある（リストの先頭に近い）ウィンドウをターゲットにする
        # ダイアログが開いていればそれが選ばれるはず
        target = visible_windows[0]
        print(f"Targeting window: {target.window_text()}")
        
        target.set_focus()
        time.sleep(0.5)
        
        # フィールド名入力欄へ移動 (Alt+F は日本語版の定石)
        pyautogui.hotkey('alt', 'f')
        time.sleep(0.3)
        return True
    except Exception as e:
        print(f"Error connecting to FileMaker: {e}")
        return False

def create_field_gui(name, field_type="テキスト", comment="AI生成"):
    print(f"--- GUI Create Start: {name} ---")
    
    if not focus_filemaker_dialog():
        return False

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.5

    # 1. 既存文字のクリア
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('backspace')
    
    # 2. フィールド名 (日本語対応のためコピペ)
    pyperclip.copy(name)
    pyautogui.hotkey('ctrl', 'v')
    print(f"  > Name entered: {name}")
    
    # 3. タイプ選択へ移動 (Tab)
    pyautogui.press('tab')
    
    # 4. タイプ選択 (ショートカットキー)
    # 日本語版ショートカット: T(テキスト), N(数値), D(日付)...
    type_map = {
        "テキスト": "t", "数値": "n", "日付": "d", "時刻": "i",
        "タイムスタンプ": "m", "オブジェクト": "r", "計算": "c", "集計": "s"
    }
    key = type_map.get(field_type, "t")
    pyautogui.write(key)
    print(f"  > Type selected: {field_type} ({key})")
    
    # 5. コメント欄へ移動
    pyautogui.press('tab')
    
    # 6. コメント (コピペ)
    pyperclip.copy(comment)
    pyautogui.hotkey('ctrl', 'v')
    print(f"  > Comment entered: {comment}")
    
    # 7. 実行 (Alt+E は『作成』ボタン)
    pyautogui.hotkey('alt', 'e')
    print("  > Sent 'Create' command (Alt+E)")
    
    time.sleep(0.5)
    return True

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        name = sys.argv[1]
        field_type = sys.argv[2] if len(sys.argv) > 2 else "テキスト"
        comment = sys.argv[3] if len(sys.argv) > 3 else "AI生成"
        
        success = create_field_gui(name, field_type, comment)
        sys.exit(0 if success else 1)
    else:
        print("Usage: python create_field_gui.py <name> [type] [comment]")
        sys.exit(1)
