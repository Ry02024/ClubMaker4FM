import subprocess
import json
import os
import sys

def run_script(script_name, args=None):
    venv_python = os.path.join(os.getcwd(), '.venv', 'Scripts', 'python.exe')
    python_cmd = venv_python if os.path.exists(venv_python) else 'python'
    script_path = os.path.join(os.getcwd(), 'scripts', script_name)
    cmd = [python_cmd, script_path]
    if args:
        cmd.append(json.dumps(args, ensure_ascii=False))
    
    # shell=True を使わず、リスト形式で渡すことでクォートの問題を回避
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    
    if result.stderr:
        print(f"Error running {script_name}: {result.stderr}", file=sys.stderr)
    return result.stdout.strip()

def main():
    # 0. Activate FileMaker
    print("Activating FileMaker Pro...")
    run_script('activate_fm.py')
    
    # 1. Get existing fields
    fields_output = run_script('get_fm_fields.py')
    try:
        fields_data = json.loads(fields_output)
    except json.JSONDecodeError:
        print('Failed to parse fields output', file=sys.stderr)
        sys.exit(1)
    if not fields_data.get('success'):
        print('Failed to retrieve fields:', fields_data.get('error'), file=sys.stderr)
        sys.exit(1)
    current_fields = fields_data.get('fields', [])

    # 2. Get AI suggestions
    suggestion_input = {"currentFields": current_fields}
    suggestions_output = run_script('suggest_field_fix.py', suggestion_input)
    try:
        suggestions_data = json.loads(suggestions_output)
    except json.JSONDecodeError:
        print('Failed to parse suggestions output', file=sys.stderr)
        sys.exit(1)
    if not suggestions_data.get('success'):
        print('AI suggestion error:', suggestions_data.get('error'), file=sys.stderr)
        sys.exit(1)
    fixes = suggestions_data.get('suggestions', [])

    # 3. Apply fixes via field_fixer.py
    if not fixes:
        print('No fixes to apply')
        return
    apply_output = run_script('field_fixer.py', fixes)
    print('Field fixer output:', apply_output)

if __name__ == '__main__':
    main()
