from pywinauto import Application, Desktop
import pyautogui
import pyperclip
import time
import sys
import os
import fm_utils  # Robust utility

import ctypes

def create_field_gui(name, field_type="Text", comment=""):
    print(f"--- GUI Robust Generate: {name} ---")
    
    # 入力をロック
    fm_utils.set_input_block(True)
    
    try:
        # Robust Recovery: Ensure we are on the right screen
        if not fm_utils.ensure_manage_database():
            print("CRITICAL: Failed to recover Manage Database dialog.")
            return False

        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5

        # 0. Ensure focus on the dialog (ensure_manage_database does this, but good to be sure before typing)
        # Note: ensure_manage_database leaves the dialog focused.
        
        # Navigate to Field Name box (Alt+F is standard)
        pyautogui.hotkey('alt', 'f')
        time.sleep(0.3)

        # 1. 既存文字のクリア
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('backspace')
        time.sleep(0.3)
        
        # 2. フィールド名入力
        pyperclip.copy(name)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.3)
        
        # 3. 型選択
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
            # 集計設定ダイアログ
            # 集計フィールドは「OK」を押すだけでは済まない場合があるが（集計対象選択）、
            # デフォルトで一番上のフィールドが集計されることを期待してEnter
            pyautogui.press('enter')
            print("  > Closed summary dialog.")

        time.sleep(0.8)
        
        # 6. Post-Action Check: Did a warning pop up? (e.g., Duplicate Name)
        # If so, fm_utils.ensure_manage_database() in the NEXT loop iteration 
        # (or explicitly here) should handle it by cancelling/closing.
        # But we want to return success/fail.
        # For now, we assume success if no crash. Strict blocking happens at START.
        
        return True
    except Exception as e:
        print(f"Error in create_field_gui: {e}")
        return False
    finally:
        fm_utils.set_input_block(False)

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
