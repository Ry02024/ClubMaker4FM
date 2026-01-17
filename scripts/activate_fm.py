from pywinauto import Application, Desktop
import time
import sys

def activate_fm():
    try:
        print("Searching for FileMaker Pro...")
        target_handle = None
        all_windows = Desktop(backend="uia").windows()
        
        # まずメインウィンドウを探す
        main_win = None
        for w in all_windows:
            if w.class_name() == "FMPRO22.0APP":
                main_win = w
                break
        
        if main_win:
            print(f"Found Main Window: {main_win.window_text()}")
            if main_win.get_show_state() == 2:
                main_win.restore()
            main_win.set_focus()
            time.sleep(1)
        
        # ダイアログを探す
        found_dialog = None
        for w in all_windows:
            title = w.window_text()
            if any(kw in title for kw in ["データベースの管理", "Manage Database", "の管理", "Database"]):
                try:
                    if "FileMaker" in w.process_name():
                        found_dialog = w
                        break
                except: continue
        
        if found_dialog:
            print(f"Found Dialog: {found_dialog.window_text()}")
            if found_dialog.get_show_state() == 2:
                found_dialog.restore()
            found_dialog.set_focus()
            return True
        else:
            print("Dialog not found. Attempting to open...")
            if main_win:
                main_win.type_keys("^+d")
                time.sleep(2.0)
                # 再度全ウィンドウを確認
                new_windows = Desktop(backend="uia").windows()
                for w in new_windows:
                    if any(kw in w.window_text() for kw in ["データベースの管理", "Manage Database"]):
                        w.set_focus()
                        return True
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    activate_fm()
