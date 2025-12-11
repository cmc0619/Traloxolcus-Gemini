import json
import glob
import sys
import io

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def parse_reviews():
    comments = []
    
    # Process Review Comments (Inline code comments)
    try:
        try:
            with open('pr_reviews.json', 'r', encoding='utf-8') as f:
                reviews = json.load(f)
        except UnicodeError:
            with open('pr_reviews.json', 'r', encoding='utf-16') as f:
                reviews = json.load(f)
                
        if isinstance(reviews, list):
                for r in reviews:
                    user = r.get('user', {}).get('login', 'Unknown')
                    # User asked for CodeRabbit / Codex. Usually bots.
                    body = r.get('body', '')
                    # Filter for likely AI/Bot content or specific keywords if needed
                    # For now, let's grab everything that looks like a bot report or from specific users.
                    # Or just grab all and I'll filter in the LLM. 
                    # But 300k of text is too much.
                    # Let's filter for 'rabbit', 'codex', or 'review' in user OR 'walkthrough' in body.
                    
                    is_bot = r.get('user', {}).get('type') == 'Bot' or 'rabbit' in user.lower() or 'codex' in user.lower()
                    
                    if is_bot:
                        comments.append({
                            'type': 'Review',
                            'pr': r.get('pull_request_url', '').split('/')[-1],
                            'file': r.get('path'),
                            'line': r.get('line'),
                            'user': user,
                            'body': body,
                            'created_at': r.get('created_at')
                        })
    except Exception as e:
        print(f"Error reading reviews: {e}")

    # Process Issue Comments (General PR comments)
    try:
        try:
            with open('pr_comments.json', 'r', encoding='utf-8') as f:
                issues = json.load(f)
        except UnicodeError:
            with open('pr_comments.json', 'r', encoding='utf-16') as f:
                issues = json.load(f)

        if isinstance(issues, list):
            for i in issues:
                user = i.get('user', {}).get('login', 'Unknown')
                is_bot = i.get('user', {}).get('type') == 'Bot' or 'rabbit' in user.lower() or 'codex' in user.lower()
                
                if is_bot:
                    comments.append({
                        'type': 'Comment',
                        'pr': i.get('issue_url', '').split('/')[-1],
                        'file': 'General',
                        'line': '-',
                        'user': user,
                        'body': i.get('body', ''),
                        'created_at': i.get('created_at')
                    })
    except Exception as e:
        print(f"Error reading comments: {e}")

    # Sort by date
    comments.sort(key=lambda x: x['created_at'], reverse=True)

    print(f"Found {len(comments)} bot comments.\n")
    
    for c in comments[:20]: # Limit to 20 most recent for now to avoid token overflow
        print(f"--- PR #{c['pr']} [{c['type']}] by {c['user']} at {c['created_at']} ---")
        if c['file'] != 'General':
            print(f"File: {c['file']} : {c['line']}")
        print(f"{c['body'][:500]} ...\n")

if __name__ == "__main__":
    parse_reviews()
