import json
import base64
import hashlib
import os
import getpass
from cryptography.fernet import Fernet

def decrypt_backup():
    print("=== Backup Decryption Tool ===")
    
    # 1. Ask for file path
    file_path = input("Enter path to backup file (drag & drop file here): ").strip().replace('"', '')
    
    if not os.path.exists(file_path):
        print("Error: File not found!")
        return

    try:
        with open(file_path, "r") as f:
            backup_data = json.load(f)
            
        if not backup_data.get("is_encrypted"):
            print("This file is NOT encrypted. You can open it directly.")
            return

        # 2. Ask for password
        password = getpass.getpass("Enter decryption password: ")
        
        # 3. Decrypt
        salt = base64.b64decode(backup_data["salt"])
        kdf = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        key = base64.urlsafe_b64encode(kdf)
        f = Fernet(key)
        
        decrypted_bytes = f.decrypt(backup_data["data"].encode())
        decrypted_json = json.loads(decrypted_bytes.decode('utf-8'))
        
        # 4. Save
        output_file = file_path.replace(".json", "_decrypted.json")
        with open(output_file, "w") as f:
            json.dump(decrypted_json, f, indent=4)
            
        print(f"\n✅ Success! Decrypted data saved to:\n{output_file}")
        
    except Exception as e:
        print(f"\n❌ Decryption Failed: {e}")
        print("Make sure the password is correct.")

if __name__ == "__main__":
    try:
        decrypt_backup()
    except KeyboardInterrupt:
        print("\nCancelled.")
    input("\nPress Enter to exit...")
