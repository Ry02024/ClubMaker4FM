import os
import sys
import json
from google import genai
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def suggest_field_fix(current_fields, context=""):
    """現在のフィールド一覧を受け取り、AIが理想的な名前・型を提案する"""
    
    keys_str = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY", "")
    if not keys_str:
        return {"success": False, "error": "API key not configured"}
    
    model_name = os.getenv("GOOGLE_GENERATIVE_AI_MODEL", "gemini-2.0-flash-exp")
    api_keys = [k.strip() for k in keys_str.split(",") if k.strip()]
    
    system_instruction = """
    You are a FileMaker database optimization expert.
    Given a list of existing fields, suggest improvements:
    - Rename to clearer, more descriptive Japanese names
    - Use consistent naming conventions (e.g., snake_case with Japanese suffixes)
    - Suggest appropriate data types if the current type seems incorrect
    - Add helpful comments explaining the field's purpose
    
    CRITICAL: DUPLICATE NAME AVOIDANCE
    - Every 'new_name' MUST be unique within the returned list.
    - Every 'new_name' MUST NOT exist in the current list of fields (unless it's the exact field being renamed).
    - If a conflict occurs, append suffixes like '_v2', '_fixed', or '_unique' to ensure uniqueness.
    
    Return ONLY a JSON array matching the input order:
    [
      {
        "old_name": "original field name",
        "new_name": "suggested new name (MUST be unique)",
        "old_type": "original type",
        "new_type": "suggested type (or same if ok)",
        "comment": "brief explanation",
        "should_fix": true/false (true if any change recommended)
      }
    ]
    
    Do NOT add markdown formatting. Return raw JSON only.
    """
    
    for api_key in api_keys:
        try:
            client = genai.Client(api_key=api_key)
            
            user_prompt = f"""
現在のフィールド一覧:
{json.dumps(current_fields, ensure_ascii=False, indent=2)}

コンテキスト: {context if context else "特になし"}

上記のフィールドを最適化してください。日本語で分かりやすい名前に変更し、適切な型を提案してください。
"""
            
            response = client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config={
                    "system_instruction": system_instruction,
                    "temperature": 0.3
                }
            )
            
            text = response.text.strip()
            
            # マークダウンのコードブロックを除去
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            suggestions = json.loads(text)
            return {"success": True, "suggestions": suggestions}
            
        except Exception:
            continue
    
    return {"success": False, "error": "All API keys failed"}

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        try:
            data = json.loads(sys.argv[1])
            current_fields = data.get("currentFields", [])
            context = data.get("context", "")
            result = suggest_field_fix(current_fields, context)
            print(json.dumps(result, ensure_ascii=True))
        except json.JSONDecodeError as e:
            print(json.dumps({"success": False, "error": f"Invalid JSON: {e}"}, ensure_ascii=True))
    else:
        print(json.dumps({"success": False, "error": "No input provided"}, ensure_ascii=False))
