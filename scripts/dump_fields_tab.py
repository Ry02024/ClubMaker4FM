from pywinauto import Application, Desktop
import time
import sys

def dump_fields_tab():
    app = Application(backend="uia").connect(path="FileMaker Pro.exe")
    windows = app.windows()
    target = None
    for w in windows:
        if "データベースの管理" in w.window_text():
            target = w
            break
    
    if target:
        dialog_spec = app.window(handle=target.handle)
        dialog_spec.set_focus()
        
        # フィールドタブをクリック
        tab_field = dialog_spec.child_window(title="フィールド", control_type="TabItem")
        tab_field.click_input()
        time.sleep(1.0)
        
        dialog_spec.print_control_identifiers()
    else:
        print("Dialog not found")

if __name__ == "__main__":
    dump_fields_tab()
