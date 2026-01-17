import os
import sys
import json
from google import genai
from dotenv import load_dotenv

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
    
    # 登録されている全キーを順番に試す
    for i, api_key in enumerate(api_keys):
        try:
            client = genai.Client(api_key=api_key)
            
            system_instruction = """
            You are an expert FileMaker database architect and UI/UX designer.
            Design a database structure and a modern UI layout based on the user's request.
            Return only a JSON object with the following structure:
            {
              "tables": [
                {
                  "name": "TableName",
                  "fields": [
                    {"name": "field_name", "type": "Text|Number|Date|Time|Timestamp|Container|Calculation|Summary"}
                  ]
                }
              ],
              "layouts": [
                {
                  "name": "LayoutName",
                  "table": "TableName",
                  "type": "dashboard|form|list",
                  "style": {
                    "primaryColor": "#HEX",
                    "accentColor": "#HEX",
                    "theme": "dark|light|glass"
                  },
                  "elements": [
                    {"field": "field_name", "label": "Label Text", "grid": {"x": 0, "y": 0, "w": 4, "h": 1}}
                  ]
                }
              ]
            }
            Use simple, descriptive names.
            Grid values: x(0-11), y(0+), w(1-12), h(1+).
            Colors should be modern, vibrant, and professional.
            Avoid any markdown formatting, only return raw JSON.
            """

            response = client.models.generate_content(
                model=model_name,
                contents=f"{system_instruction}\n\nUser Request: {prompt}"
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
    if len(sys.argv) > 1:
        user_prompt = " ".join(sys.argv[1:])
        generate_db_design(user_prompt)
    else:
        print(json.dumps({"error": "No prompt provided"}))
