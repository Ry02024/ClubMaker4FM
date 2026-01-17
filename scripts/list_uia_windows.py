from pywinauto import Desktop
import sys

def list_all_uia_windows():
    print("Listing all UIA top-level windows:")
    try:
        windows = Desktop(backend="uia").windows()
        for w in windows:
            try:
                print(f"[{w.class_name()}] '{w.window_text()}'")
            except:
                pass
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_all_uia_windows()
