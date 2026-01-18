import pywinauto
import time
import sys
from pywinauto import Desktop

def close_popups():
    print("Looking for FileMaker popups to close...", file=sys.stderr)
    
    # 閉じるべきタイトルキーワード
    targets = [
        "オプション", "Options", 
        "計算", "Calculation", 
        "集計", "Summary",
        "指定", "Specify"
    ]
    
    # FileMakerプロセスにアタッチしたいが、まずはデスクトップから探す
    desktop = Desktop(backend="uia")
    
    # 全ウィンドウ走査は重いので、前面にあるものを中心に
    # 何回かトライして、Esc連打も有効
    
    for i in range(3):
        try:
            # FileMakerと思わしきウィンドウ、かつDialog
            windows = desktop.windows(control_type="Window")
            for w in windows:
                txt = w.window_text()
                if not txt: continue
                
                # 特定のキーワードが含まれているか
                hit = False
                for t in targets:
                    if t in txt:
                        hit = True
                        break
                
                # Manage Database (データベースの管理) 自体は閉じない方がいいかもしれないが、
                # "余計な画面" なら閉じてもいいか？
                # ユーザー意図としては「エラーで止まっている変な小窓」を消したいはず
                # Manage Database は親ウィンドウなので除外
                if "データベース" in txt or "Database" in txt:
                    continue
                
                if hit:
                    print(f"Found popup: '{txt}' - Closing...", file=sys.stderr)
                    try:
                        w.set_focus()
                        time.sleep(0.2)
                        # Cancelボタンがあれば押す
                        if w.child_window(title="キャンセル", control_type="Button").exists():
                             w.child_window(title="キャンセル", control_type="Button").click()
                        elif w.child_window(title="Cancel", control_type="Button").exists():
                             w.child_window(title="Cancel", control_type="Button").click()
                        else:
                             w.close()
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"Error closing '{txt}': {e}", file=sys.stderr)
        except:
            pass
            
        time.sleep(1)

    print("Popup cleanup finished.", file=sys.stderr)

if __name__ == "__main__":
    close_popups()
