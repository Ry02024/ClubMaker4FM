from pywinauto import Application, Desktop
import json
import sys
import time

def find_manage_database_dialog(app):
    """FileMakerの「データベースの管理」ダイアログを探す(正確なマッチング)"""
    # 優先キーワード
    priority_keywords = ["データベースの管理", "Manage Database"]
    fallback_keywords = ["Database", "の管理"]
    exclude_keywords = ["レイアウト", "Layout", "スクリプト", "Script"]
    
    # 1. 最上位ウィンドウから優先キーワードで探す
    windows = app.windows()
    for w in windows:
        title = w.window_text()
        if any(pk in title for pk in priority_keywords):
            print(f"Found priority dialog as top window: {title}", file=sys.stderr)
            return w

    # 2. メインウィンドウの子から優先キーワードで探す
    for w in windows:
        for child in w.children():
            title = child.window_text()
            if any(pk in title for pk in priority_keywords):
                print(f"Found priority dialog as child: {title}", file=sys.stderr)
                return child

    # 3. フォールバック (ただし除外キーワードを含むものは避ける)
    for w in windows:
        title = w.window_text()
        if any(fk in title for fk in fallback_keywords):
            if not any(ek in title for ek in exclude_keywords):
                print(f"Found fallback dialog as top window: {title}", file=sys.stderr)
                return w
                
    for w in windows:
        for child in w.children():
            title = child.window_text()
            if any(fk in title for fk in fallback_keywords):
                if not any(ek in title for ek in exclude_keywords):
                    print(f"Found fallback dialog as child: {title}", file=sys.stderr)
                    return child
                    
    return None

import fm_utils

def get_existing_fields():
    fields = []
    fm_utils.start_overlay()
    fm_utils.update_overlay("FileMakerからフィールドを読み取っています...")
    
    try:
        # Try to connect
        try:
            app = Application(backend="uia").connect(path="FileMaker Pro.exe")
        except:
            return {"success": False, "error": "Could not connect to FileMaker Pro."}

        # Auto-open logic disabled for stability (User request to revert)
        # if not fm_utils.ensure_manage_database():
        #      return {"success": False, "error": "Could not open 'Manage Database' dialog."}

        dialog = find_manage_database_dialog(app)

        if not dialog:
            return {"success": False, "error": "Manage Database dialog not found."}

        dialog_spec = app.window(handle=dialog.handle)
        dialog_spec.set_focus()
        
        # 「フィールド」タブ項目を直接クリックして切り替え
        try:
            tab_field = dialog_spec.child_window(title="フィールド", control_type="TabItem")
            if tab_field.exists():
                tab_field.click_input()
                time.sleep(0.5)
        except:
            # フォールバック: Alt+F
            dialog_spec.type_keys("%f") 
            time.sleep(0.5)

        # フィールドリスト (DataGrid) を取得
        # DataGridをダイアログ直下から探索
        field_list = dialog_spec.child_window(auto_id="IDC_DEFFIELDS_FIELD_LIST", control_type="DataGrid")
        
        if not field_list.exists():
            # DataGridを全探索
            grids = dialog_spec.descendants(control_type="DataGrid")
            if grids:
                field_list = grids[0]
            else:
                return {"success": False, "error": "Field list (DataGrid) not found. Please ensure Fields tab is selected."}

        items = field_list.descendants(control_type="DataItem")
        
        for item_wrapper in items:
            cells = item_wrapper.children()
            if len(cells) >= 2:
                name_text = ""
                type_text = ""
                
                # 名前 (1列目)
                name_texts = cells[0].descendants(control_type="Text")
                if name_texts:
                    name_text = name_texts[0].window_text()
                
                # タイプ (2列目)
                type_texts = cells[1].descendants(control_type="Text")
                if type_texts:
                    type_text = type_texts[0].window_text()
                
                if name_text:
                    fields.append({"name": name_text, "type": type_text})
        
        fm_utils.update_overlay(f"読み取り完了: {len(fields)}件")
        time.sleep(1.0)
        return {"success": True, "fields": fields}

    except Exception as e:
        import traceback
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}
    finally:
        fm_utils.stop_overlay()

if __name__ == "__main__":
    result = get_existing_fields()
    
    # Save to data/current_fields.json
    try:
        import os
        data_dir = os.path.join(os.getcwd(), 'data')
        os.makedirs(data_dir, exist_ok=True)
        file_path = os.path.join(data_dir, 'current_fields.json')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving to file: {e}", file=sys.stderr)

    # Still print to stdout for other scripts to use
    # use ensure_ascii=True to safely pass unicode via stdout on Windows
    print(json.dumps(result, ensure_ascii=True))
