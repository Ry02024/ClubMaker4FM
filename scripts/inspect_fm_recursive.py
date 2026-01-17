from pywinauto import Desktop
import sys

def dump_children(wrapper, indent=0):
    try:
        text = wrapper.window_text()
        cls = wrapper.class_name()
        print("  " * indent + f"[{cls}] '{text}'")
        for child in wrapper.children():
            dump_children(child, indent + 1)
    except:
        pass

def inspect_fm_recursive():
    try:
        windows = Desktop(backend="win32").windows()
        dialogs = [w for w in windows if w.is_visible() and ("データベースの管理" in w.window_text() or "Manage Database" in w.window_text())]
        
        if not dialogs:
            print("No Manage Database dialog found.")
            return

        target = dialogs[0]
        print(f"Dumping hierarchy for: {target.window_text()}")
        dump_children(target)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_fm_recursive()
