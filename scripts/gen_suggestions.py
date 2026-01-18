import json
import os
import sys

# Add scripts directory to path
sys.path.append(os.path.join(os.getcwd(), 'scripts'))
import suggest_field_fix

def main():
    with open('data/current_fields.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        fields = data.get('fields', [])
    
    # Get suggestions
    result = suggest_field_fix.suggest_field_fix(fields)
    
    if result.get('success'):
        with open('data/suggestions.json', 'w', encoding='utf-8') as f:
            json.dump(result.get('suggestions'), f, ensure_ascii=False, indent=2)
        print("Suggestions saved to data/suggestions.json")
    else:
        print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    main()
