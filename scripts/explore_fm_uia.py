from pywinauto import Application, Desktop
import sys
import io

# Set stdout to UTF-8 to handle special characters
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def explore_fm_uia():
    try:
        print("Searching for all windows in FileMaker process (UIA)...")
        app = Application(backend="uia").connect(path="FileMaker Pro.exe")
        windows = app.windows()
        
        for w in windows:
            title = w.window_text()
            print(f"\n--- Found Window: '{title}' [{w.class_name()}] ---")
            
            # If it's a main window, try to find the "Manage Database" dialog inside it
            if "データベースの管理" in title or "Manage Database" in title:
                print("Inspecting this dialog...")
                try:
                    spec = Desktop(backend="uia").window(handle=w.handle)
                    spec.print_control_identifiers()
                except Exception as e:
                    print(f"Error dumping identifiers: {e}")
            else:
                # Also check children of main windows
                try:
                    children = w.children()
                    for child in children:
                        c_title = child.window_text()
                        if "データベースの管理" in c_title or "Manage Database" in c_title:
                            print(f"Found Dialog as child: '{c_title}'")
                            spec = Desktop(backend="uia").window(handle=child.handle)
                            spec.print_control_identifiers()
                except:
                    pass
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    explore_fm_uia()
