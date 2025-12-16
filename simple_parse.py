import json

def main():
    try:
        with open('comments_latest.json', mode='r', encoding='utf-16') as f:
            c = json.load(f)
    except Exception:
        with open('comments_latest.json', mode='r', encoding='utf-8') as f:
            c = json.load(f)
            
    # Sort
    c.sort(key=lambda x: x.get('created_at', ''), reverse=False)
    
    print(f"Total comments: {len(c)}")
    print("\n--- LAST 5 COMMENTS ---")
    for item in c[-5:]:
        created_at = item.get('created_at')
        path = item.get('path')
        line = item.get('line')
        body = item.get('body', '').replace('\n', ' ')
        print(f"[{created_at}] File: {path}:{line}")
        print(f"Comment: {body[:200]}")
        print("-" * 20)

if __name__ == '__main__':
    main()
