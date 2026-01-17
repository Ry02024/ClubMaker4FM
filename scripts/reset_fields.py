from pywinauto import Application, Desktop
import time
import sys
import pyautogui

def find_manage_database_dialog(app):
    priority_keywords = ["データベースの管理", "Manage Database"]
    windows = app.windows()
    for w in windows:
        if any(pk in w.window_text() for pk in priority_keywords): return w
    for w in windows:
        for child in w.children():
            if any(pk in child.window_text() for pk in priority_keywords): return child
    return None

def reset_fields():
    print("=== Resetting Fields ===")
    try:
        app = Application(backend="uia").connect(path="FileMaker Pro.exe")
        dialog = find_manage_database_dialog(app)
        if not dialog:
            print("Dialog not found")
            return
        
        dialog_spec = app.window(handle=dialog.handle)
        dialog_spec.set_focus()
        
        # フィールドタブへ切り替え
        try:
            tab_field = dialog_spec.child_window(title="フィールド", control_type="TabItem")
            tab_field.click_input()
            time.sleep(0.5)
        except:
            dialog_spec.type_keys("%f")
            time.sleep(0.5)

        field_list = dialog_spec.child_window(auto_id="IDC_DEFFIELDS_FIELD_LIST", control_type="DataGrid")
        delete_button = dialog_spec.child_window(auto_id="IDC_DEFFIELDS_DELETE_BUTTON", control_type="Button")
        
        while True:
            items = field_list.descendants(control_type="DataItem")
            if not items:
                print("All fields deleted.")
                break
            
            field_name = "Unknown"
            cells = items[0].children()
            if cells:
                name_texts = cells[0].descendants(control_type="Text")
                if name_texts: field_name = name_texts[0].window_text()

            print(f"Deleting: {field_name}")
            # セルをクリックして選択
            if cells:
                cells[0].click_input()
            else:
                items[0].click_input()
            time.sleep(0.3)
            
            delete_button.click_input()
            time.sleep(0.5)
            
            # 消去の確認ダイアログ (Enterを送る)
            pyautogui.press('enter')
            time.sleep(0.5)
            
            # ダイアログが残っている場合のセーフティ
            try:
                for win in Desktop(backend="uia").windows():
                    if "FileMaker" in win.window_text() and win.control_type() == "Window":
                        # OK または 削除 ボタンを探す
                        for btn_text in ["OK", "削除", "はい"]:
                            btn = win.child_window(title=btn_text, control_type="Button")
                            if btn.exists():
                                btn.click_input()
                                time.sleep(0.3)
            except:
                pass

    except Exception as e:
        print(f"Error during reset: {e}")

if __name__ == "__main__":
    reset_fields()
