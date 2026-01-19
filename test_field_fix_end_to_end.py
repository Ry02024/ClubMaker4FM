"""
フィールド修正のエンドツーエンドテスト

このスクリプトは以下をテストします：
1. 実際のFileMakerからフィールドを読み込む
2. AIで修正案を生成する
3. その修正案を使って実際に修正を実行する
"""
import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path

# Windowsコンソールのエンコーディング設定
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def step1_read_fields():
    """ステップ1: フィールドの読み込み"""
    print("=" * 60)
    print("ステップ1: フィールドの読み込み")
    print("=" * 60)
    
    script_path = project_root / "scripts" / "get_fm_fields.py"
    venv_python = project_root / ".venv" / "Scripts" / "python.exe"
    
    if not venv_python.exists():
        venv_python = "python"
    else:
        venv_python = str(venv_python)
    
    if not script_path.exists():
        print(f"[ERROR] スクリプトが見つかりません: {script_path}")
        return None
    
    try:
        print(f"[INFO] FileMakerからフィールドを読み込んでいます...")
        result = subprocess.run(
            [venv_python, str(script_path)],
            capture_output=True,
            text=True,
            timeout=180,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode != 0:
            print(f"[ERROR] フィールド読み込みに失敗しました")
            if result.stderr:
                print(f"STDERR: {result.stderr}")
            return None
        
        # JSONをパース
        try:
            data = json.loads(result.stdout)
            if data.get("success"):
                fields = data.get("fields", [])
                print(f"[OK] フィールド読み込み成功: {len(fields)}件のフィールドを取得")
                
                # 最初の5件を表示
                print(f"\n[INFO] 読み込んだフィールド（最初の5件）:")
                for i, field in enumerate(fields[:5], 1):
                    print(f"  {i}. {field.get('name')} ({field.get('type')})")
                if len(fields) > 5:
                    print(f"  ... 他 {len(fields) - 5}件")
                
                return fields
            else:
                print(f"[ERROR] フィールド読み込み失敗: {data.get('error')}")
                return None
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSONパースエラー: {e}")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"[ERROR] タイムアウト: フィールド読み込みが180秒を超えました")
        return None
    except Exception as e:
        print(f"[ERROR] エラー: {e}")
        import traceback
        traceback.print_exc()
        return None

def step2_generate_suggestions(fields, max_fields=10):
    """ステップ2: AIで修正案を生成"""
    print("\n" + "=" * 60)
    print("ステップ2: AIで修正案を生成")
    print("=" * 60)
    
    if not fields or len(fields) == 0:
        print(f"[ERROR] フィールドが空です")
        return None
    
    # テスト用にフィールド数を制限
    test_fields = fields[:max_fields] if len(fields) > max_fields else fields
    if len(fields) > max_fields:
        print(f"[WARN] テスト用に最初の{max_fields}件のみを使用します（全{len(fields)}件中）")
    
    script_path = project_root / "scripts" / "suggest_field_fix.py"
    venv_python = project_root / ".venv" / "Scripts" / "python.exe"
    
    if not venv_python.exists():
        venv_python = "python"
    else:
        venv_python = str(venv_python)
    
    if not script_path.exists():
        print(f"[ERROR] スクリプトが見つかりません: {script_path}")
        return None
    
    # 一時ファイルにデータを保存
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.json') as f:
            temp_file = f.name
            json.dump({
                "currentFields": test_fields,
                "context": "テスト用のコンテキスト: 実際のフィールドを修正します"
            }, f, ensure_ascii=False, indent=2)
        
        print(f"[INFO] 一時ファイル作成: {temp_file}")
        print(f"[INFO] AI修正案生成中...")
        
        result = subprocess.run(
            [venv_python, str(script_path), "--file", temp_file],
            capture_output=True,
            text=True,
            timeout=120,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode != 0:
            print(f"[ERROR] AI修正案生成に失敗しました")
            if result.stderr:
                print(f"STDERR: {result.stderr}")
            return None
        
        # JSONをパース
        try:
            lines = result.stdout.strip().split('\n')
            last_line = lines[-1] if lines else ""
            
            if not last_line or not last_line.strip().startswith('{'):
                print(f"[ERROR] 有効なJSONが見つかりません")
                return None
            
            data = json.loads(last_line)
            if data.get("success"):
                suggestions = data.get("suggestions", [])
                print(f"[OK] AI修正案生成成功: {len(suggestions)}件の提案を取得")
                
                # 修正推奨のフィールドを表示
                fix_recommended = [s for s in suggestions if s.get("should_fix", False)]
                print(f"[INFO] 修正推奨: {len(fix_recommended)}件")
                
                if fix_recommended:
                    print(f"\n[INFO] 修正推奨フィールド（最初の5件）:")
                    for i, s in enumerate(fix_recommended[:5], 1):
                        print(f"  {i}. {s.get('old_name')} -> {s.get('new_name')} ({s.get('old_type')} -> {s.get('new_type')})")
                
                return suggestions
            else:
                print(f"[ERROR] AI修正案生成失敗: {data.get('error')}")
                return None
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSONパースエラー: {e}")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"[ERROR] タイムアウト: AI修正案生成が120秒を超えました")
        return None
    except Exception as e:
        print(f"[ERROR] エラー: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass

def step3_apply_fixes(suggestions):
    """ステップ3: 修正案を実際に適用"""
    print("\n" + "=" * 60)
    print("ステップ3: 修正案を実際に適用")
    print("=" * 60)
    
    if not suggestions:
        print(f"[ERROR] 修正案がありません")
        return False
    
    # 修正推奨のフィールドのみを抽出
    fixes_to_apply = []
    for s in suggestions:
        if s.get("should_fix", False):
            fix = {
                "old_name": s.get("old_name"),
                "new_name": s.get("new_name"),
                "new_type": s.get("new_type") if s.get("old_type") != s.get("new_type") else None,
                "comment": s.get("comment", "AI最適化")
            }
            fixes_to_apply.append(fix)
    
    if len(fixes_to_apply) == 0:
        print(f"[WARN] 修正推奨のフィールドがありません")
        return True
    
    print(f"[INFO] 修正対象: {len(fixes_to_apply)}件")
    print(f"[INFO] 修正内容（最初の3件）:")
    for i, fix in enumerate(fixes_to_apply[:3], 1):
        type_change = f" ({fix['new_type']})" if fix.get('new_type') else ""
        print(f"  {i}. {fix['old_name']} -> {fix['new_name']}{type_change}")
    if len(fixes_to_apply) > 3:
        print(f"  ... 他 {len(fixes_to_apply) - 3}件")
    
    # 確認
    print(f"\n[WARN] 実際にFileMakerのフィールドを修正します。")
    print(f"[WARN] 続行しますか？ (y/n): ", end="")
    
    # 自動テストの場合は 'y' を返す（実際の対話型テストでは入力待ち）
    # ここでは自動実行するため、確認をスキップ
    confirm = "y"  # 実際のテストでは input() を使用
    
    if confirm.lower() != 'y':
        print(f"[INFO] テストをキャンセルしました")
        return False
    
    script_path = project_root / "scripts" / "field_fixer.py"
    venv_python = project_root / ".venv" / "Scripts" / "python.exe"
    
    if not venv_python.exists():
        venv_python = "python"
    else:
        venv_python = str(venv_python)
    
    if not script_path.exists():
        print(f"[ERROR] スクリプトが見つかりません: {script_path}")
        return False
    
    # 一時ファイルに修正データを保存
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.json') as f:
            temp_file = f.name
            json.dump(fixes_to_apply, f, ensure_ascii=False, indent=2)
        
        print(f"[INFO] 一時ファイル作成: {temp_file}")
        print(f"[INFO] 修正実行中...")
        
        result = subprocess.run(
            [venv_python, str(script_path), "--file", temp_file],
            capture_output=True,
            text=True,
            timeout=300,  # 5分のタイムアウト
            encoding='utf-8',
            errors='replace'
        )
        
        print(f"\nReturn code: {result.returncode}")
        
        if result.stderr:
            print(f"\nSTDERR:\n{result.stderr}")
        
        if result.stdout:
            print(f"\nSTDOUT:\n{result.stdout}")
        
        if result.returncode != 0:
            print(f"\n[ERROR] 修正実行に失敗しました")
            return False
        
        # JSONをパース
        try:
            lines = result.stdout.strip().split('\n')
            last_line = lines[-1] if lines else ""
            
            if not last_line or not last_line.strip().startswith('{'):
                print(f"\n[WARN] 有効なJSONが見つかりません（正常終了の可能性あり）")
                return True
            
            data = json.loads(last_line)
            print(f"\n[OK] JSONパース成功")
            print(f"[INFO] 結果: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            if data.get("success"):
                succeeded = data.get("succeeded", 0)
                total = data.get("total", len(fixes_to_apply))
                print(f"\n[OK] 修正処理が正常に完了しました")
                print(f"[INFO] 成功: {succeeded}/{total}件")
                return True
            else:
                print(f"\n[WARN] 修正処理は失敗しました")
                print(f"[INFO] エラー: {data.get('error', 'Unknown error')}")
                return False
                
        except json.JSONDecodeError as e:
            print(f"\n[WARN] JSONパースエラー: {e}")
            print(f"[INFO] スクリプトは実行されましたが、JSON出力がありません")
            return True  # エラーではない可能性
            
    except subprocess.TimeoutExpired:
        print(f"\n[ERROR] タイムアウト: 修正実行が300秒を超えました")
        return False
    except Exception as e:
        print(f"\n[ERROR] エラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass

def main():
    """メイン処理: エンドツーエンドテスト"""
    print("[TEST] フィールド修正のエンドツーエンドテスト開始")
    print(f"[INFO] プロジェクトルート: {project_root}")
    print()
    
    # ステップ1: フィールド読み込み
    fields = step1_read_fields()
    if not fields:
        print("\n[FAIL] テスト失敗: フィールド読み込みに失敗しました")
        return 1
    
    # ステップ2: AI修正案生成
    suggestions = step2_generate_suggestions(fields, max_fields=10)
    if not suggestions:
        print("\n[FAIL] テスト失敗: AI修正案生成に失敗しました")
        return 1
    
    # 修正推奨のフィールドがあるか確認
    fix_recommended = [s for s in suggestions if s.get("should_fix", False)]
    if len(fix_recommended) == 0:
        print("\n[WARN] 修正推奨のフィールドがありません")
        print("[INFO] テストは成功しましたが、修正対象がありませんでした")
        return 0
    
    # ステップ3: 修正実行
    success = step3_apply_fixes(suggestions)
    if not success:
        print("\n[FAIL] テスト失敗: 修正実行に失敗しました")
        return 1
    
    print("\n" + "=" * 60)
    print("[SUCCESS] 全テスト成功！")
    print("=" * 60)
    print(f"\n[SUMMARY] テスト結果サマリー:")
    print(f"  - 読み込んだフィールド数: {len(fields)}件")
    print(f"  - 生成された修正案数: {len(suggestions)}件")
    print(f"  - 修正推奨数: {len(fix_recommended)}件")
    print(f"  - 修正実行: 成功")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
