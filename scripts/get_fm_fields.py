from pywinauto import Application, Desktop
import json
import sys
import time
import pyautogui

def find_manage_database_dialog(app):
    """fm_utilsの共通関数を使用する"""
    return fm_utils.find_manage_database_dialog()

import fm_utils

def get_existing_fields():
    fields_dict = {}  # 重複を避けるため名前をキーにする
    total_expected = 0
    fm_utils.start_overlay()
    fm_utils.update_overlay("FileMakerから全フィールドを読み取っています...")
    fm_utils.set_input_block(True)
    
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

        # dialog は Desktop オブジェクトで見つけた pywinauto wrapper
        dialog_spec = dialog
        dialog_spec.set_focus()
        
        # 「フィールド」タブ項目を直接クリックして切り替え
        try:
            tab_control = dialog_spec.child_window(control_type="Tab")
            fields_tab = tab_control.child_window(title="フィールド", control_type="TabItem")
            if fields_tab.exists():
                fields_tab.click_input()
                time.sleep(0.5)
        except:
            dialog_spec.type_keys("%f") 
            time.sleep(0.5)

        # 1. フィールド総数を取得 (Win32バックエンド併用で高速化)
        count_label = ""
        try:
            from pywinauto import Desktop as DesktopW32
            win_w32 = DesktopW32(backend="win32").window(handle=dialog_spec.handle)
            # 全コントロールから「フィールド」を含むものを探す
            for ctrl in win_w32.descendants():
                t = ctrl.window_text()
                if t and "フィールド" in t and any(char.isdigit() for char in t):
                    count_label = t
                    break
        except: pass

        if not count_label:
            # UIAでのフォールバック
            try:
                for el in dialog_spec.descendants(control_type="Text"):
                    t = el.window_text()
                    if t and "フィールド" in t and any(char.isdigit() for char in t):
                        count_label = t
                        break
            except: pass

        total_expected = 0
        if count_label:
            import re
            # 「13 / 26 フィールド」のような形式を考慮し、最も大きい数字または最後尾の数字を取得
            matches = re.findall(r'(\d+)', count_label)
            if matches:
                total_expected = int(matches[-1]) 
                print(f"  > Detected total (last match): {total_expected} from '{count_label}'", file=sys.stderr)
        
        if total_expected == 0:
             print("  > Warning: Could not detect total field count. Using safety scan limit (50 steps buffer).", file=sys.stderr)
        
        # フィールドリスト (DataGrid) を取得
        field_list = dialog_spec.child_window(auto_id="IDC_DEFFIELDS_FIELD_LIST", control_type="DataGrid")
        if not field_list.exists():
            grids = dialog_spec.descendants(control_type="DataGrid")
            if grids: field_list = grids[0]
            else: return {"success": False, "error": "Field list not found."}

        # 2. スクロールしながら取得
        field_list.set_focus()
        pyautogui.press('home')
        time.sleep(0.3)

        # 取得したフィールドの順序と内容を保持
        ordered_fields = []
        
        # ユーザーの要望: 「1/13」のようにリアルタイムで1件ずつカウントを表示
        for i in range(total_expected if total_expected > 0 else 100):
            current_count = i + 1
            fm_utils.update_overlay(f"読み取り中: {current_count} / {total_expected if total_expected > 0 else '??'}")
            
            # 再取得して現在のDataItem（フォーカスされている可能性があるもの）を特定
            try:
                # 画面に見えているアイテムの中から、現在のアクティブなものを推測するか、
                # 単に現在のDataGridの状態から情報を抜く
                # 1件ずつ移動するので、descendantsの最初の数件に目的のデータがあるはず
                items = dialog_spec.child_window(auto_id="IDC_DEFFIELDS_FIELD_LIST", control_type="DataGrid").descendants(control_type="DataItem")
                
                # 現在の「行」を特定する（多くの場合、一番上の見えるアイテムか、選択されているもの）
                # ここでは「新しく見つかった名前」を順に溜めていく
                for item in items:
                    try:
                        cells = item.children()
                        if not cells: continue
                        
                        # 名前
                        n_nodes = cells[0].descendants(control_type="Text")
                        n_text = n_nodes[0].window_text() if n_nodes else cells[0].window_text()
                        
                        # タイプ
                        t_text = ""
                        if len(cells) > 1:
                            t_nodes = cells[1].descendants(control_type="Text")
                            t_text = t_nodes[0].window_text() if t_nodes else cells[1].window_text()
                        
                        if n_text and not any(f["name"] == n_text for f in ordered_fields):
                            if not any(k in n_text for k in ["名前", "タイプ", "オプション"]): # ヘッダ除外
                                ordered_fields.append({"name": n_text, "type": t_text})
                                break # 1つ見つかればこの行の処理はOK
                    except: continue
            except: pass

            # 次へ移動
            if current_count < total_expected:
                pyautogui.press('down')
                time.sleep(0.05) # 短い待機でリズムを作る
            else:
                break

        fm_utils.update_overlay(f"読み取り完了: {len(ordered_fields)}件")
        return {"success": True, "fields": ordered_fields}

    except Exception as e:
        import traceback
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}
    finally:
        fm_utils.set_input_block(False)
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
