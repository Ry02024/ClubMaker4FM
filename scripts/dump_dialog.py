from pywinauto import Application, Desktop
import sys

def dump():
    app = Application(backend="uia").connect(path="FileMaker Pro.exe")
    windows = app.windows()
    target = None
    for w in windows:
        if "データベースの管理" in w.window_text():
            target = w
            break
    if not target:
        for w in windows:
            for child in w.children():
                if "データベースの管理" in child.window_text():
                    target = child
                    break
            if target: break
    
    if target:
        app.window(handle=target.handle).print_control_identifiers()
    else:
        print("Dialog not found")

if __name__ == "__main__":
    dump()
