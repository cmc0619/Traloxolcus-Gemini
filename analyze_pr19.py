import json

def main():
    try:
        with open('comments_pr19_latest.json', mode='r', encoding='utf-16') as f:
            comments = json.load(f)
    except Exception:
        with open('comments_pr19_latest.json', mode='r', encoding='utf-8') as f:
            comments = json.load(f)

    # Sort by creation time
    comments.sort(key=lambda x: x.get('created_at', ''))

    print(f"Total Comments on PR 19: {len(comments)}")
    print("-" * 50)
    
    for c in comments:
        user = c.get('user', {}).get('login')
        body = c.get('body', '')
        path = c.get('path')
        line = c.get('line')
        created_at = c.get('created_at')
        
        print(f"[{created_at}] {user}")
        print(f"File: {path}:{line}")
        print(f"Content: {body}\n")
        print("-" * 50)

if __name__ == "__main__":
    main()
