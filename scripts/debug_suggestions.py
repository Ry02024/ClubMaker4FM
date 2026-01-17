import subprocess
import json
import os

def check():
    with open('suggest_input.json', 'r', encoding='utf-8') as f:
        data = f.read()
    
    venv_python = os.path.join(os.getcwd(), '.venv', 'Scripts', 'python.exe')
    cmd = [venv_python, 'scripts/suggest_field_fix.py', data]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)

if __name__ == "__main__":
    check()
