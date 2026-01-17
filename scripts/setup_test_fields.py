from pywinauto import Application, Desktop
import time
import sys

def find_manage_database_dialog(app):
    """FileMakerの「データベースの管理」ダイアログを探す(正確なマッチング)"""
    priority_keywords = ["データベースの管理", "Manage Database"]
    fallback_keywords = ["Database", "の管理"]
    exclude_keywords = ["レイアウト", "Layout", "スクリプト", "Script"]
    
    windows = app.windows()
    for w in windows:
        title = w.window_text()
        if any(pk in title for pk in priority_keywords):
            return w
    for w in windows:
        for child in w.children():
            if any(pk in child.window_text() for pk in priority_keywords):
                return child
    return None

def create_fields(fields_to_create):
    try:
        app = Application(backend="uia").connect(path="FileMaker Pro.exe")
        dialog = find_manage_database_dialog(app)
        if not dialog:
            print("Manage Database dialog not found.")
            return False
            
        dialog_spec = app.window(handle=dialog.handle)
        dialog_spec.set_focus()
        
        # フィールド名入力欄
        name_edit = dialog_spec.child_window(auto_id="IDC_DEFFIELDS_FIELDNAME_EDIT", control_type="Edit")
        # 作成ボタン (IDC_DEFFIELDS_CREATE_BUTTON) or Name "作成"
        create_button = dialog_spec.child_window(auto_id="IDC_DEFFIELDS_CREATE_BUTTON", control_type="Button")
        
        for name, ftype in fields_to_create:
            print(f"Creating field: {name} ({ftype})")
            name_edit.set_focus()
            name_edit.type_keys("^a{BACKSPACE}", with_spaces=True)
            name_edit.type_keys(name, with_spaces=True)
            
            # 型選択 (簡易)
            type_map = {"Text": "t", "Number": "n", "Date": "d"}
            type_combo = dialog_spec.child_window(auto_id="IDC_FIELD_TYPE_MENU", control_type="ComboBox")
            type_combo.type_keys(type_map.get(ftype, "t") + "{ENTER}")
            
            time.sleep(0.3)
            create_button.click_input()
            time.sleep(0.8)
            
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_fields = [
        ("StaffID", "Number"),
        ("StaffName", "Text"),
        ("Role", "Text"),
        ("ContactInfo", "Text"),
        ("スタッフ_ID", "Text"),
        ("スタッフ_ID_主キー", "Text")
    ]
    create_fields(test_fields)
