import json

def load_json(path):
    try:
        with open(path, 'r', encoding='utf-16') as f:
            return json.load(f)
    except:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

try:
    prs = load_json('open_prs.json')
    if not isinstance(prs, list):
        print(f"Unexpected JSON format: {type(prs)}")
        # If it's a dict, it might be an error from GitHub API
        if isinstance(prs, dict) and 'message' in prs:
             print(f"GitHub API Error: {prs['message']}")
    else:
        for pr in prs:
            print(f"PR #{pr['number']}: {pr['title']} ({pr['head']['ref']})")
except Exception as e:
    print(f"Error: {e}")
