import os
import sys
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

def generate_db_design(prompt):
    api_key = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")
    if not api_key:
        print(json.dumps({"error": "API Key not found in .env"}))
        return

    client = genai.Client(api_key=api_key)
    
    system_instruction = """
    You are an expert FileMaker database architect.
    Design a database structure based on the user's request.
    Return only a JSON object with the following structure:
    {
      "tables": [
        {
          "name": "TableName",
          "fields": [
            {"name": "field_name", "type": "Text|Number|Date|Time|Timestamp|Container|Calculation|Summary"},
            ...
          ]
        }
      ]
    }
    Use simple, descriptive field names.
    Types must be exactly one of: Text, Number, Date, Time, Timestamp, Container, Calculation, Summary.
    Avoid any markdown formatting, only return raw JSON.
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=f"{system_instruction}\n\nUser Request: {prompt}"
        )
        
        text = response.text.strip()
        # Markdownのデコレーション(```json)を削除
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        # パースを確認して出力
        json_data = json.loads(text)
        print(json.dumps(json_data))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # コマンドライン引数をすべて結合（空白まじりのプロンプトに対応）
        user_prompt = " ".join(sys.argv[1:])
        generate_db_design(user_prompt)
    else:
        print(json.dumps({"error": "No prompt provided"}))
