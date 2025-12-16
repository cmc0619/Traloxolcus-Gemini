import json
from datetime import datetime

def load_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_iso(date_str):
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except:
        return datetime.min

def main():
    comments = load_json("comments_latest.json")
    # Filters for comments created AFTER the last known check (approx 6:42Z) just to be sure we see NEW stuff
    # Or just sort and show the last 5
    
    comments.sort(key=lambda x: parse_iso(x.get('created_at', '') or x.get('submitted_at', '')))
    
    print(f"Total Comment Objects: {len(comments)}")
    print("\n--- NEWEST COMMENTS (Last 5) ---")
    
    for c in comments[-5:]:
        path = c.get('path', 'unknown')
        line = c.get('line', '?')
        body = c.get('body', '').replace('\n', ' ')
        user = c.get('user', {}).get('login', 'unknown')
        created_at = c.get('created_at', 'unknown')
        
        print(f"[{created_at}] User: {user}")
        print(f"File: {path}:{line}")
        print(f"Comment: {body[:300]}...") 
        print("-" * 40)

if __name__ == "__main__":
    main()
