import urllib.request
import json

base_url = "https://api.github.com/repos/cmc0619/Traloxolcus-Gemini"
pr_num = 22
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/vnd.github.v3+json"
}

def get_json(url):
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

print(f"--- Fecthing Data for PR #{pr_num} ---")

# Helper to safe print
def safe_print(s):
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode('ascii', 'replace').decode('ascii'))

# 1. General Comments
comments = get_json(f"{base_url}/issues/{pr_num}/comments")
print(f"\nGeneral Comments ({len(comments)}):")
for c in comments:
    safe_print(f"[{c['user']['login']}] {c['body']}")

# 2. Reviews
reviews = get_json(f"{base_url}/pulls/{pr_num}/reviews")
print(f"\nReviews ({len(reviews)}):")
for r in reviews:
    safe_print(f"[{r['user']['login']}] {r['state']}: {r.get('body', '')}")

# 3. Code Comments
code_comments = get_json(f"{base_url}/pulls/{pr_num}/comments")
print(f"\nCode Comments ({len(code_comments)}):")
for c in code_comments:
    safe_print(f"[{c['user']['login']}] {c['path']}:{c.get('line', '?')} - {c['body']}")
