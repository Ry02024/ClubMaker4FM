import os
import sys
import json
from google import genai
from google.genai import types
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
            
            # google-genaiの最新APIを使用
            try:
                # system_instructionをcontentsに含める形式に変更
                full_prompt = f"{system_instruction}\n\n{user_prompt}"
                
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part(text=full_prompt)
                    ],
                    config=types.GenerateContentConfig(
                        temperature=0.3
                    )
                )
            except Exception as api_error:
                # API呼び出しエラーを詳細に記録
                import traceback
                error_trace = traceback.format_exc()
                print(f"API call error: {str(api_error)}", file=sys.stderr)
                print(f"API call traceback: {error_trace}", file=sys.stderr)
                raise
            
            # レスポンスの取得（複数の方法を試す）
            text = None
            if hasattr(response, 'text') and response.text:
                text = response.text.strip()
            elif hasattr(response, 'candidates') and response.candidates:
                # 代替方法: candidatesから取得
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        text = candidate.content.parts[0].text.strip() if hasattr(candidate.content.parts[0], 'text') else None
                    elif hasattr(candidate.content, 'text'):
                        text = candidate.content.text.strip()
            
            if not text:
                # デバッグ情報を出力
                debug_info = {
                    "response_type": str(type(response)),
                    "response_attrs": dir(response),
                    "has_text": hasattr(response, 'text'),
                    "has_candidates": hasattr(response, 'candidates'),
                }
                if hasattr(response, 'candidates') and response.candidates:
                    debug_info["candidate_type"] = str(type(response.candidates[0]))
                    debug_info["candidate_attrs"] = dir(response.candidates[0])
                
                error_msg = f"Response has no accessible text. Debug info: {json.dumps(debug_info, indent=2)}"
                print(error_msg, file=sys.stderr)
                raise ValueError(error_msg)
            
            # マークダウンのコードブロックを除去
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            suggestions = json.loads(text)
            return {"success": True, "suggestions": suggestions}
            
        except Exception as e:
            # エラーの詳細をstderrに出力（デバッグ用）
            import traceback
            error_trace = traceback.format_exc()
            print(f"API key error: {str(e)}", file=sys.stderr)
            print(f"Traceback: {error_trace}", file=sys.stderr)
            continue
    
    return {"success": False, "error": "All API keys failed"}

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Suggest field fixes using AI')
    parser.add_argument('--file', type=str, help='Path to JSON file containing currentFields and context')
    parser.add_argument('data', nargs='?', help='JSON string (deprecated, use --file instead)')
    
    args = parser.parse_args()
    
    try:
        if args.file:
            # 一時ファイルから読み取る
            with open(args.file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif args.data:
            # 後方互換性のため、コマンドライン引数もサポート
            data = json.loads(args.data)
        else:
            print(json.dumps({"success": False, "error": "No input provided. Use --file option or provide JSON string."}, ensure_ascii=False))
            sys.exit(1)
        
        current_fields = data.get("currentFields", [])
        context = data.get("context", "")
        result = suggest_field_fix(current_fields, context)
        print(json.dumps(result, ensure_ascii=True))
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": f"Invalid JSON: {e}"}, ensure_ascii=True))
        sys.exit(1)
    except FileNotFoundError as e:
        print(json.dumps({"success": False, "error": f"File not found: {e}"}, ensure_ascii=True))
        sys.exit(1)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(json.dumps({
            "success": False, 
            "error": f"Unexpected error: {str(e)}",
            "traceback": error_details
        }, ensure_ascii=True))
        # エラー詳細をstderrにも出力（デバッグ用）
        print(f"Error details: {error_details}", file=sys.stderr)
        sys.exit(1)
