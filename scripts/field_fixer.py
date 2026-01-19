from pywinauto import Application, Desktop
import time
import sys
import json
import ctypes
import fm_utils  # Robust utility

def find_manage_database_dialog(app):
    """fm_utilsの共通関数を使用する"""
    return fm_utils.find_manage_database_dialog()

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
                    # UI構成要素からテキストを抽出
                    texts = win.descendants(control_type="Static")
                    if not texts:
                        texts = win.descendants(control_type="Text")
                    content_text = "".join([t.window_text() for t in texts if t.window_text()])
                except:
                    pass

                print(f"  > [Dialog Debug] Title: '{title}', Content: '{content_text[:50]}...'", file=sys.stderr)

                # 1. 保存確認の場合
                if any(k in content_text for k in ["保存", "save", "変更しますか"]):
                    save_btn = win.child_window(title_re=".*保存.*|.*はい.*|.*Yes.*", control_type="Button")
                    if save_btn.exists():
                        print(f"  > [Dialog: Save] Clicking Save/Yes", file=sys.stderr)
                        save_btn.click_input()
                        time.sleep(0.2)  # 待機時間を短縮（0.5秒→0.2秒）
                        return True
                
                # 2. 名前重複エラーなどの警告の場合
                if any(k in content_text for k in ["すでに使用されています", "already in use", "無効", "invalid"]):
                    ok_btn = win.child_window(title_re=".*OK.*", control_type="Button")
                    if ok_btn.exists():
                        print(f"  > [CRITICAL ERROR] Duplicate name or invalid name detected: {content_text}", file=sys.stderr)
                        ok_btn.click_input()
                        time.sleep(0.2)  # 待機時間を短縮（0.5秒→0.2秒）
                        # 重複エラー時は「異常」として即座に中断フラグを返す
                        return "ABORT_ERROR"

                # 3. その他の一般的な OK 案内の場合
                ok_btn = win.child_window(title_re=".*OK.*|.*閉じる.*|.*Close.*", control_type="Button")
                if ok_btn.exists():
                    print(f"  > [Dialog: Info] Clicking 'OK/Close'", file=sys.stderr)
                    ok_btn.click_input()
                    time.sleep(0.2)  # 待機時間を短縮（0.5秒→0.2秒）
                    return True
                    
    except Exception as e:
        print(f"  > [Dialog Handler Exception] {e}", file=sys.stderr)
    return False

def select_field_by_name(dialog_spec, field_name):
    """
    リストの最上部(Home)に移動し、Downキーで1つずつ走査して、
    指定された名前のフィールドを確実に選択する。
    """
    try:
        field_list = dialog_spec.child_window(auto_id="IDC_DEFFIELDS_FIELD_LIST", control_type="DataGrid")
        if not field_list.exists():
            return False
        
        field_list.set_focus()
        # リストの一番上へ移動
        import pyautogui
        pyautogui.press('home')
        time.sleep(0.1)  # 待機時間を短縮（0.3秒→0.1秒）
        
        max_search = 300 # フィールド総数に応じた上限
        seen_items = set()  # 重複チェック用（高速化）
        
        for i in range(max_search):
            # 現在見えている(UIAで取得可能な)DataItemから、名前が一致するものを探す
            items = field_list.descendants(control_type="DataItem")
            if not items:
                items = field_list.children(control_type="DataItem")
            
            for item in items:
                try:
                    # 重複チェック（同じアイテムを複数回処理しない）
                    item_id = id(item)
                    if item_id in seen_items:
                        continue
                    seen_items.add(item_id)
                    
                    cells = item.children()
                    if not cells: continue
                    name_nodes = cells[0].descendants(control_type="Text")
                    if not name_nodes: continue
                    current_name = name_nodes[0].window_text()
                    
                    if current_name == field_name:
                        # 名前が一致したら選択する
                        try:
                            item.select() # SelectionItem pattern
                            time.sleep(0.05)  # 待機時間を短縮（0.1秒→0.05秒）
                        except:
                            item.click_input()
                        
                        # 確実に反映させるために最初のセルをクリック
                        try:
                            cells[0].click_input()
                        except: pass
                        
                        print(f"  > Target found and selected: {field_name}", file=sys.stderr)
                        return True
                except: continue

            # 高速スクロール: PageDownで一度に複数行スクロール
            # 最初の数回はPageDown、その後は調整
            if i < 3:
                pyautogui.press('pagedown')
                time.sleep(0.02)  # 待機時間を大幅に短縮（0.05秒→0.02秒）
            else:
                pyautogui.press('pagedown')
                time.sleep(0.02)
            
        return False
    except Exception as e:
        print(f"  > Select error: {e}", file=sys.stderr)
        return False

