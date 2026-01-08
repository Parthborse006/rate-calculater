import urllib.request
import json
import urllib.parse

class SyncManager:
    def __init__(self):
        self.enabled = False
        self.url = ""
        self.headers = {}
        try:
            # CREDENTIALS
            URL = "https://jlidoznndxqhvtvgwqnj.supabase.co"
            KEY = "sb_publishable_8RX9HzSr7aKQfh6WTjlSqg_n6tlaYDF"
            
            if "YOUR_" not in URL:
                self.url = URL
                self.headers = {
                    "apikey": KEY,
                    "Authorization": f"Bearer {KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "resolution=merge-duplicates"
                }
                self.enabled = True
                print("Online Sync (StdLib): Enabled")
        except Exception as e:
            print(f"Online Sync Error (Init): {e}")

    def pull_data(self, user_id):
        if not self.enabled or not user_id: return None
        try:
            safe_id = urllib.parse.quote(f"ilike.*{user_id}*")
            # Query the user_data table for the specific user_id
            endpoint = f"{self.url}/rest/v1/user_data?user_id={safe_id}&select=user_id"
            
            req = urllib.request.Request(endpoint, method='GET')
            for k, v in self.headers.items():
                req.add_header(k, v)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    content = response.read().decode('utf-8')
                    records = json.loads(content)
                    return records
        except Exception as e:
            print(f"Online Sync Pull Error: {e}")
        return None

if __name__ == "__main__":
    manager = SyncManager()
    user_to_check = "yashborse005"
    print(f"Checking for user: {user_to_check}...")
    result = manager.pull_data(user_to_check)
    
    if result and len(result) > 0:
        print(f"SUCCESS: Match found in table 'user_data'!")
        print(f"Record: {result[0]}")
    else:
        print(f"FAILURE: User '{user_to_check}' NOT found in table.")
