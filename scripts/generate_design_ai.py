import os
import sys
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
from field_parser import parse_field_names, extract_table_name

load_dotenv()

def generate_db_design(prompt):
    # .env から全てのキーを取得
    keys_str = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY", "")
    if not keys_str:
        print(json.dumps({"error": "API Key not found in .env"}))
        return

    # モデル名を .env から取得 (デフォルトは gemini-2.0-flash-exp)
    model_name = os.getenv("GOOGLE_GENERATIVE_AI_MODEL", "gemini-2.0-flash-exp")

    # 空白を除去しつつリスト化
    api_keys = [k.strip() for k in keys_str.split(",") if k.strip()]
    
    errors = []
    
    # ========================================
    # Step 1: プログラムでフィールド名を抽出（パーサー）
    # ========================================
    print(f"[Parser] プロンプト受信: {len(prompt)} 文字", file=sys.stderr)
    field_list = parse_field_names(prompt)
    table_name = extract_table_name(prompt)
    print(f"[Parser] テーブル名: {table_name}", file=sys.stderr)
    print(f"[Parser] 抽出フィールド数: {len(field_list)}", file=sys.stderr)
    
    # フィールドが抽出できなかった場合は、従来通りAIに任せる
    if not field_list:
        # 抽象的な指示の場合はAIが考える
        print("[Parser] フィールドが抽出されませんでした。AIに任せます。", file=sys.stderr)
        clean_prompt = prompt
        use_parser = False
    else:
        # クリーンなリストをAIに渡す
        print(f"[Parser] 抽出フィールド: {field_list[:10]}{'...' if len(field_list) > 10 else ''}", file=sys.stderr)
        use_parser = True
        clean_prompt = f"""
【テーブル名】: {table_name}

【フィールドリスト（全{len(field_list)}件）】:
{json.dumps(field_list, ensure_ascii=False)}

上記のフィールドを全て使用してデータベースとUIを設計してください。
フィールド名は一字一句変えないでください。
"""
    
    print(f"[AI] モデル: {model_name}", file=sys.stderr)
    
    # 登録されている全キーを順番に試す
    for i, api_key in enumerate(api_keys):
        try:
            client = genai.Client(api_key=api_key)
            
            if use_parser:
                # パーサー使用時：簡素化されたプロンプト
                system_instruction = """
あなたはFileMakerのプロフェッショナルです。
渡された【フィールドリスト】の全てを使用して設計してください。

[ルール]
1. リストにある名前は一字一句変えず、全てフィールド名として採用すること。
2. フィールドタイプは、名前から推測して適切に割り当てる（例: flg_* -> Number, var_* -> Text, *_drpt -> Text）。
3. UIレイアウトは12カラムグリッドで作成し、関連するフィールドをグループ化すること。
4. JSON以外の説明文は一切出力しないこと。
5. フィールドは省略せず、必ず全て含めること。

Return only a JSON object with the following structure:
{
  "thoughts": ["日本語でAIの思考過程を記述"],
  "tables": [
    {
      "name": "テーブル名",
      "fields": [
        {"name": "フィールド名", "type": "Text|Number|Date|Time|Timestamp|Container|Calculation|Summary"}
      ]
    }
  ],
  "layouts": [
    {
      "name": "レイアウト名",
      "table": "テーブル名",
      "type": "dashboard|form|list",
      "style": {"primaryColor": "#HEX", "accentColor": "#HEX", "theme": "dark|light|glass"},
      "elements": [
        {"field": "フィールド名", "label": "ラベル", "grid": {"x": 0, "y": 0, "w": 4, "h": 1}}
      ]
    }
  ]
}
Grid values: x(0-11), y(0+), w(1-12), h(1+).
Avoid any markdown formatting, only return raw JSON.
"""
            else:
                # パーサー未使用時：従来のプロンプト（抽象的な指示用）
                system_instruction = """
You are an expert FileMaker database architect and UI/UX designer.
Design a database structure and a modern UI layout based on the user's request.

[UI/UX Design Principles]
- Use a 12-column grid system (x: 0-11).
- Group related fields together visually.
- Ensure clear hierarchy.
- Use professional, modern color palettes.

Return only a JSON object with the following structure:
{
  "thoughts": ["AIの思考過程（日本語）"],
  "tables": [{"name": "TableName", "fields": [{"name": "field_name", "type": "Text|Number|Date|..."}]}],
  "layouts": [{"name": "LayoutName", "table": "TableName", "type": "dashboard|form|list", "style": {...}, "elements": [...]}]
}
Use Japanese for 'thoughts'. Avoid markdown, only return raw JSON.
"""

            # google-genaiの最新APIを使用
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part(text=f"{system_instruction}\n\nUser Request: {clean_prompt}")
                ],
                config=types.GenerateContentConfig(
                    temperature=0.3
                )
            )
            
            text = response.text.strip()
            
            # JSON部分を抽出
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                text = json_match.group(0)
            
            json_data = json.loads(text)
            
            # 構造の補正
            if isinstance(json_data, list):
                json_data = {"tables": json_data}
            elif "design" in json_data and "tables" in json_data["design"]:
                json_data = json_data["design"]
            
            # パーサー情報を追加（デバッグ用）
            if use_parser:
                json_data["_parser_info"] = {
                    "used": True,
                    "extracted_fields": len(field_list),
                    "table_name": table_name
                }
            
            # 成功したらJSONを出力して終了
            print(json.dumps(json_data))
            return

        except Exception as e:
            err_msg = str(e)
            errors.append(f"Key {i+1} ({model_name}): {err_msg}")
            
            # 429 (クォータ切れ) の場合は1.5秒待機してから次へ
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                import time
                time.sleep(1.5)
            continue

    # 全てのキーが失敗した場合
    print(json.dumps({
        "error": "All API keys failed.",
        "details": errors
    }))

if __name__ == "__main__":
    user_prompt = None
    
    # --file オプションでファイルからプロンプトを読み込む
    if len(sys.argv) > 2 and sys.argv[1] == "--file":
        file_path = sys.argv[2]
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                user_prompt = f.read()
        except Exception as e:
            print(json.dumps({"error": f"Failed to read prompt file: {e}"}))
            sys.exit(1)
    elif len(sys.argv) > 1:
        user_prompt = " ".join(sys.argv[1:])
    
    if user_prompt:
        generate_db_design(user_prompt)
    else:
        print(json.dumps({"error": "No prompt provided"}))
