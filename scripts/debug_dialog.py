from pywinauto import Desktop
import sys
import io

# Set stdout to UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def debug_dialog():
    print("Searching for Manage Database dialog...")
    all_windows = Desktop(backend="uia").windows()
    target = None
    for w in all_windows:
        title = w.window_text()
        if any(kw in title for kw in ["データベースの管理", "Manage Database", "の管理", "Database"]):
            try:
                if "FileMaker" in w.process_name():
                    target = w
                    break
            except: continue
            
    if target:
        print(f"Found Dialog: '{target.window_text()}'")
        print("Dumping identifiers...")
        target.print_control_identifiers()
    else:
        print("Dialog not found.")

if __name__ == "__main__":
    debug_dialog()
