import win32clipboard
import win32con
import sys
import os

def set_fm_xml_clipboard(xml_data: str):
    """FileMaker Pro 25対応 多形式クリップボード登録"""
    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        
        # 1. 基本Unicodeテキスト (CF_UNICODETEXT) - Windowsの標準
        # win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, xml_data) は内部でUTF-16LEに変換される
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, xml_data)
        
        # 2. FileMaker XML形式 (FileMaker XML Snippet) - これが貼り付けボタン活性化の鍵
        try:
            fm_format = win32clipboard.RegisterClipboardFormat("FileMaker XML Snippet")
            win32clipboard.SetClipboardData(fm_format, xml_data.encode('utf-8'))
        except Exception as e:
            print(f"Warning: FileMaker XML Snippet error: {e}")

        # 3. 旧形式テキスト (CF_TEXT) 
        try:
            win32clipboard.SetClipboardData(win32con.CF_TEXT, xml_data.encode('ascii', 'ignore'))
        except Exception as e:
            print(f"Warning: CF_TEXT error: {e}")

        # 4. HTML形式 (HTML Format) - ブラウザ連携の互換性向上のため
        try:
            cf_html = win32clipboard.RegisterClipboardFormat("HTML Format")
            html_content = f'<html><body><!--StartFragment-->{xml_data}<!--EndFragment--></body></html>'
            win32clipboard.SetClipboardData(cf_html, html_content.encode('utf-8'))
        except Exception as e:
            print(f"Warning: HTML Format error: {e}")
            
        win32clipboard.CloseClipboard()
        print(f"Success: Registered 4 formats to clipboard for FileMaker. Length: {len(xml_data)}")
        return True
    except Exception as e:
        print(f"Error setting multi-format clipboard: {e}")
        try: win32clipboard.CloseClipboard()
        except: pass
        return False

if __name__ == "__main__":
    # 引数または標準入力からXMLを取得
    xml_input = ""
    if len(sys.argv) > 1:
        # ファイルから読み込む（コマンドライン引数の制限回避のため）
        if os.path.exists(sys.argv[1]):
            with open(sys.argv[1], 'r', encoding='utf-8') as f:
                xml_input = f.read()
        else:
            xml_input = sys.argv[1]
    
    if not xml_input:
        xml_input = sys.stdin.read()
        
    if xml_input:
        success = set_fm_xml_clipboard(xml_input)
        sys.exit(0 if success else 1)
    else:
        print("Error: No XML input provided.")
        sys.exit(1)
