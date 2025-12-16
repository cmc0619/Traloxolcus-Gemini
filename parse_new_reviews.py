import json
import os
from datetime import datetime

def load_json(filename):
    # PowerShell redirection in Windows often creates UTF-16LE with BOM
    try:
        with open(filename, 'r', encoding='utf-16') as f:
            return json.load(f)
    except (UnicodeError, json.JSONDecodeError):
        # Fallback to UTF-8
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)

def parse_iso(date_str):
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except:
        return datetime.min

def main():
    comments = load_json("comments_new.json")
    
    # Sort by submitted_at/created_at
    comments.sort(key=lambda x: parse_iso(x.get('created_at', '') or x.get('submitted_at', '')))
    
    print(f"Total Comment Objects: {len(comments)}")
    
    print("\n--- DETAILED COMMENTS (Sorted Chronologically) ---")
    for c in comments:
        path = c.get('path', 'unknown')
        line = c.get('line', '?')
        body = c.get('body', '').replace('\n', ' ')
        user = c.get('user', {}).get('login', 'unknown')
        created_at = c.get('created_at', 'unknown')
        
        print(f"[{created_at}] User: {user}")
        print(f"File: {path}:{line}")
        print(f"Comment: {body[:200]}...") # Truncate for readability
        print("-" * 40)

if __name__ == "__main__":
    main()
