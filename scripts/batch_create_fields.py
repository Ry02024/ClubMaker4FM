import sys
import time
import json
import os
from pywinauto import Application, Desktop
import pyautogui
import fm_utils

def batch_create_fields(field_list):
    print(f"--- Batch Generate: {len(field_list)} fields ---", file=sys.stderr)
    
    fm_utils.start_overlay()
    fm_utils.set_input_block(True)
    
    success_count = 0
    try:
        dialog = fm_utils.find_manage_database_dialog()
        if not dialog:
            if not fm_utils.ensure_manage_database():
                return 0
            dialog = fm_utils.find_manage_database_dialog()
        
        dialog.set_focus()
        # 確実に「フィールド」タブを選択
        fm_utils.select_fields_tab(dialog)
        time.sleep(0.5)
        
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

        for i, f in enumerate(field_list):
            name = f.get("name")
            f_type = f.get("type", "Text")
            comment = f.get("comment", "")
            
            fm_utils.update_overlay(f"生成中: {i+1} / {len(field_list)} ({name})")
            print(f"  > [Step {i+1}] Creating '{name}' ({f_type})...", file=sys.stderr)
            
            try:
                # 1. 名前入力
                name_edit = dialog.child_window(auto_id="IDC_DEFFIELDS_FIELDNAME_EDIT", control_type="Edit")
                name_edit.set_focus()
                name_edit.set_text(name)
                time.sleep(0.2)
                
                # 入力検証
                actual_name = name_edit.window_text() or name_edit.get_value() or ""
                if actual_name != name:
                    print(f"  > Warning: set_text failed. Using manual typing...", file=sys.stderr)
                    name_edit.click_input()
                    pyautogui.hotkey('ctrl', 'a')
                    pyautogui.press('backspace')
                    pyautogui.typewrite(name)
                    time.sleep(0.2)

                # 2. 型選択
                key = type_map.get(f_type, "t")
                try:
                    type_combo = dialog.child_window(auto_id="IDC_FIELD_TYPE_MENU", control_type="ComboBox")
                    type_combo.set_focus()
                    type_combo.type_keys(key)
                except: pass
                
                # 3. 作成ボタンクリック
                # Alt+E (作成) は非常に強力で確実
                print(f"  > Sending Alt+E (Create)...", file=sys.stderr)
                # ボタン自体の存在を確認（デバッグ用）
                try:
                    create_btn = dialog.child_window(title_re=".*作成.*|.*Create.*", auto_id="IDC_DEFFIELDS_CREATE_BTN", control_type="Button")
                    if not create_btn.exists():
                        create_btn = dialog.child_window(title_re=".*作成.*|.*Create.*", control_type="Button")
                    
                    # 確実にボタンが見えるようにする
                    if create_btn.exists():
                         # ボタンを直接クリックする代わりにショートカットを送る（フォーカスが外れるのを防ぐため）
                         dialog.type_keys("%e")
                    else:
                         # 見つからない場合も強引に Alt+E
                         pyautogui.hotkey('alt', 'e')
                except:
                    pyautogui.hotkey('alt', 'e')
                
                # 4. 特殊なダイアログ対応
                time.sleep(0.8)
                
                # 計算/集計の場合は必ずダイアログが出る
                if f_type in ["Calculation", "Summary", "計算", "集計"]:
                    time.sleep(1.0)
                    # 前面のダイアログに Enter を送る
                    pyautogui.press('enter')
                    print(f"  > Dismissed extra dialog for {f_type}", file=sys.stderr)
                    time.sleep(0.5)
                else:
                    # 重複エラー等による警告ダイアログが出ているか確認 (タイトルが "FileMaker Pro")
                    try:
                        desktop = Desktop(backend="uia")
                        popup = desktop.window(title="FileMaker Pro", control_type="Window", top_level_only=True)
                        if popup.exists(timeout=0):
                             print(f"  > Alert detected: {popup.window_text()}. Dismissing...", file=sys.stderr)
                             popup.set_focus()
                             pyautogui.press('esc') # 警告を閉じる
                             time.sleep(0.5)
                    except: pass
                
                success_count += 1
                time.sleep(0.1)
                
            except Exception as e:
                print(f"  > Failed to create '{name}': {e}", file=sys.stderr)
                # ここでの不用意な Esc はメインダイアログを閉じてしまうため、何もしない
        
    finally:
        fm_utils.set_input_block(False)
        fm_utils.stop_overlay()
    
    return success_count

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            # 引数がファイルパスか、直接のJSON文字列か判定
            if os.path.exists(sys.argv[1]):
                with open(sys.argv[1], "r", encoding="utf-8") as f:
                    field_list = json.load(f)
            else:
                field_list = json.loads(sys.argv[1])
            
            if not isinstance(field_list, list):
                field_list = [field_list]
                
            count = batch_create_fields(field_list)
            print(json.dumps({"success": True, "count": count}))
        except Exception as e:
            print(json.dumps({"success": False, "error": str(e)}))
    else:
        print(json.dumps({"success": False, "error": "No input provided"}))
