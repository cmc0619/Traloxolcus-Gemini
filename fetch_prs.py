import urllib.request
import json
import sys

url = "https://api.github.com/repos/cmc0619/Traloxolcus-Gemini/pulls?state=open"
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/vnd.github.v3+json"
}

try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        data = response.read()
        prs = json.loads(data)
        
        print(f"Found {len(prs)} open PRs:")
        for pr in prs:
           print(f"PR #{pr['number']}: {pr['title']} - {pr['html_url']}")
           print(f"Head: {pr['head']['ref']}")
           
except Exception as e:
    print(f"Error fetching PRs: {e}")
