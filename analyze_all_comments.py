import json

def load_json(path):
    try:
        with open(path, 'r', encoding='utf-16') as f:
            return json.load(f)
    except:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

def main():
    issue_comments = load_json('comments_issue19.json')
    pr_comments = load_json('comments_pr19_full.json')

    all_comments = []
    
    # 1. Issue Comments (General)
    if isinstance(issue_comments, list):
        for c in issue_comments:
            all_comments.append({
                'type': 'General Issue Comment',
                'user': c.get('user', {}).get('login'),
                'body': c.get('body'),
                'created_at': c.get('created_at'),
                'path': 'N/A'
            })

    # 2. PR Review Comments (Code)
    if isinstance(pr_comments, list):
        for c in pr_comments:
             all_comments.append({
                'type': 'Code Review (Diff)',
                'user': c.get('user', {}).get('login'),
                'body': c.get('body'),
                'created_at': c.get('created_at'),
                'path': f"{c.get('path')}:{c.get('line')}"
            })
            
    # Sort
    all_comments.sort(key=lambda x: x['created_at'])

    print(f"Total Combined Comments: {len(all_comments)}")
    print("-" * 60)
    for c in all_comments:
        user = c['user']
        if user != 'cmc0619': 
             body = c['body']
             if "token constant" in body:
                 print(f"FOUND 'token constant' in comment by {user} at {c['created_at']}")
                 idx = body.find("token constant")
                 print(f"CONTEXT:\n{body[max(0, idx-500):idx+2000]}\n")
                 print("-" * 60)
             else:
                 print(f"Comment by {user} (No 'token constant' found). Length: {len(body)}")

if __name__ == "__main__":
    main()
