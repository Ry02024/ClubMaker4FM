import sys
import time
import json
import os
from pywinauto import Application, Desktop
import pyautogui
import fm_utils

def batch_create_fields(field_list):
    print(f"--- Batch Generate: {len(field_list)} fields (Simple Mode) ---", file=sys.stderr)
    
    fm_utils.start_overlay()
    fm_utils.set_input_block(True)
    
    success_count = 0
    
    try:
        # 1. ダイアログ取得 (シンプルに)
        dialog = fm_utils.find_manage_database_dialog()
        if not dialog:
            # 見つからなければ1回だけ開く試行
            if fm_utils.ensure_manage_database():
                dialog = fm_utils.find_manage_database_dialog()
        
        if not dialog:
            print("Error: Manage Database dialog not found.", file=sys.stderr)
            return 0

        dialog.set_focus()
        fm_utils.select_fields_tab(dialog)
        time.sleep(0.5)

        # 2. 単純ループ
        for i, f in enumerate(field_list):
            name = f.get("name")
            f_type = f.get("type", "Text") # 型選択は一応残すが、基本テキストでもOKなら無視でも可
            
            fm_utils.update_overlay(f"生成中: {i+1} / {len(field_list)} ({name})")
            print(f"  > Creating '{name}'...", file=sys.stderr)
            
            try:
                # 名前入力欄 (IDC_DEFFIELDS_FIELDNAME_EDIT)
                edit = dialog.child_window(auto_id="IDC_DEFFIELDS_FIELDNAME_EDIT", control_type="Edit")
                edit.set_focus()
                edit.set_text(name)
                
                # 型選択 (コンボボックス)
                # ユーザー指示:「名前入力」→「テキスト型にリセット」→「Shirft+Alt+E (作成)」
                # これにより計算フィールドなどが選択された状態を防ぐ
                try:
                    cb = dialog.child_window(auto_id="IDC_FIELD_TYPE_MENU", control_type="ComboBox")
                    cb.type_keys("t") # Text
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Warning: Failed to reset type to Text: {e}", file=sys.stderr)

                # 作成 (Shift+Alt+E)
                # ユーザー指摘により Shift+Alt+E に変更（以前のボタンクリックは誤動作の原因だった）
                print(f"  > Sending Shift+Alt+E (Create)...", file=sys.stderr)
                pyautogui.hotkey('shift', 'alt', 'e')
                
                # 少し待つ
                time.sleep(0.5)

                # 計算/集計ダイアログや重複エラーが出たら Enter/Esc で閉じる (最低限の保護)
                if f_type in ["Calculation", "Summary", "計算", "集計"]:
                    time.sleep(0.5)
                    pyautogui.press('enter')
                
                success_count += 1

            except Exception as e:
                print(f"  > Error creating {name}: {e}", file=sys.stderr)
                # エラー時も停止せず次へ
    
    finally:
        fm_utils.set_input_block(False)
        fm_utils.stop_overlay()
    
    return success_count

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            if os.path.exists(sys.argv[1]):
                with open(sys.argv[1], "r", encoding="utf-8") as f:
                    field_list = json.load(f)
            else:
                field_list = json.loads(sys.argv[1])
            if not isinstance(field_list, list): field_list = [field_list]
                
            count = batch_create_fields(field_list)
            print(json.dumps({"success": True, "count": count}))
        except Exception as e:
            print(json.dumps({"success": False, "error": str(e)}))
    else:
        print(json.dumps({"success": False, "error": "No input provided"}))
