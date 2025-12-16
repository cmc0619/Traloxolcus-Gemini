
import urllib.request
import json
import sys

url = "https://api.github.com/repos/cmc0619/Traloxolcus-Gemini/pulls/22"
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/vnd.github.v3+json"
}

try:
    print(f"Fetching {url}...")
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        data = response.read()
        pr = json.loads(data)
        
        print(f"--- PR #{pr['number']}: {pr['title']} ---")
        body = pr['body']
        # Encode to ascii/utf-8 and decode ignoring errors to avoid charmap issues in windows console
        safe_body = body.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
        print(f"Description:\n{safe_body}")
        print("---------------------------------------------------")
        
except Exception as e:
    print(f"Error fetching PR: {e}")
