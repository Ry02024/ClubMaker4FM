from pywinauto import Application, Desktop
import time
import sys
import json
import ctypes
import fm_utils  # Robust utility

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

def handle_confirmation_dialog(app):
    """保存確認またはエラーダイアログが表示されたら適切に処理する"""
    try:
        from pywinauto import Desktop
        # すべてのトップレベルウィンドウを確認
        for win in Desktop(backend="uia").windows():
            title = win.window_text()
            if "FileMaker" in title and win.control_type() == "Window":
                content_text = ""
                try:
                    texts = win.descendants(control_type="Text")
                    content_text = "".join([t.window_text() for t in texts])
                except:
                    pass

                # 1. 保存確認の場合
                if "保存" in content_text or "save" in content_text.lower():
                    save_btn = win.child_window(title="保存(S)", control_type="Button")
                    if save_btn.exists():
                        print(f"  > [Dialog: Save] Clicking '保存(S)'", file=sys.stderr)
                        save_btn.click_input()
                        time.sleep(0.5)
                        return True
                
                # 2. 名前重複エラーなどの警告の場合
                if "すでに使用されています" in content_text or "already in use" in content_text.lower():
                    ok_btn = win.child_window(title="OK", control_type="Button")
                    if ok_btn.exists():
                        print(f"  > [Dialog: Error] Duplicate name detected. Clicking 'OK' to skip.", file=sys.stderr)
                        ok_btn.click_input()
                        time.sleep(0.5)
                        return "error_duplicate"

                # 3. その他の一般的な OK 案内の場合
                ok_btn = win.child_window(title="OK", control_type="Button")
                if ok_btn.exists():
                    print(f"  > [Dialog: Info] Clicking 'OK'", file=sys.stderr)
                    ok_btn.click_input()
                    time.sleep(0.5)
                    return True
                    
    except Exception as e:
        pass
    return False

def fix_single_field(dialog_spec, old_name, new_name, new_type=None, comment="AI最適化"):
    """単體フィールドの名前・型を修整する"""
    print(f"\n[Fixing] {old_name} -> {new_name}", file=sys.stderr)
    
    handle_confirmation_dialog(None)

    try:
        # 1. フィールド一覧から対象を探す
        field_list = dialog_spec.child_window(auto_id="IDC_DEFFIELDS_FIELD_LIST", control_type="DataGrid")
        if not field_list.exists():
            return False
        
        target_item = None
        items = field_list.descendants(control_type="DataItem")
        for item in items:
            cells = item.children()
            if cells:
                name_texts = cells[0].descendants(control_type="Text")
                if name_texts and name_texts[0].window_text() == old_name:
                    target_item = item
                    break
        
        if not target_item:
            print(f"  > Error: Field '{old_name}' not found in list.", file=sys.stderr)
            return False

        # 2. 選択処理
        print(f"  > Selecting field: {old_name}", file=sys.stderr)
        cells = target_item.children()
        if cells:
             cells[0].click_input() 
        else:
             target_item.click_input()
        time.sleep(0.5)

        # 3. 状態確認
        name_edit = dialog_spec.child_window(auto_id="IDC_DEFFIELDS_FIELDNAME_EDIT", control_type="Edit")
        change_button = dialog_spec.child_window(auto_id="IDC_DEFFIELDS_SAVE_BUTTON", control_type="Button")
        
        if name_edit.get_value() != old_name:
            print(f"  > Selection mismatch (Expected: {old_name}, Got: {name_edit.get_value()}). Retrying click...", file=sys.stderr)
            target_item.click_input()
            time.sleep(0.5)

        # 4. 名前入力
        print(f"  > Entering new name: {new_name}", file=sys.stderr)
        name_edit.set_focus()
        name_edit.type_keys("^a{BACKSPACE}", with_spaces=True)
        time.sleep(0.2)
        name_edit.type_keys(new_name, with_spaces=True)
        time.sleep(0.3)
        
        # 5. 型変更
        if new_type:
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
            type_combo = dialog_spec.child_window(auto_id="IDC_FIELD_TYPE_MENU", control_type="ComboBox")
            key = type_map.get(new_type, "t")
            type_combo.type_keys(key + "{ENTER}")
            time.sleep(0.3)
        
        # 6. コメント入力
        comment_edit = dialog_spec.child_window(auto_id="IDC_DEFFIELDS_FIELDCOMMENT_EDIT", control_type="Edit")
        comment_edit.set_focus()
        comment_edit.type_keys("^a{BACKSPACE}", with_spaces=True)
        comment_edit.type_keys(comment, with_spaces=True)
        time.sleep(0.3)
        
        # 7. 変更ボタン
        print(f"  > Finalizing change...", file=sys.stderr)
        dialog_spec.type_keys("%a")
        time.sleep(0.5)
        
        handle_confirmation_dialog(None)

        if change_button.exists() and change_button.is_enabled():
             print("  > Button still enabled. Direct click...", file=sys.stderr)
             change_button.click_input()
             time.sleep(0.5)
             handle_confirmation_dialog(None)
            
        print(f"  > Done: {old_name} -> {new_name}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"  > Exception: {e}", file=sys.stderr)
        return False

def batch_fix(fix_list):
    """一括修整を実行する"""
    print(f"=== Starting Batch Fix (Selection Pattern): {len(fix_list)} fields ===", file=sys.stderr)
    fm_utils.set_input_block(True)
    fm_utils.start_overlay()
    try:
        app = Application(backend="uia").connect(path="FileMaker Pro.exe")
        
        success_count = 0
        errors = []
        
        for i, fix in enumerate(fix_list):
            if not fix.get("should_fix", True): continue
            
            old_name = fix.get("old_name", "")
            new_name = fix.get("new_name", old_name)
            
            # Update Overlay
            fm_utils.update_overlay(f"【{i+1}/{len(fix_list)}】 フィールド修整中...\n{old_name} ➔ {new_name}")
            
            if not fm_utils.ensure_manage_database():
                print("CRITICAL: Could not recover Manage Database dialog. Aborting batch.", file=sys.stderr)
                break
                
            dialog = find_manage_database_dialog(app)
            if not dialog:
                print("Error: Dialog open but handle not found?", file=sys.stderr)
                errors.append(fix.get("old_name"))
                continue
                
            dialog_spec = app.window(handle=dialog.handle)
            dialog_spec.set_focus()

            new_type = fix.get("new_type", None)
            comment = fix.get("comment", "ClubMaker最適化")
            
            if fix_single_field(dialog_spec, old_name, new_name, new_type, comment):
                success_count += 1
            else:
                errors.append(old_name)
            time.sleep(1.0) 
        
        fm_utils.update_overlay("完了しました！")
        time.sleep(1.5)
        return {"success": True, "total": len(fix_list), "succeeded": success_count, "errors": errors}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        fm_utils.stop_overlay()
        fm_utils.set_input_block(False)

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        try:
            fixes = json.loads(sys.argv[1])
            result = batch_fix(fixes)
            print(json.dumps(result, ensure_ascii=True))
        except:
            sys.exit(1)
    else:
        sys.exit(1)
