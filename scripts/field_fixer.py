from pywinauto import Application, Desktop
import time
import sys
import json
import ctypes

def set_input_block(block=True):
    """ユーザーの入力をロック/解除する（Windows API）"""
    try:
        res = ctypes.windll.user32.BlockInput(block)
        if res == 0 and block:
            print("WARNING: Could not block input. Run as Administrator for full protection.")
        else:
            print(f"Input {'Locked' if block else 'Unlocked'}")
    except Exception as e:
        print(f"BlockInput error: {e}")

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
    for w in windows:
        title = w.window_text()
        if any(fk in title for fk in fallback_keywords) and not any(ek in title for ek in exclude_keywords):
            return w
    return None

def fix_single_field(dialog_spec, old_name, new_name, new_type=None, comment="AI最適化"):
    """単体フィールドの名前・型を修整する"""
    print(f"--- Fixing: {old_name} → {new_name} ---")
    
    try:
        # 1. フィールド一覧から対象を探して選択
        field_list = dialog_spec.child_window(auto_id="IDC_DEFFIELDS_FIELD_LIST", control_type="DataGrid")
        if not field_list.exists():
            grids = dialog_spec.descendants(control_type="DataGrid")
            if grids: field_list = grids[0]
            else: return False
        
        target_item = None
        for item in field_list.descendants(control_type="DataItem"):
            cells = item.children()
            if cells:
                name_texts = cells[0].descendants(control_type="Text")
                if name_texts and name_texts[0].window_text() == old_name:
                    target_item = item
                    break
        
        if not target_item:
            print(f"  > Error: Field '{old_name}' not found in list.")
            return False

        # 選択
        target_item.click_input()
        time.sleep(0.3)

        # 2. 名前を入力
        name_edit = dialog_spec.child_window(auto_id="IDC_DEFFIELDS_FIELDNAME_EDIT", control_type="Edit")
        name_edit.set_focus()
        name_edit.type_keys("^a{BACKSPACE}", with_spaces=True)
        name_edit.type_keys(new_name + "{ENTER}", with_spaces=True)
        time.sleep(0.3)
        
        # 3. 型を変更
        type_map = {
            "Text": "t", "テキスト": "t",
            "Number": "n", "数値": "n",
            "Date": "d", "日付": "d",
            "Time": "i", "時刻": "i",
            "Timestamp": "m", "タイムスタンプ": "m",
            "Container": "r", "オブジェクト": "r",
            "Calculation": "c", "計算": "c",
            "Summary": "s", "集計": "s"
        }
        if new_type:
            type_combo = dialog_spec.child_window(auto_id="IDC_FIELD_TYPE_MENU", control_type="ComboBox")
            key = type_map.get(new_type, "t")
            type_combo.type_keys(key + "{ENTER}")
            time.sleep(0.3)
        
        # 4. コメントを入力
        comment_edit = dialog_spec.child_window(auto_id="IDC_DEFFIELDS_FIELDCOMMENT_EDIT", control_type="Edit")
        comment_edit.set_focus()
        comment_edit.type_keys("^a{BACKSPACE}", with_spaces=True)
        comment_edit.type_keys(comment + "{ENTER}", with_spaces=True)
        time.sleep(0.3)
        
        # 5. 変更ボタンをクリック
        save_button = dialog_spec.child_window(auto_id="IDC_DEFFIELDS_SAVE_BUTTON", control_type="Button")
        
        if save_button.exists() and save_button.is_enabled():
            print("  > Change button is enabled. Clicking...")
            save_button.click_input()
        else:
            print("  > Change button is DISABLED or not found. Trying Alt+A as fallback...")
            dialog_spec.set_focus()
            dialog_spec.type_keys("%a")
        
        print(f"  > Applied change attempt: {old_name} → {new_name}")
        time.sleep(1.0)
        return True
    except Exception as e:
        print(f"  > Error fixing {old_name}: {e}")
        return False

def batch_fix(fix_list):
    """一括修整を実行する"""
    print(f"=== Starting Batch Fix (UIA Precise): {len(fix_list)} fields ===")
    set_input_block(True)
    try:
        app = Application(backend="uia").connect(path="FileMaker Pro.exe")
        dialog = find_manage_database_dialog(app)
        if not dialog:
            return {"success": False, "error": "Manage Database dialog not found"}
            
        dialog_spec = app.window(handle=dialog.handle)
        dialog_spec.set_focus()
        
        success_count = 0
        errors = []
        for fix in fix_list:
            old_name = fix.get("old_name", "")
            new_name = fix.get("new_name", old_name)
            new_type = fix.get("new_type", None)
            comment = fix.get("comment", "ClubMaker最適化")
            if fix_single_field(dialog_spec, old_name, new_name, new_type, comment):
                success_count += 1
            else:
                errors.append(old_name)
            time.sleep(0.5)
        
        print(f"=== Batch Fix Complete: {success_count}/{len(fix_list)} succeeded ===")
        return {"success": True, "total": len(fix_list), "succeeded": success_count, "errors": errors}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        set_input_block(False)

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        try:
            fixes = json.loads(sys.argv[1])
            result = batch_fix(fixes)
            print(json.dumps(result, ensure_ascii=False))
        except json.JSONDecodeError as e:
            print(json.dumps({"success": False, "error": f"Invalid JSON: {e}"}, ensure_ascii=False))
    else:
        sys.exit(1)
