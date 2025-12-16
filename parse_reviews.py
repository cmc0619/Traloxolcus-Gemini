import json
import os

def load_json(filename):
    # PowerShell redirection in Windows often creates UTF-16LE with BOM
    try:
        with open(filename, 'r', encoding='utf-16') as f:
            return json.load(f)
    except (UnicodeError, json.JSONDecodeError):
        # Fallback to UTF-8
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)

def main():
    comments = load_json("review_comments.json")
    print(f"Total Comment Objects: {len(comments)}")
    
    print("\n--- DETAILED COMMENTS ---")
    for c in comments:
        path = c.get('path', 'unknown')
        line = c.get('line', '?')
        body = c.get('body', '').replace('\n', ' ')
        user = c.get('user', {}).get('login', 'unknown')
        
        print(f"User: {user}")
        print(f"File: {path}:{line}")
        print(f"Comment: {body[:200]}...") # Truncate for readability
        print("-" * 40)

if __name__ == "__main__":
    main()
