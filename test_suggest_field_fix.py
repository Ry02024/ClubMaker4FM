"""
テスト用スクリプト: suggest_field_fix.pyを直接実行してエラーを確認
"""
import sys
import os
import json

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# テストデータ
test_data = {
    "currentFields": [
        {"name": "var_vlist", "type": "日付"},
        {"name": "var_tmp", "type": "日付"},
        {"name": "var_tc", "type": "日付"}
    ],
    "context": "テスト用のコンテキスト"
}

# 一時ファイルに保存
import tempfile
temp_file = os.path.join(tempfile.gettempdir(), f"clubmaker_test_{os.getpid()}.json")
with open(temp_file, 'w', encoding='utf-8') as f:
    json.dump(test_data, f, ensure_ascii=False, indent=2)

print(f"Test file created: {temp_file}")
print(f"Test data: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
print("\n" + "="*50)
print("Running suggest_field_fix.py...")
print("="*50 + "\n")

# スクリプトを実行
import subprocess
script_path = os.path.join(os.path.dirname(__file__), "scripts", "suggest_field_fix.py")
venv_python = os.path.join(os.path.dirname(__file__), ".venv", "Scripts", "python.exe")

if os.path.exists(venv_python):
    python_cmd = venv_python
else:
    python_cmd = "python"

command = [python_cmd, script_path, "--file", temp_file]

try:
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=120,
        encoding='utf-8',
        errors='replace'
    )
    
    print("STDOUT:")
    print(result.stdout)
    print("\n" + "-"*50 + "\n")
    print("STDERR:")
    print(result.stderr)
    print("\n" + "-"*50 + "\n")
    print(f"Return code: {result.returncode}")
    
    if result.returncode != 0:
        print("\n❌ Script failed!")
    else:
        print("\n✅ Script succeeded!")
        
except subprocess.TimeoutExpired:
    print("❌ Script execution timeout (120s)")
except Exception as e:
    print(f"❌ Error running script: {e}")
finally:
    # 一時ファイルを削除
    if os.path.exists(temp_file):
        try:
            os.unlink(temp_file)
            print(f"\nCleaned up: {temp_file}")
        except:
            pass