def fix_single_field(dialog_spec, old_name, new_name, new_type=None, comment="AI最適化"):
    """
    1つのフィールドを上から順に探して修整する。
    """
    print(f"\n[Fixing] {old_name} -> {new_name}", file=sys.stderr)
    handle_confirmation_dialog(None)

    # 1. フィールドを上から順に検索して選択
    if not select_field_by_name(dialog_spec, old_name):
        print(f"  > Error: Field '{old_name}' not found. Skipping to prevent accidental creation.", file=sys.stderr)
        return False

    try:
        # 2. 選択後の検証
        name_edit = dialog_spec.child_window(auto_id="IDC_DEFFIELDS_FIELDNAME_EDIT", control_type="Edit")
        if not name_edit.exists():
             print("  > Error: Field Name edit box not found.", file=sys.stderr)
             return False
             
        # 直接 window_text() を取得
        actual_val = name_edit.window_text() or name_edit.get_value() or ""
        print(f"  > Verification: Active field in Edit box is '{actual_val}' (Expected: '{old_name}')", file=sys.stderr)
        
        # 名前が一致しない場合でも、ひとまずフォーカスしてリトライを試みる
        if actual_val != old_name:
            print(f"  > Warning: Selection mismatch. Trying to re-select...", file=sys.stderr)
            # 再度検索
            if not select_field_by_name(dialog_spec, old_name):
                 return False
            actual_val = name_edit.window_text() or name_edit.get_value() or ""
            if actual_val != old_name:
                print(f"  > Selection still failing. Skipping '{old_name}'.", file=sys.stderr)
                return False

        # 3. 名前変更
        print(f"  > Entering new name: '{new_name}'", file=sys.stderr)
        # UIAの直接入力(set_text/set_edit_text)を試みる
        entered_success = False
        try:
            name_edit.set_focus()
            name_edit.set_text(new_name) # 速くて確実
            time.sleep(0.1)  # 待機時間を短縮（0.2秒→0.1秒）
            if name_edit.window_text() == new_name or name_edit.get_value() == new_name:
                entered_success = True
        except: pass
        
        if not entered_success:
            # フォールバック: キー操作
            print("  > Direct entry failed. Falling back to type_keys...", file=sys.stderr)
            name_edit.click_input()
            time.sleep(0.05)  # 待機時間を短縮（0.1秒→0.05秒）
            name_edit.type_keys("^a{BACKSPACE}", with_spaces=True)
            time.sleep(0.05)  # 待機時間を短縮（0.1秒→0.05秒）
            name_edit.type_keys(new_name, with_spaces=True)
            time.sleep(0.1)  # 待機時間を短縮（0.3秒→0.1秒）
        
        # 入力後の値を最終ダブルチェック
        entered_val = name_edit.window_text() or name_edit.get_value() or ""
        print(f"  > Value after entry: '{entered_val}'", file=sys.stderr)
        
        if not entered_val or entered_val == old_name:
             print("  > Critical: Name was NOT updated in the edit box. Retrying with pyautogui...", file=sys.stderr)
             name_edit.click_input()
             pyautogui.hotkey('ctrl', 'a')
             pyautogui.press('backspace')
             pyautogui.typewrite(new_name)
             time.sleep(0.2)  # 待機時間を短縮（0.5秒→0.2秒）

        # 4. 型変更
        if new_type:
            try:
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
                type_combo.set_focus()
                # 警告: ここで Enter を送ると「作成」が実行される可能性があるため、キーのみ送る
                type_combo.type_keys(key)
                time.sleep(0.1)  # 待機時間を短縮（0.3秒→0.1秒）
            except Exception as e:
                print(f"  > Warning: Type change failed: {e}", file=sys.stderr)
        
        # 5. コメント変更
        try:
            comment_edit = dialog_spec.child_window(auto_id="IDC_DEFFIELDS_FIELDCOMMENT_EDIT", control_type="Edit")
            if comment_edit.exists():
                comment_edit.set_focus()
                # 確実にクリアしてからセット
                comment_edit.set_text(comment)
                time.sleep(0.1)  # 待機時間を短縮（0.2秒→0.1秒）
        except: pass
        
        # 6. 変更確定
        print(f"  > Finalizing change (Clicking 'Change')...", file=sys.stderr)
        clicked = False
        try:
            # 変更ボタン (日本語: 変更, 英語: Change)
            # 警告: 「作成」ボタン（IDC_DEFFIELDS_CREATE_BTN）は絶対にクリックしないよう厳格に特定
            change_btn = dialog_spec.child_window(title_re="^変更$|^Change$", control_type="Button", auto_id="IDC_DEFFIELDS_CHANGE_BTN")
            if not change_btn.exists():
                # タイトルのみで再試行
                change_btn = dialog_spec.child_window(title_re="^変更$|^Change$", control_type="Button")
            
            if change_btn.exists():
                print(f"  > Found 'Change' button. Clicking...", file=sys.stderr)
                change_btn.click_input()
                clicked = True
        except Exception as e:
            print(f"  > Change button search error: {e}", file=sys.stderr)

        if not clicked:
            # 日本語版の変更ショートカットは Alt+M (修整/Modify) の場合がある
            print(f"  > Fallback: Sending Alt+M (Japanese Change shortcut)...", file=sys.stderr)
            dialog_spec.type_keys("%m")
            time.sleep(0.1)  # 待機時間を短縮（0.3秒→0.1秒）
            # または Alt+A (Change)
            dialog_spec.type_keys("%a")
        
        time.sleep(0.3)  # 変更の反映待ち（0.8秒→0.3秒）
        
        # 7. 完了確認 (Editボックスがクリアされるか、次の行が選択されるかなど)
        # FileMakerでは「変更」を押すと、通常入力エリアが空になるか、引き続き選択されている
        # ここでは特に待機のみ行い、ダイアログをチェック
        handle_confirmation_dialog(None)
        return True
    except Exception as e:
        print(f"  > Exception during fix: {e}", file=sys.stderr)
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
                print("CRITICAL: 'データベースの管理' ダイアログが見つかりません。FileMakerが前面にあり、ダイアログが開いているか確認してください。", file=sys.stderr)
                # フォールバック: 現在アクティブなウィンドウを試す
                try:
                    desktop = Desktop(backend="uia")
                    dialog = desktop.top_window()
                    print(f"  > Fallback: Attempting to use top window: '{dialog.window_text()}'", file=sys.stderr)
                except:
                    break
            else:
                dialog = fm_utils.find_manage_database_dialog()

            if not dialog:
                print("Error: Dialog open but handle not found?", file=sys.stderr)
                errors.append(fix.get("old_name"))
                continue
                
            dialog_spec = dialog
            dialog_spec.set_focus()

            # Ensure "Fields" tab is selected (Reliable check)
            try:
                # auto_id や control_type でより確実に特定
                tab_control = dialog_spec.child_window(control_type="Tab")
                if tab_control.exists():
                    fields_tab = tab_control.child_window(title="フィールド", control_type="TabItem")
                    if fields_tab.exists():
                        if not fields_tab.is_selected():
                            print(f"  > Selecting 'Fields' tab...", file=sys.stderr)
                            fields_tab.click_input()
                            time.sleep(0.3)  # 待機時間を短縮（0.8秒→0.3秒）
                    else:
                        # フォールバック: キー送信
                        dialog_spec.type_keys("%f")
                        time.sleep(0.2)  # 待機時間を短縮（0.5秒→0.2秒）
            except Exception as e:
                print(f"  > [Tab Selection Warning] {e}. Trying Atl+F...", file=sys.stderr)
                dialog_spec.type_keys("%f")
                time.sleep(0.2)  # 待機時間を短縮（0.5秒→0.2秒）

            new_type = fix.get("new_type", None)
            comment = fix.get("comment", "ClubMaker最適化")
            
            if fix_single_field(dialog_spec, old_name, new_name, new_type, comment):
                success_count += 1
            else:
                errors.append(old_name)
            
            # 各フィールド修整後にダイアログが出た場合を考慮
            diag_res = handle_confirmation_dialog(app)
            if diag_res == "ABORT_ERROR":
                print("CRITICAL: Aborting due to duplicate name error.", file=sys.stderr)
                fm_utils.update_overlay("エラー発生: 名前重複。中断します。")
                break
            time.sleep(0.2)  # 待機時間を短縮（0.5秒→0.2秒） 
        
        fm_utils.update_overlay("完了しました！")
        time.sleep(0.5)  # 待機時間を短縮（1.5秒→0.5秒）
        return {"success": True, "total": len(fix_list), "succeeded": success_count, "errors": errors}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        fm_utils.stop_overlay()
        fm_utils.set_input_block(False)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix FileMaker fields')
    parser.add_argument('--file', type=str, help='Path to JSON file containing fixes list')
    parser.add_argument('data', nargs='?', help='JSON string (deprecated, use --file instead)')
    
    args = parser.parse_args()
    
    try:
        if args.file:
            # 一時ファイルから読み取る
            with open(args.file, 'r', encoding='utf-8') as f:
                fixes = json.load(f)
        elif args.data:
            # 後方互換性のため、コマンドライン引数もサポート
            fixes = json.loads(args.data)
        else:
            print(json.dumps({"success": False, "error": "No input provided. Use --file option or provide JSON string."}, ensure_ascii=True))
            sys.exit(1)
        
        result = batch_fix(fixes)
        print(json.dumps(result, ensure_ascii=True))
    except FileNotFoundError as e:
        print(json.dumps({"success": False, "error": f"File not found: {e}"}, ensure_ascii=True))
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": f"Invalid JSON: {e}"}, ensure_ascii=True))
        sys.exit(1)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(json.dumps({
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "traceback": error_details
        }, ensure_ascii=True))
        print(f"Error details: {error_details}", file=sys.stderr)
        sys.exit(1)
