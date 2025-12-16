import json
import glob

def search_json_files(keyword):
    files = glob.glob('*.json')
    print(f"Searching for '{keyword}' in {files}...")
    
    found_count = 0
    for filename in files:
        try:
            # Try UTF-16 first as that's what PowerShell redirection usually produces
            try:
                with open(filename, 'r', encoding='utf-16') as f:
                    data = json.load(f)
            except:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
            if not isinstance(data, list):
                continue
                
            for item in data:
                body = item.get('body', '')
                if keyword.lower() in body.lower():
                    print(f"\n--- Found in {filename} ---")
                    print(f"File: {item.get('path')}:{item.get('line')}")
                    print(f"Comment: {body}")
                    found_count += 1
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            
    print(f"\nTotal matches found: {found_count}")

if __name__ == "__main__":
    search_json_files("pydantic")
