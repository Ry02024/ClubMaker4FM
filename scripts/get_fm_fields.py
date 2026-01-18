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
        # 1. ダイアログが確実に前面にあるようにする
        if not fm_utils.ensure_manage_database():
             return {"success": False, "error": "Could not open 'Manage Database' dialog."}
             
        dialog = fm_utils.find_manage_database_dialog()
        if not dialog:
            return {"success": False, "error": "Manage Database dialog not found."}

        dialog.set_focus()
        
        # 2. 「フィールド」タブを確実に選択
        if not fm_utils.select_fields_tab(dialog):
            return {"success": False, "error": "Could not select 'Fields' tab."}
        
        time.sleep(0.5)
        dialog_spec = dialog

        # 1. フィールド総数を取得
        total_expected = -1
        import re
        try:
            # 「XXX フィールド」を探す
            # 英語: "0 fields", "3 fields" etc
            # 日本語: "0 フィールド", "3 フィールド"
            for el in dialog_spec.descendants(control_type="Text"):
                t = (el.window_text() or "").strip()
                if "フィールド" in t or "Field" in t or "field" in t:
                    m = re.search(r'(\d+)', t)
                    if m:
                        val = int(m.group(1))
                        # あまりに大きい数字は誤検出の可能性があるので除外するなどしてもよいが、一旦信じる
                        total_expected = val
                        print(f"  > Detected total_expected: {total_expected} from '{t}'", file=sys.stderr)
                        break
        except: pass
        
        # 2. スクロールしながら取得
        grid = dialog_spec.child_window(auto_id="IDC_DEFFIELDS_FIELD_LIST", control_type="DataGrid")
        grid.set_focus()
        pyautogui.press('home')
        time.sleep(0.5)

        # 取得したフィールドの順序と内容を保持
        ordered_fields = []
        
        # 最大ループ回数を決定
        if total_expected == 0:
             # 明示的に0件とわかった場合 -> ほぼループ不要だが、念のため2回
             max_loops = 2
        elif total_expected > 0:
             # 件数がわかっている場合 -> ある程度余裕を持たせる
             max_loops = max(total_expected * 2, 20)
        else:
             # 検出失敗 (-1) の場合 -> 安全策で多めに回す（以前の挙動に近い）
             max_loops = 50
        
        for i in range(max_loops):
            fm_utils.update_overlay(f"読み取り中: {len(ordered_fields)} / {total_expected if total_expected > 0 else '??'}")
            
            # 現在見えている全アイテムから、新規フィールドを探す
            try:
                # リフレッシュ
                items = grid.descendants(control_type="DataItem")
                if not items: items = grid.children(control_type="DataItem")
                
                print(f"  > [Loop {i}] Items visible: {len(items)}, Collected: {len(ordered_fields)}", file=sys.stderr)
                
                found_new_in_any_item = False
                for item in items:
                    try:
                        # Item自体のテキストからも名前を推測（フォールバック）
                        it_text = (item.window_text() or "").strip()
                        
                        cells = item.children()
                        n_text = ""
                        t_text = ""
                        
                        if len(cells) >= 1:
                            # Cell 0 から名前
                            n_nodes = cells[0].descendants(control_type="Text")
                            if n_nodes:
                                n_text = " ".join([n.window_text() for n in n_nodes if n.window_text()]).strip()
                            if not n_text:
                                n_text = (cells[0].window_text() or "").strip()
                        
                        if len(cells) >= 2:
                            # Cell 1 から型
                            t_nodes = cells[1].descendants(control_type="Text")
                            if t_nodes:
                                t_text = " ".join([n.window_text() for n in t_nodes if n.window_text()]).strip()
                            if not t_text:
                                t_text = (cells[1].window_text() or "").strip()

                        # もし Cell から取れなかった場合、Whole Text から推測 (並べ替え 名前 型 ...)
                        if not n_text and "並べ替え" in it_text:
                            parts = it_text.split()
                            if len(parts) >= 3:
                                n_text = parts[1]
                                t_text = parts[2]

                        if n_text and not any(f["name"] == n_text for f in ordered_fields):
                            # ヘッダ系の文字列を「完全一致」で除外 (名前_1 などを誤って消さないため)
                            if n_text not in ["名前", "フィールド名", "型", "タイプ", "オプション", "オプション / コメント", "並べ替え"]:
                                print(f"    - Added: '{n_text}' ({t_text})", file=sys.stderr)
                                ordered_fields.append({"name": n_text, "type": t_text})
                                found_new_in_any_item = True
                    except: continue

            except Exception as e:
                print(f"  > Scan error: {e}", file=sys.stderr)

            # 終了判定
            if total_expected > 0 and len(ordered_fields) >= total_expected:
                print(f"  > Reached expected total: {total_expected}", file=sys.stderr)
                break
                
            # 次へ移動
            pyautogui.press('down')
            time.sleep(0.1)

        fm_utils.update_overlay(f"読み取り完了: {len(ordered_fields)}件")
        return {"success": True, "fields": ordered_fields}

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
