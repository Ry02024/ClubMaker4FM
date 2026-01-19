"""
フィールド読み込み → AI修正案生成 → リスト化のエンドツーエンドテスト

このスクリプトは以下をテストします：
1. フィールドの読み込み（get_fm_fields.py）
2. AIによる修正案の生成（suggest_field_fix.py）
3. 結果のリスト化と表示
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

def test_field_reading():
    """ステップ1: フィールドの読み込みをテスト"""
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
        result = subprocess.run(
            [venv_python, str(script_path)],
            capture_output=True,
            text=True,
            timeout=180,  # 3分のタイムアウト
            encoding='utf-8',
            errors='replace'
        )
        
        print(f"Return code: {result.returncode}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        
        if result.returncode != 0:
            print(f"[ERROR] フィールド読み込みに失敗しました")
            print(f"Error: {result.stderr}")
            return None
        
        # JSONをパース
        try:
            data = json.loads(result.stdout)
            if data.get("success"):
                fields = data.get("fields", [])
                print(f"[OK] フィールド読み込み成功: {len(fields)}件のフィールドを取得")
                print(f"\n最初の5件:")
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
            print(f"STDOUT: {result.stdout}")
            return None
            
    except subprocess.TimeoutExpired:
        print("[ERROR] タイムアウト: フィールド読み込みが180秒を超えました")
        return None
    except Exception as e:
        print(f"[ERROR] エラー: {e}")
        return None

def test_ai_suggestions(fields, context=""):
    """ステップ2: AIによる修正案の生成をテスト"""
    print("\n" + "=" * 60)
    print("ステップ2: AIによる修正案の生成")
    print("=" * 60)
    
    if not fields or len(fields) == 0:
        print("[WARN] フィールドが空です。スキップします。")
        return None
    
    # テスト用にフィールド数を制限（大量のフィールドでテストする場合）
    test_fields = fields[:20] if len(fields) > 20 else fields
    if len(fields) > 20:
        print(f"[WARN] テスト用に最初の20件のみを使用します（全{len(fields)}件中）")
    
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
                "context": context or "テスト用のコンテキスト"
            }, f, ensure_ascii=False, indent=2)
        
        print(f"[INFO] 一時ファイル作成: {temp_file}")
        print(f"[INFO] テストフィールド数: {len(test_fields)}件")
        
        result = subprocess.run(
            [venv_python, str(script_path), "--file", temp_file],
            capture_output=True,
            text=True,
            timeout=120,  # 2分のタイムアウト
            encoding='utf-8',
            errors='replace'
        )
        
        print(f"Return code: {result.returncode}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        
        if result.returncode != 0:
            print(f"[ERROR] AI修正案生成に失敗しました")
            print(f"Error: {result.stderr}")
            return None
        
        # JSONをパース
        try:
            lines = result.stdout.strip().split('\n')
            last_line = lines[-1] if lines else ""
            
            if not last_line or not last_line.strip().startswith('{'):
                print(f"[ERROR] 有効なJSONが見つかりません")
                print(f"STDOUT: {result.stdout}")
                return None
            
            data = json.loads(last_line)
            if data.get("success"):
                suggestions = data.get("suggestions", [])
                print(f"[OK] AI修正案生成成功: {len(suggestions)}件の提案を取得")
                return suggestions
            else:
                print(f"[ERROR] AI修正案生成失敗: {data.get('error')}")
                if 'traceback' in data:
                    print(f"Traceback:\n{data['traceback']}")
                return None
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSONパースエラー: {e}")
            print(f"STDOUT: {result.stdout}")
            return None
            
    except subprocess.TimeoutExpired:
        print("[ERROR] タイムアウト: AI修正案生成が120秒を超えました")
        return None
    except Exception as e:
        print(f"[ERROR] エラー: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # 一時ファイルを削除
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
                print(f"[INFO] 一時ファイル削除: {temp_file}")
            except:
                pass

def format_suggestions_list(suggestions):
    """ステップ3: 修正案をリスト形式で表示"""
    print("\n" + "=" * 60)
    print("ステップ3: 修正案のリスト化")
    print("=" * 60)
    
    if not suggestions:
        print("[ERROR] 修正案がありません")
        return None
    
    print(f"\n[LIST] 修正案リスト ({len(suggestions)}件):\n")
    
    # テーブル形式で表示
    print(f"{'No.':<5} {'現在の名前':<25} {'提案名':<25} {'現在の型':<15} {'提案型':<15} {'修正':<5}")
    print("-" * 100)
    
    for i, suggestion in enumerate(suggestions, 1):
        old_name = suggestion.get("old_name", "")
        new_name = suggestion.get("new_name", "")
        old_type = suggestion.get("old_type", "")
        new_type = suggestion.get("new_type", "")
        should_fix = suggestion.get("should_fix", False)
        
        # 変更がある場合は強調表示
        name_changed = old_name != new_name
        type_changed = old_type != new_type
        
        fix_mark = "✓" if should_fix else "-"
        name_mark = "→" if name_changed else "="
        type_mark = "→" if type_changed else "="
        
        print(f"{i:<5} {old_name[:24]:<25} {name_mark} {new_name[:24]:<25} {old_type[:14]:<15} {type_mark} {new_type[:14]:<15} {fix_mark:<5}")
    
    # 統計情報
    fix_count = sum(1 for s in suggestions if s.get("should_fix", False))
    name_changed_count = sum(1 for s in suggestions if s.get("old_name") != s.get("new_name"))
    type_changed_count = sum(1 for s in suggestions if s.get("old_type") != s.get("new_type"))
    
    print("\n" + "-" * 100)
    print(f"[STATS] 統計:")
    print(f"  - 総提案数: {len(suggestions)}件")
    print(f"  - 修正推奨: {fix_count}件")
    print(f"  - 名前変更: {name_changed_count}件")
    print(f"  - 型変更: {type_changed_count}件")
    
    return suggestions

def main():
    """メイン処理: エンドツーエンドテスト"""
    print("[TEST] フィールド読み込み -> AI修正案生成 -> リスト化のテスト開始")
    print(f"[INFO] プロジェクトルート: {project_root}")
    print()
    
    # ステップ1: フィールド読み込み
    fields = test_field_reading()
    if not fields:
        print("\n[FAIL] テスト失敗: フィールド読み込みに失敗しました")
        return 1
    
    # ステップ2: AI修正案生成
    suggestions = test_ai_suggestions(fields, context="テスト用のコンテキスト")
    if not suggestions:
        print("\n[FAIL] テスト失敗: AI修正案生成に失敗しました")
        return 1
    
    # ステップ3: リスト化
    formatted = format_suggestions_list(suggestions)
    if not formatted:
        print("\n[FAIL] テスト失敗: リスト化に失敗しました")
        return 1
    
    print("\n" + "=" * 60)
    print("[SUCCESS] 全テスト成功！")
    print("=" * 60)
    print(f"\n[SUMMARY] テスト結果サマリー:")
    print(f"  - 読み込んだフィールド数: {len(fields)}件")
    print(f"  - 生成された修正案数: {len(suggestions)}件")
    print(f"  - 修正推奨数: {sum(1 for s in suggestions if s.get('should_fix', False))}件")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
