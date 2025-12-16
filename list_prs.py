import json

try:
    with open('open_prs.json', 'r', encoding='utf-8') as f:
        prs = json.load(f)
        
    for pr in prs:
        print(f"PR #{pr['number']}: {pr['title']} ({pr['head']['ref']})")
except Exception as e:
    print(f"Error: {e}")
