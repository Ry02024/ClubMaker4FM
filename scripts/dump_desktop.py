from pywinauto import Application, Desktop
import time

def dump_all():
    all_windows = Desktop(backend="uia").windows()
    for w in all_windows:
        if "データベースの管理" in w.window_text():
            print(f"Dumping: {w.window_text()}")
            w.print_control_identifiers()
            break

if __name__ == "__main__":
    dump_all()
