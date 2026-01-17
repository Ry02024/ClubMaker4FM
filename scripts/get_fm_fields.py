from pywinauto import Application, Desktop
import sys
import json

def get_existing_fields():
    """『データベースの管理』ダイアログから現在のフィールド一覧を取得する"""
    try:
        # Desktop経由でウィンドウを探す
        all_windows = Desktop(backend="win32").windows()
        dialogs = [w for w in all_windows if w.is_visible() and ("データベースの管理" in w.window_text() or "Manage Database" in w.window_text())]
        
        if not dialogs:
            return {"success": False, "error": "Manage Database dialog not found."}
            
        target = dialogs[0]
        # ListViewを探す (通常、フィールド一覧は1番目のListView)
        list_view = target.child_window(class_name="SysListView32")
        
        if not list_view.exists():
            return {"success": False, "error": "Field List View not found."}
            
        # 項目を取得
        items = list_view.texts()
        # ListViewのtexts()は[ヘッダー1, ヘッダー2, ..., 行1列1, 行1列2, ...] という形式
        # 日本語版では: [フィールド名, タイプ, オプション/コメント, ...]
        
        fields = []
        # ヘッダーが3つと仮定
        header_count = 3
        for i in range(header_count, len(items), header_count):
            if i < len(items):
                fields.append(items[i]) # フィールド名
                
        return {"success": True, "fields": fields}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = get_existing_fields()
    print(json.dumps(result, ensure_ascii=False))
