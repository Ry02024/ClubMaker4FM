from pywinauto import Application
import sys

def inspect_fm_dialog():
    try:
        from pywinauto import Desktop
        windows = Desktop(backend="uia").windows()
        dialogs = [w for w in windows if w.is_visible() and ("データベースの管理" in w.window_text() or "Manage Database" in w.window_text())]
        
        if not dialogs:
            print("No Manage Database dialog found.")
            return

        target_wrapper = dialogs[0]
        target = Desktop(backend="uia").window(handle=target_wrapper.handle)
        print(f"Inspecting Window: {target.window_text()}")
        target.print_control_identifiers()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_fm_dialog()
