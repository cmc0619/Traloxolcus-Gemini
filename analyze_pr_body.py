import json

def load_json(path):
    try:
        with open(path, 'r', encoding='utf-16') as f:
            return json.load(f)
    except:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

def main():
    pr = load_json('pr19_details.json')
    body = pr.get('body', '')
    
    if "token constant" in body:
        print("FOUND 'token constant' in PR BODY!")
        idx = body.find("token constant")
        print(f"CONTEXT:\n{body[max(0, idx-500):idx+2000]}\n")
    else:
        print("NOT FOUND in PR Body.")

if __name__ == "__main__":
    main()
