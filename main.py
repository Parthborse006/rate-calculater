
import flet as ft
from datetime import datetime
import json
import os
import smtplib
import random
import hashlib
import secrets
import re
import time
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Try to import cryptography, use fallback if not available (Android APK)
try:
    from cryptography.fernet import Fernet
    import base64
    CRYPTO_AVAILABLE = True
except ImportError:
    # Fallback for Android - use simple base64 encoding
    import base64
    CRYPTO_AVAILABLE = False
    print("Warning: cryptography module not available. Using base64 fallback for encryption.")

def hash_password(password):
    """Hash a password for storing."""
    salt = os.urandom(16)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + '$' + pwdhash.hex()

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    try:
        salt_hex, hash_hex = stored_password.split('$')
        salt = bytes.fromhex(salt_hex)
        pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
        return pwdhash.hex() == hash_hex
    except Exception:
        return False

def main(page: ft.Page):
    page.title = "Interest Calculator"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window_width = 400
    page.window_height = 700
    page.window_icon = "assets/icon.png"
    
    # Custom Colors
    primary_color = "#6200EE"
    background_color = "#F5F5F5"
    card_color = "#FFFFFF"

    page.bgcolor = background_color

    # Data Persistence
    DATA_FILE = "data.json"
    USERS_FILE = "users.json"
    all_data = {}
    all_users = {}
    current_user = [None] # List for mutable closure reference
    
    # Session Management
    SESSION_TIMEOUT = 900  # 15 minutes of inactivity
    last_activity = [time.time()]
    session_active = [True]  # To control the thread
    
    def reset_session():
        """Reset the session timer on user activity"""
        last_activity[0] = time.time()
    
    def check_session():
        """Background thread to check for session timeout"""
        while session_active[0]:
            time.sleep(60)  # Check every minute
            if not session_active[0]:  # Check again after sleep
                break
            if current_user[0]:
                elapsed = time.time() - last_activity[0]
                if elapsed > SESSION_TIMEOUT:
                    print(f"Session timeout: {elapsed}s > {SESSION_TIMEOUT}s")
                    
                    # Log out (thread-safe update)
                    current_user[0] = None
                    
                    # Only attempt UI update if session is still active
                    if not session_active[0]:
                        break
                    
                    # Schedule UI update
                    def logout_ui():
                        try:
                            items_list_view.controls.clear()
                            show_login_screen()
                            page.snack_bar = ft.SnackBar(content=ft.Text("Session expired due to inactivity"))
                            page.snack_bar.open = True
                            page.update()
                        except Exception as e:
                            # Silently handle errors during shutdown
                            print(f"Session timeout UI update skipped: {e}")
                    
                    # Try to update UI, but don't fail if app is shutting down
                    try:
                        logout_ui()
                    except Exception as e:
                        print(f"Error handling timeout: {e}")
    
    # Start session monitor
    session_thread = threading.Thread(target=check_session, daemon=True)
    session_thread.start()
    
    # --- Online Sync (Upsert Logic) ---
    # --- Online Sync (REST API Logic - Android Optimized) ---
    # --- Online Sync (Standard Lib - No Dependencies) ---
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

        def push_data(self, user_id, data, callback=None):
            if not self.enabled or not user_id: 
                if callback: callback("Sync Disabled or Invalid User")
                return
            
            def _push():
                try:
                    import urllib.request
                    import json
                    
                    endpoint = f"{self.url}/rest/v1/user_data"
                    payload = json.dumps({"user_id": user_id, "data": data}).encode('utf-8')
                    
                    req = urllib.request.Request(endpoint, data=payload, method='POST')
                    for k, v in self.headers.items():
                        req.add_header(k, v)
                    req.add_header("Prefer", "resolution=merge-duplicates")
                    
                    with urllib.request.urlopen(req, timeout=10) as response:
                        if response.status in [200, 201, 204]:
                            print(f"Online Sync: Pushed data for {user_id}")
                            if callback: callback(f"Synced Successfully! ({len(data)} items)")
                        else:
                             print(f"Online Sync Failed: {response.status}")
                             if callback: callback(f"Sync Error: HTTP {response.status}")
                             
                except Exception as e:
                    print(f"Online Sync Error: {e}")
                    if callback: callback(f"Sync Error: {str(e)}")
            
            threading.Thread(target=_push, daemon=True).start()

        def pull_data(self, user_id):
            if not self.enabled or not user_id: return None
            try:
                import urllib.request
                import json
                
                # Encode params manually since urllib doesn't do it comfortably
                # endpoint?user_id=eq.ID&select=data
                # We need to URL encode the ID if it has special chars
                import urllib.parse
                safe_id = urllib.parse.quote(f"eq.{user_id}")
                endpoint = f"{self.url}/rest/v1/user_data?user_id={safe_id}&select=data"
                
                req = urllib.request.Request(endpoint, method='GET')
                for k, v in self.headers.items():
                    req.add_header(k, v)
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        content = response.read().decode('utf-8')
                        records = json.loads(content)
                        if records and len(records) > 0:
                            print(f"Online Sync: Pulled data for {user_id}")
                            return records[0]["data"]
            except Exception as e:
                print(f"Online Sync Pull Error: {e}")
            return None

    sync_manager = SyncManager()

    # Firebase Setup
    firebase_db = [None]
    


    def load_data():
        try:
            stored_data = page.client_storage.get("app_data")
            if stored_data:
                return json.loads(stored_data)
        except Exception as e:
            print(f"Error loading data: {e}")
        return {}

    def sync_user_to_cloud(user_id, callback=None):
        if not user_id: return
        
        # Package Profile + Items
        profile = all_users.get(user_id, {}).copy() # Copy to avoid mutating local state safely
        if "login_id" not in profile:
            profile["login_id"] = user_id # Force Inject ID for legacy users
            
        items = all_data.get(user_id, [])
        
        full_package = {
            "profile": profile,
            "items": items
        }
        
        # Push to cloud
        sync_manager.push_data(user_id, full_package, callback)

    def save_data():
        # Save to client storage (works on Android without special perms)
        try:
            page.client_storage.set("app_data", json.dumps(all_data))
            
            # Auto-Sync on save
            if current_user[0]:
                sync_user_to_cloud(current_user[0])
        except Exception as e:
            print(f"Error saving data: {e}")
        
        


    
    def load_users():
        try:
            stored_users = page.client_storage.get("app_users")
            if stored_users:
                return json.loads(stored_users)
        except Exception as e:
            print(f"Error loading users: {e}")
        return {}

    def save_users():
        # Save to client storage (works on Android without special perms)
        try:
            page.client_storage.set(APP_USERS_KEY, json.dumps(all_users))
            # Auto-Sync on user profile update
            if current_user[0]:
                sync_user_to_cloud(current_user[0])
        except Exception as e:
            print(f"Error saving users: {e}")
        
        
    def migrate_legacy_data():
        """Migrate old file-based data to client_storage"""
        # Only migrate if client_storage is empty
        if not page.client_storage.get("app_users"):
             if os.path.exists(USERS_FILE):
                try:
                    with open(USERS_FILE, "r") as f:
                        old_users = json.load(f)
                    page.client_storage.set("app_users", json.dumps(old_users))
                    print(f"Migrated {len(old_users)} users to secure storage.")
                except Exception as e:
                    print(f"Migration error (Users): {e}")

        if not page.client_storage.get("app_data"):
             if os.path.exists(DATA_FILE):
                try:
                    with open(DATA_FILE, "r") as f:
                        old_data = json.load(f)
                    page.client_storage.set("app_data", json.dumps(old_data))
                    print(f"Migrated legacy data for {len(old_data)} users.")
                except Exception as e:
                    print(f"Migration error (Data): {e}")

    # Run migration on startup
    migrate_legacy_data()

    # Load data from storage into memory
    all_data = load_data()
    all_users = load_users()
    print(f"Loaded {len(all_users)} users and data for {len(all_data)} accounts.")
    


    
    # Security Functions
    def hash_password(password):
        """Hash password with salt using PBKDF2"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}${pwd_hash.hex()}"
    
    def verify_password(stored_password, provided_password):
        """Verify password against stored hash"""
        try:
            salt, pwd_hash = stored_password.split('$')
            new_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt.encode(), 100000)
            return new_hash.hex() == pwd_hash
        except:
            # Fallback for old plain-text passwords (migration)
            return stored_password == provided_password
    
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_phone(phone):
        """Validate phone number format"""
        # Remove spaces and dashes
        phone = phone.replace(' ', '').replace('-', '')
        pattern = r'^\+?1?\d{10,15}$'
        return re.match(pattern, phone) is not None
    
    def validate_password_strength(password):
        """Check password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
        return True, "Strong password"
    
    # Rate Limiting
    login_attempts = {}  # {username: [timestamp1, timestamp2, ...]}
    
    def check_rate_limit(username):
        """Check if user has exceeded login attempt limit"""
        now = time.time()
        if username in login_attempts:
            # Remove attempts older than 15 minutes
            login_attempts[username] = [t for t in login_attempts[username] if now - t < 900]
            
            if len(login_attempts[username]) >= 5:
                return False, "Too many login attempts. Please try again in 15 minutes."
        return True, ""
    
    def record_login_attempt(username):
        """Record a login attempt"""
        if username not in login_attempts:
            login_attempts[username] = []
        login_attempts[username].append(time.time())
    
    def clear_login_attempts(username):
        """Clear login attempts after successful login"""
        if username in login_attempts:
            login_attempts[username] = []
    
    # Export/Import Functions
    encryption_password_field = ft.TextField(label="Encryption Password (Optional)", password=True, can_reveal_password=True)
    

    
    # Export Data Storage (Mutable)
    current_export_data = [None]
    

    
    # Load configuration
    def load_config():
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    return json.load(f)
        except:
            pass
        return {"email": {"enabled": False}, "sms": {"enabled": False}}
    
    config = load_config()


    
    # OTP Storage
    otp_storage = {}  # {email/phone: {"otp": "123456", "timestamp": ...}}
    
    # Verification Functions
    def send_email_otp(email, otp):
        if not config.get("email", {}).get("enabled", False):
            print(f"[DEMO MODE] Email OTP for {email}: {otp}")
            return True
        
        try:
            msg = MIMEMultipart()
            msg['From'] = config["email"]["sender_email"]
            msg['To'] = email
            msg['Subject'] = "Interest Calculator - Verification Code"
            
            body = f"""Your verification code is: {otp}
            
This code will expire in 10 minutes.
            
If you didn't request this code, please ignore this email."""
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(config["email"]["smtp_server"], config["email"]["smtp_port"])
            server.starttls()
            server.login(config["email"]["sender_email"], config["email"]["sender_password"])
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Email error: {e}")
            return False
    
    def send_sms_otp(phone, otp):
        if not config.get("sms", {}).get("enabled", False):
            print(f"[DEMO MODE] SMS OTP for {phone}: {otp}")
            return True
        
        try:
            from twilio.rest import Client
            client = Client(
                config["sms"]["twilio_account_sid"],
                config["sms"]["twilio_auth_token"]
            )
            
            message = client.messages.create(
                body=f"Your Interest Calculator verification code is: {otp}",
                from_=config["sms"]["twilio_phone"],
                to=phone
            )
            return True
        except ImportError:
            print(f"[ANDROID] Twilio not available. SMS OTP for {phone}: {otp}")
            return True  # Return True in demo mode
        except Exception as e:
            print(f"SMS error: {e}")
            return False
    
    def generate_otp():
        return str(random.randint(100000, 999999))
    
    # Firebase Initialization (moved to top of main)


    def refresh_click(e):
        print("Refresh button clicked!")  # Debug print
        reset_session()
        # Reset all fields
        principal_field.value = ""
        rate_field.value = "1.5"
        date_button.text = "Select Start Date"
        result_text.value = ""
        result_container.opacity = 0
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Form refreshed!"),
            action="OK",
        )
        page.snack_bar.open = True
        page.update()

    def calculate_interest_helper(principal, rate, start_date):
        current_date = datetime.now()
        days_diff = (current_date - start_date).days
        interest_rate = rate / 100
        daily_interest = (principal * interest_rate) / 30
        total_interest = daily_interest * days_diff
        final_amount = principal + total_interest
        return days_diff, total_interest, final_amount

    def calculate_click(e):
        reset_session()
        try:
            if not principal_field.value:
                result_text.value = "Please enter principal amount"
                result_text.color = ft.Colors.RED
                page.update()
                return
            
            if not date_picker.value:
                 result_text.value = "Please select a start date"
                 result_text.color = ft.Colors.RED
                 page.update()
                 return
            
            if not rate_field.value:
                result_text.value = "Please enter interest rate"
                result_text.color = ft.Colors.RED
                page.update()
                return

            principal = float(principal_field.value)
            rate = float(rate_field.value)
            start_date = date_picker.value
            
            days_diff, total_interest, final_amount = calculate_interest_helper(principal, rate, start_date)
            
            result_text.value = (
                f"Days: {days_diff}\n"
                f"Interest: ₹{total_interest:.2f}\n"
                f"Total: ₹{final_amount:.2f}"
            )
            result_text.color = ft.Colors.BLACK
            
            # Animate result container
            result_container.opacity = 1
            result_container.update()
            
        except ValueError:
            result_text.value = "Invalid input"
            result_text.color = ft.Colors.RED
        
        page.update()

    # Date Picker
    date_picker = ft.DatePicker(
        on_change=lambda e: setattr(date_button, "text", e.control.value.strftime('%Y-%m-%d')) or date_button.update(),
    )
    # page.overlay.append(date_picker) # Not needed with page.open()
    
    date_button = ft.ElevatedButton(
        "Select Start Date",
        icon=ft.Icons.CALENDAR_TODAY,
        on_click=lambda _: page.open(date_picker),
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=primary_color,
            shape=ft.RoundedRectangleBorder(radius=10),
        ),
        height=50,
    )

    principal_field = ft.TextField(
        label="Principal Amount",
        prefix_text="₹ ",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=10,
        filled=True,
        bgcolor=card_color,
    )

    rate_field = ft.TextField(
        label="Interest Rate (%)",
        value="1.5",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=10,
        filled=True,
        bgcolor=card_color,
    )

    calculate_btn = ft.ElevatedButton(
        text="Calculate",
        on_click=calculate_click,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=primary_color,
            shape=ft.RoundedRectangleBorder(radius=10),
        ),
        height=50,
        width=200,
    )

    result_text = ft.Text(
        size=18,
        weight=ft.FontWeight.BOLD,
        text_align=ft.TextAlign.CENTER,
    )
    
    result_container = ft.Container(
        content=result_text,
        padding=20,
        bgcolor=card_color,
        border_radius=15,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color=ft.Colors.BLUE_GREY_100,
        ),
        opacity=0, # Hidden initially
        animate_opacity=300,
        alignment=ft.alignment.center
    )

    # Items Logic
    items_list_view = ft.ListView(expand=True, spacing=10, padding=10)
    search_field = ft.TextField(
        label="Search by Name, Amount, or Date",
        prefix_icon=ft.Icons.SEARCH,
        border_radius=10,
        on_change=lambda e: render_items(e.control.value),
    )
    
    def render_items(search_query=""):
        items_list_view.controls.clear()
        if current_user[0] and current_user[0] in all_data:
            for idx, item in enumerate(all_data[current_user[0]]):
                # Filter based on search query
                if search_query:
                    query_lower = search_query.lower()
                    name_match = query_lower in item['name'].lower()
                    amount_match = query_lower in str(item['amount'])
                    date_match = query_lower in item['date']
                    
                    if not (name_match or amount_match or date_match):
                        continue
                
                create_item_card(item, idx)
        items_list_view.update()

    def create_item_card(item_data, index):
        i_name = item_data['name']
        i_amount = item_data['amount']
        i_rate = item_data['rate']
        i_date_str = item_data['date']
        i_date = datetime.strptime(i_date_str, '%Y-%m-%d')

        def calculate_this(e):
            days, interest, total = calculate_interest_helper(i_amount, i_rate, i_date)
            page.dialog = ft.AlertDialog(
                title=ft.Text(f"Result: {i_name}"),
                content=ft.Text(
                    f"Days: {days}\n"
                    f"Interest: ₹{interest:.2f}\n"
                    f"Total: ₹{total:.2f}",
                    size=16
                ),
                actions=[ft.TextButton("Close", on_click=lambda _: page.close(page.dialog))]
            )
            page.open(page.dialog)

        def delete_this(e):
            def confirm_delete(e):
                if current_user[0] in all_data:
                    # Find and remove the item by matching all properties
                    items = all_data[current_user[0]]
                    for i, item in enumerate(items):
                        if (item['name'] == i_name and 
                            item['amount'] == i_amount and 
                            item['rate'] == i_rate and 
                            item['date'] == i_date_str):
                            items.pop(i)
                            save_data()
                            render_items()
                            page.close(page.dialog)
                            page.snack_bar = ft.SnackBar(content=ft.Text("Item Deleted!"))
                            page.snack_bar.open = True
                            page.update()
                            break
            
            page.dialog = ft.AlertDialog(
                title=ft.Text("Confirm Deletion"),
                content=ft.Text(f"Are you sure you want to delete '{i_name}'?"),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: page.close(page.dialog)),
                    ft.TextButton("Delete", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.Colors.RED)),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.open(page.dialog)

        new_item = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.MONETIZATION_ON, color=primary_color, size=40),
                                ft.Column(
                                    [
                                        ft.Text(i_name, size=18, weight=ft.FontWeight.BOLD),
                                        ft.Text(f"Amount: ₹{i_amount}", size=14),
                                        ft.Text(f"Interest Rate: {i_rate}%", size=14),
                                        ft.Text(f"Start Date: {i_date_str}", size=14, color=ft.Colors.GREY_700),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                ft.Column(
                                    [
                                        ft.IconButton(
                                            icon=ft.Icons.CALCULATE, 
                                            tooltip="Calculate Interest",
                                            on_click=calculate_this,
                                            icon_color=primary_color,
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.DELETE,
                                            icon_color=ft.Colors.RED,
                                            tooltip="Delete Item",
                                            on_click=delete_this,
                                        ),
                                    ],
                                    spacing=0,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                    ],
                    spacing=0,
                ),
                padding=15,
            ),
            elevation=2,
        )
        items_list_view.controls.append(new_item)

    # Add Item Dialog Fields
    item_name_field = ft.TextField(label="Name")
    item_amount_field = ft.TextField(label="Amount", keyboard_type=ft.KeyboardType.NUMBER, prefix_text="₹ ")
    item_rate_field = ft.TextField(label="Interest Rate (%)", value="1.5", keyboard_type=ft.KeyboardType.NUMBER)
    
    item_date_button = ft.ElevatedButton(
        "Select Date",
        icon=ft.Icons.CALENDAR_TODAY,
    )
    
    item_date_picker = ft.DatePicker(
        on_change=lambda e: setattr(item_date_button, "text", e.control.value.strftime('%Y-%m-%d')) or item_date_button.update(),
    )
    
    def open_add_item_dialog(e):
        item_name_field.value = ""
        item_amount_field.value = ""
        item_rate_field.value = "1.5"
        item_date_button.text = "Select Date"
        page.open(add_item_dialog)

    def close_add_item_dialog(e):
        page.close(add_item_dialog)

    def save_item_click(e):
        reset_session()
        if not current_user[0]:
             page.snack_bar = ft.SnackBar(content=ft.Text("Please Login first!"))
             page.snack_bar.open = True
             page.update()
             return

        if not item_name_field.value or not item_amount_field.value or not item_rate_field.value or item_date_button.text == "Select Date":
            page.snack_bar = ft.SnackBar(content=ft.Text("Please fill all fields"))
            page.snack_bar.open = True
            page.update()
            return
        
        try:
            item_data = {
                "name": item_name_field.value,
                "amount": float(item_amount_field.value),
                "rate": float(item_rate_field.value),
                "date": item_date_button.text
            }
            
            if current_user[0] not in all_data:
                all_data[current_user[0]] = []
            
            all_data[current_user[0]].append(item_data)
            save_data()
            render_items()
            
            page.close(add_item_dialog)
            page.snack_bar = ft.SnackBar(content=ft.Text("Item Added!"))
            page.snack_bar.open = True
            page.update()
        except ValueError:
             page.snack_bar = ft.SnackBar(content=ft.Text("Invalid Number format"))
             page.snack_bar.open = True
             page.update()

    item_date_button.on_click = lambda _: page.open(item_date_picker)

    add_item_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Add New Item"),
        content=ft.Column(
            [
                item_name_field,
                item_amount_field,
                item_rate_field,
                item_date_button,
            ],
            tight=True,
        ),
        actions=[
            ft.TextButton("Cancel", on_click=close_add_item_dialog),
            ft.TextButton("Save", on_click=save_item_click),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    
    # Floating Action Button
    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.ADD,
        on_click=open_add_item_dialog,
        visible=False, # Hidden initially
    )

    # Authentication UI
    # Registration Form Fields
    reg_name_field = ft.TextField(label="Full Name")
    reg_email_field = ft.TextField(label="Email")
    reg_phone_field = ft.TextField(label="Phone Number")
    reg_loginid_field = ft.TextField(label="Login ID")
    reg_password_field = ft.TextField(label="Password", password=True, can_reveal_password=True)
    
    # Login Form Fields
    login_id_field = ft.TextField(label="Login ID")
    login_password_field = ft.TextField(label="Password", password=True, can_reveal_password=True)
    
    def show_login_screen():
        # Always show Welcome/Landing page first
        auth_view.content = landing_content

        auth_view.visible = True
        main_container.visible = False
        page.appbar = None # Remove app bar for login
        page.drawer = None
        if page.floating_action_button:
            page.floating_action_button.visible = False
        page.update()
    
    def show_main_app():
        auth_view.visible = False
        main_container.visible = True
        page.appbar = app_bar
        page.drawer = nav_drawer
        page.update()
    
    # OTP Verification Fields
    email_otp_field = ft.TextField(label="Email OTP", max_length=6)
    phone_otp_field = ft.TextField(label="Phone OTP", max_length=6)
    
    def attempt_register(e):
        print("Register button clicked") # Debug
        try:
            if not all([reg_name_field.value, reg_email_field.value, reg_phone_field.value, 
                        reg_loginid_field.value, reg_password_field.value]):
                print("Validation failed: Empty fields")
                page.snack_bar = ft.SnackBar(content=ft.Text("Please fill all fields"))
                page.snack_bar.open = True
                page.update()
                return

            # Sanitize Login ID
            reg_loginid_field.value = reg_loginid_field.value.strip()
            
            # Validate email format
            if not validate_email(reg_email_field.value):
                print(f"Validation failed: Invalid email '{reg_email_field.value}'")
                page.snack_bar = ft.SnackBar(content=ft.Text("Invalid email format"))
                page.snack_bar.open = True
                page.update()
                return
            
            # Auto-prepend +91 if missing
            phone_val = reg_phone_field.value.strip()
            if not phone_val.startswith("+"):
                phone_val = "+91" + phone_val
                reg_phone_field.value = phone_val # Update UI to show the change
                page.update()

            # Validate phone format
            if not validate_phone(phone_val):
                print(f"Validation failed: Invalid phone '{phone_val}'")
                page.snack_bar = ft.SnackBar(content=ft.Text("Invalid phone number format. Use: +91..."))
                page.snack_bar.open = True
                page.update()
                return
            
            # Validate password strength
            is_strong, message = validate_password_strength(reg_password_field.value)
            if not is_strong:
                print(f"Validation failed: Weak password - {message}")
                page.snack_bar = ft.SnackBar(content=ft.Text(message))
                page.snack_bar.open = True
                page.update()
                return
            
            # Check for empty Name and Login ID (explicitly)
            if not reg_name_field.value.strip() or not reg_loginid_field.value.strip():
                 print("Validation failed: Empty Name or Login ID")
                 page.snack_bar = ft.SnackBar(content=ft.Text("Name and Login ID are required!"))
                 page.snack_bar.open = True
                 page.update()
                 return

            if reg_loginid_field.value in all_users:
                print(f"Validation failed: Login ID '{reg_loginid_field.value}' exists locally")
                page.snack_bar = ft.SnackBar(content=ft.Text("Login ID already exists!"))
                page.snack_bar.open = True
                page.update()
                return

            # Check Global/Cloud Availability
            print(f"Checking cloud availability for: {reg_loginid_field.value}")
            if sync_manager.pull_data(reg_loginid_field.value) or sync_manager.pull_data(reg_loginid_field.value + " "):
                print(f"Validation failed: Login ID '{reg_loginid_field.value}' exists globally")
                reg_loginid_field.error_text = "Login ID already taken Globally"
                reg_loginid_field.update()
                # page.snack_bar = ft.SnackBar(content=ft.Text("Login ID already taken Please choose another."))
                # page.snack_bar.open = True
                # page.update()
                return
            else:
                 # Clear error if valid
                 reg_loginid_field.error_text = None
                 reg_loginid_field.update()
            
            # Generate and send OTPs
            # email_otp = generate_otp() # REMOVED: Email verification disabled
            phone_otp = generate_otp()
            
            # otp_storage[reg_email_field.value] = {"otp": email_otp, "type": "email"}
            otp_storage[reg_phone_field.value] = {"otp": phone_otp, "type": "phone"}
            
            print(f"Sending OTPs... Phone({reg_phone_field.value}): {phone_otp}")
            
            # Send OTPs
            # email_sent = send_email_otp(reg_email_field.value, email_otp)
            sms_sent = send_sms_otp(reg_phone_field.value, phone_otp)
            
            if not sms_sent:
                print("Failed to send verification codes")
                page.snack_bar = ft.SnackBar(content=ft.Text("Failed to send SMS code. Check console for OTP."))
                page.snack_bar.open = True
                page.update()
            
            # Show verification dialog
            page.close(register_dialog)
            # email_otp_field.value = ""
            phone_otp_field.value = ""
            
            # Show OTPs for debugging/usability
            demo_otp_text.value = f"Debug Code: Phone [{phone_otp}]"
            
            page.open(verify_otp_dialog)
            demo_otp_text.update() # Update text after dialog is open
            print("Opened verify dialog")

        except Exception as ex:
            print(f"Registration Error: {ex}")
            import traceback
            traceback.print_exc()
            page.snack_bar = ft.SnackBar(content=ft.Text(f"Error: {ex}"))
            page.snack_bar.open = True
            page.update()
    
    demo_otp_text = ft.Text("", size=12, color=ft.Colors.BLUE)

    def verify_otp_click(e):
        # email = reg_email_field.value
        phone = reg_phone_field.value
        
        # Verify OTPs
        # email_valid = (email in otp_storage and 
        #               otp_storage[email]["otp"] == email_otp_field.value)
        phone_valid = (phone in otp_storage and 
                      otp_storage[phone]["otp"] == phone_otp_field.value)
        
        # if not email_valid:
        #     page.snack_bar = ft.SnackBar(content=ft.Text("Invalid Email OTP Code"))
        #     page.snack_bar.open = True
        #     page.update()
        #     return

        if not phone_valid:
            page.snack_bar = ft.SnackBar(content=ft.Text("Invalid Phone OTP Code"))
            page.snack_bar.open = True
            page.update()
            return
        
        # Hash password before saving
        hashed_password = hash_password(reg_password_field.value)
        
        # Save user after verification
        all_users[reg_loginid_field.value] = {
            "name": reg_name_field.value,
            "login_id": reg_loginid_field.value, # Explicitly store ID
            "email": reg_email_field.value,
            "phone": reg_phone_field.value,
            "password": hashed_password,  # Store hashed password
            "verified": True
        }
        save_users()
        
        # Clean up OTP storage
        # otp_storage.pop(email, None)
        otp_storage.pop(phone, None)
        
        page.close(verify_otp_dialog)
        page.snack_bar = ft.SnackBar(content=ft.Text("Registration successful! Logging in..."))
        page.snack_bar.open = True
        page.update()
        
        # Auto-Login
        complete_login(reg_loginid_field.value)
        
        # Clear registration fields
        reg_name_field.value = ""
        reg_email_field.value = ""
        reg_phone_field.value = ""
        reg_loginid_field.value = ""
        reg_password_field.value = ""
    
    verify_otp_dialog = ft.AlertDialog(
        title=ft.Text("Verify Your Account"),
        content=ft.Column(
            [
                ft.Text("Please enter the verification code sent to you.", size=12),
                ft.Divider(height=20),
                
                # Email Section Removed
                # ft.Row([ft.Icon(ft.Icons.EMAIL), ft.Text("Email Verification", weight=ft.FontWeight.BOLD)]),
                # ft.Text("Code sent to your email:", size=12, color=ft.Colors.GREY),
                # email_otp_field,
                
                # ft.Divider(height=20),
                
                # Phone Section
                ft.Row([ft.Icon(ft.Icons.PHONE_ANDROID), ft.Text("Phone Verification", weight=ft.FontWeight.BOLD)]),
                ft.Text("Code sent to your phone:", size=12, color=ft.Colors.GREY),
                phone_otp_field,
                
                ft.Container(height=10),
                demo_otp_text, # Added debug text
                ft.Text("Check console if in demo mode", size=12, color=ft.Colors.GREY),
            ],
            tight=True,
            width=400,
            scroll=ft.ScrollMode.AUTO,
        ),
        actions=[
            ft.TextButton("Cancel", on_click=lambda _: page.close(verify_otp_dialog)),
            ft.TextButton("Verify", on_click=verify_otp_click),
        ],
    )
    
    def open_register_dialog(e):
        # Reset fields and status
        reg_name_field.value = ""
        reg_email_field.value = ""
        reg_phone_field.value = ""
        reg_loginid_field.value = ""
        reg_password_field.value = ""
        password_status_text.value = "Must contain: 8+ chars, A-Z, a-z, 0-9"
        password_status_text.color = ft.Colors.GREY
        page.open(register_dialog)
    
    # Password Validation UI
    password_status_text = ft.Text("Must contain: 8+ chars, A-Z, a-z, 0-9", size=12, color=ft.Colors.GREY)

    def update_password_status(e):
        password = e.control.value
        if not password:
             password_status_text.value = "Must contain: 8+ chars, A-Z, a-z, 0-9"
             password_status_text.color = ft.Colors.GREY
             password_status_text.update()
             return

        missing = []
        if len(password) < 8: missing.append("8+ chars")
        if not re.search(r'[A-Z]', password): missing.append("Upper")
        if not re.search(r'[a-z]', password): missing.append("Lower")
        if not re.search(r'[0-9]', password): missing.append("Number")
        
        if not missing:
            password_status_text.value = "Strong Password ✅"
            password_status_text.color = ft.Colors.GREEN
        else:
            password_status_text.value = "Missing: " + ", ".join(missing)
            password_status_text.color = ft.Colors.RED
        password_status_text.update()

    reg_password_field.on_change = update_password_status

    register_dialog = ft.AlertDialog(
        title=ft.Text("Register New Account"),
        content=ft.Column(
            [
                reg_name_field,
                reg_email_field,
                reg_phone_field,
                reg_loginid_field,
                reg_password_field,
                password_status_text,
            ],
            tight=True,
            scroll=ft.ScrollMode.AUTO,
        ),
        actions=[
            ft.TextButton("Cancel", on_click=lambda _: page.close(register_dialog)),
            ft.TextButton("Register", on_click=attempt_register),
        ],
    )
    
    def attempt_login(e):
        print(f"Login attempt: ID='{login_id_field.value}'")
        try:
            if not login_id_field.value or not login_password_field.value:
                print("Login failed: Empty fields")
                page.snack_bar = ft.SnackBar(content=ft.Text("Please enter Login ID and Password"))
                page.snack_bar.open = True
                page.update()
                return
            
            # Check rate limit
            can_attempt, rate_message = check_rate_limit(login_id_field.value)
            if not can_attempt:
                print(f"Login rate limited: {rate_message}")
                page.snack_bar = ft.SnackBar(content=ft.Text(rate_message))
                page.snack_bar.open = True
                page.update()
                return
            
            cleaned_id = login_id_field.value.strip()
            # Update UI to match sanitized value
            login_id_field.value = cleaned_id
            
            if cleaned_id not in all_users:
                print(f"Login failed: User '{cleaned_id}' not found locally. Checking Online...")
                
                # Device Migration / Online Check
                online_payload = sync_manager.pull_data(cleaned_id)
                
                # --- Trailing Space Recovery Logic ---
                # If clean ID fails, check for ID + space (Legacy Fix)
                if not online_payload:
                     print(f"Clean ID '{cleaned_id}' not found. Checking for legacy 'space' error...")
                     spaced_payload = sync_manager.pull_data(cleaned_id + " ")
                     if spaced_payload:
                         print("Found data under legacy ID (with space)! recovering...")
                         online_payload = spaced_payload
                # -------------------------------------

                if online_payload:
                    print(f"Found online data for {cleaned_id}")
                    
                    # 1. Parse Data
                    profile = None
                    items = []
                    
                    if isinstance(online_payload, dict):
                        profile = online_payload.get("profile")
                        items = online_payload.get("items", [])
                    elif isinstance(online_payload, list):
                        # Legacy Format (Raw List)
                        items = online_payload
                        
                    # 2. Check Logic
                    is_authenticated = False
                    
                    # CASE A: Profile exists (Standard Cloud Account)
                    if profile and "password" in profile:
                        if verify_password(profile["password"], login_password_field.value):
                            print("Password verified against cloud!")
                            is_authenticated = True
                        else:
                            print("Wrong password for cloud account.")
                            page.snack_bar = ft.SnackBar(content=ft.Text("Incorrect Password (Cloud Account)"))
                            page.snack_bar.open = True
                            page.update()
                            return

                    # CASE B: No Profile (Legacy/Orphaned Data) -> Auto-Adopt
                    # This fixes the issue for 'yashborse005'
                    elif items:
                        print("Legacy data found (No Profile). recovering account...")
                        # Create new profile with CURRENT input credentials
                        hashed_password = hash_password(login_password_field.value)
                        profile = {
                            "name": login_id_field.value, # Default name
                            "login_id": login_id_field.value,
                            "email": "",
                            "phone": "",
                            "password": hashed_password,
                            "verified": True,
                            "2fa_enabled": False
                        }
                        is_authenticated = True
                    else:
                        print("User found but data is empty.")

                    # 3. Finalize Login
                    if is_authenticated:
                        print("Migrating data to this device...")
                        
                        # Save Locally
                        all_users[login_id_field.value] = profile
                        save_users()
                        
                        all_data[login_id_field.value] = items
                        save_data() # This triggers a push, which will FIX the cloud structure
                        
                        # Proceed to standard local login below
                        pass 
                
                if login_id_field.value not in all_users:
                    print(f"Login failed: User '{login_id_field.value}' not found anywhere.")
                    page.snack_bar = ft.SnackBar(content=ft.Text("User ID or Password is incorrect"))
                    page.snack_bar.open = True
                    page.update()
                    return
            
            # Verify password using hash
            user_data = all_users[login_id_field.value]
            stored_password = user_data["password"]
            if not verify_password(stored_password, login_password_field.value):
                print("Login failed: Invalid password")
                record_login_attempt(login_id_field.value)
                page.snack_bar = ft.SnackBar(content=ft.Text("Wrong Password!"))
                page.snack_bar.open = True
                page.update()
                return
            
            # Check for 2FA
            if user_data.get("2fa_enabled", False):
                print("2FA required")
                # Generate and send OTP
                email = user_data.get("email")
                phone = user_data.get("phone")
                
                otp = generate_otp()
                # Store temporarily for login verification
                otp_storage[login_id_field.value] = {"otp": otp, "timestamp": time.time()}
                
                # Send (try email preferably)
                if email:
                    send_email_otp(email, otp)
                if phone:
                    send_sms_otp(phone, otp)
                    
                page.open(login_2fa_dialog)
                return

            # Successful login - clear rate limit
            print("Login successful")
            complete_login(login_id_field.value)

        except Exception as ex:
            print(f"Login Logic Error: {ex}")
            import traceback
            traceback.print_exc()
            page.snack_bar = ft.SnackBar(content=ft.Text(f"An error occurred: {str(ex)}"))
            page.snack_bar.open = True
            page.update()

    def complete_login(username):
        clear_login_attempts(username)
        current_user[0] = username
        
        # Save Last Login ID
        try:
            page.client_storage.set("last_user_id", username)
        except Exception as e:
            print(f"Error saving last user: {e}")

        reset_session()
        

        
        # Initialize user data if new
        if current_user[0] not in all_data:
            all_data[current_user[0]] = []
        
        render_items()
        show_main_app()
        
        page.snack_bar = ft.SnackBar(content=ft.Text(f"Welcome {all_users[current_user[0]]['name']}!"))
        page.snack_bar.open = True
        page.update()
        
        # Clear fields
        login_id_field.value = ""
        login_password_field.value = ""

    def guest_login_click(e):
        complete_login("guest")

    login_otp_field = ft.TextField(label="Enter OTP", max_length=6, text_align=ft.TextAlign.CENTER)

    def verify_login_otp_click(e):
        username = login_id_field.value
        if username in otp_storage and otp_storage[username]["otp"] == login_otp_field.value:
            otp_storage.pop(username) # Clear OTP
            page.close(login_2fa_dialog)
            complete_login(username)
        else:
            page.snack_bar = ft.SnackBar(content=ft.Text("Invalid OTP"))
            page.snack_bar.open = True
            page.update()

    login_2fa_dialog = ft.AlertDialog(
        title=ft.Text("Two-Factor Authentication"),
        content=ft.Column([
            ft.Text("Enter the OTP sent to your registered email/phone:"),
            ft.Container(height=10),
            login_otp_field
        ], tight=True),
        actions=[
            ft.TextButton("Cancel", on_click=lambda _: page.close(login_2fa_dialog)),
            ft.TextButton("Verify", on_click=verify_login_otp_click),
        ]
    )

    # Drawer Logic - Refactored
    
    def handle_drawer_change(e):
        print(f"Drawer selected_index: {e.control.selected_index}")  # Debug
        
        if e.control.selected_index == 0: # Items index
            home_view.visible = False
            items_view.visible = True
            if page.floating_action_button:
                page.floating_action_button.visible = True
            page.update()
        elif e.control.selected_index == 1: # Logout index
            if current_user[0]: # If logged in, then logout
                print("Logging out...")  # Debug
                current_user[0] = None
                items_list_view.controls.clear()
                items_list_view.update()
                
                # Reset views
                home_view.visible = True
                items_view.visible = False
                
                # Show login screen
                show_login_screen()
                
                page.snack_bar = ft.SnackBar(content=ft.Text("Logged Out Successfully!"))
                page.snack_bar.open = True
                page.update()
                return
        
        # Close drawer after selection
        page.close(nav_drawer)

    def go_home(e):
        items_view.visible = False
        home_view.visible = True
        if page.floating_action_button:
            page.floating_action_button.visible = False # Hide FAB
        page.update()

    # Navigation Drawer (store reference)
    nav_drawer = ft.NavigationDrawer(
        controls=[
            ft.NavigationDrawerDestination(
                icon=ft.Icons.LIST,
                label="Items",
            ),
            ft.Divider(),
            ft.NavigationDrawerDestination(
                icon=ft.Icons.LOGOUT,
                label="Logout",
            ),
        ],
        on_change=handle_drawer_change,
    )

    # AppBar (store reference)
    settings_dialog = ft.AlertDialog(
        title=ft.Text("Settings"),
        content=ft.Column(
            [
                ft.Text("Security", weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        ft.Text("Enable 2FA for Login"),
                        ft.Switch(
                            value=False,
                            on_change=lambda e: update_2fa_setting(e.control.value)
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(),
                ft.Text("Cloud Sync", weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                ft.ElevatedButton(
                    "Sync Now",
                    icon=ft.Icons.CLOUD_UPLOAD,
                    on_click=lambda e: manual_sync_click(e),
                    width=200,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)
                ),

            ],
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        actions=[
            ft.TextButton("Close", on_click=lambda _: page.close(settings_dialog)),
        ],
    )
    
    def manual_sync_click(e):
        if not current_user[0]:
             page.snack_bar = ft.SnackBar(content=ft.Text("Please login first!"))
             page.snack_bar.open = True
             page.update()
             return

        if not sync_manager.enabled:
             page.snack_bar = ft.SnackBar(content=ft.Text("Online Sync is disabled (Check keys)."))
             page.snack_bar.open = True
             page.update()
             return

        page.snack_bar = ft.SnackBar(content=ft.Text("Syncing to Cloud..."))
        page.snack_bar.open = True
        page.update()
        
        def on_sync_complete(result):
             if "Error" in result:
                  page.snack_bar = ft.SnackBar(content=ft.Text(f"{result}"), bgcolor=ft.Colors.RED)
             else:
                  page.snack_bar = ft.SnackBar(content=ft.Text(f"{result}"), bgcolor=ft.Colors.GREEN)
             page.snack_bar.open = True
             page.update()

        # Trigger push with callback
        sync_user_to_cloud(current_user[0], callback=on_sync_complete)
    
    def update_2fa_setting(value):
        if not current_user[0]:
             page.snack_bar = ft.SnackBar(content=ft.Text("Please login first!"))
             page.snack_bar.open = True
             page.update()
             return

        if current_user[0] in all_users:
            all_users[current_user[0]]["2fa_enabled"] = value
            save_users()
            page.snack_bar = ft.SnackBar(content=ft.Text(f"2FA {'Enabled' if value else 'Disabled'}"))
            page.snack_bar.open = True
            page.update()

    def open_settings_dialog(e):
        if current_user[0] and current_user[0] in all_users:
            # Update switch value
            settings_dialog.content.controls[1].controls[1].value = all_users[current_user[0]].get("2fa_enabled", False)
        page.open(settings_dialog)
    
    app_bar = ft.AppBar(
        leading=ft.IconButton(
            icon=ft.Icons.MENU,
            icon_color=ft.Colors.WHITE,
            tooltip="Menu",
            on_click=lambda e: page.open(nav_drawer),
        ),
        title=ft.Text("Interest Calculator", color=ft.Colors.WHITE),
        center_title=False,
        bgcolor=primary_color,
        actions=[
            ft.IconButton(
                icon=ft.Icons.SETTINGS,
                icon_color=ft.Colors.WHITE,
                tooltip="Settings",
                on_click=open_settings_dialog,
            ),
            ft.IconButton(
                icon=ft.Icons.REFRESH,
                icon_color=ft.Colors.WHITE,
                tooltip="Refresh",
                on_click=refresh_click,
            ),

        ],
    )



    # Views
    home_view = ft.Column(
            [
                ft.Container(height=20),
                ft.Text("Interest Calculator", size=30, weight=ft.FontWeight.BOLD, color=primary_color),
                ft.Container(height=20),
                principal_field,
                ft.Container(height=10),
                rate_field,
                ft.Container(height=10),
                date_button,
                ft.Container(height=30),
                calculate_btn,
                ft.Container(height=30),
                result_container,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    items_view = ft.Container(
        content=ft.Column(
            [
                ft.Text("Items Page", size=30, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                search_field,
                ft.Container(height=10),
                items_list_view, # List of items
                ft.ElevatedButton("Back to Calculator", on_click=go_home),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.START, # Align top to allow list growth
        ),
        visible=False,
        alignment=ft.alignment.top_center, # Align container to top
        padding=20,
        expand=True,
    )

    # --- Auth View & Navigation Redesign ---

    # 1. Login Form Content (Existing - Refactored for Redesign)
    login_form_content = ft.Column(
        [
            ft.Container(height=50),
            ft.Icon(ft.Icons.CALCULATE, size=80, color=primary_color),
            ft.Text("Interest Calculator", size=32, weight=ft.FontWeight.BOLD, color=primary_color),
            ft.Container(height=30),
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Login", size=24, weight=ft.FontWeight.BOLD),
                            ft.Container(height=10),
                            login_id_field,
                            login_password_field,
                            ft.Container(height=10),
                            ft.ElevatedButton(
                                "Login",
                                on_click=attempt_login,
                                style=ft.ButtonStyle(
                                    color=ft.Colors.WHITE,
                                    bgcolor=primary_color,
                                ),
                                width=200,
                            ),


                            ft.Container(height=5),
                            ft.TextButton("Back", on_click=lambda e: show_landing_page()),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        scroll=ft.ScrollMode.AUTO, # Enable scrolling for smaller screens
                    ),
                    padding=30,
                ),
                width=400,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
    )

    # 2. Landing Page Content (New)
    def on_new_user_click(e):
        open_register_dialog(e)

    def on_existing_user_click(e):
        # Reset password field (optional security)
        login_password_field.value = ""
        # Re-assign content to ensure updates are reflected
        auth_view.content = login_form_content
        auth_view.update()

    
    
    
    def quick_login_click(e):
        last_user = page.client_storage.get("last_user_id")
        if last_user:
            # Set ID and focus Password for quick entry
            login_id_field.value = last_user
            login_password_field.value = "" # Clear password
            login_password_field.focus() 
            auth_view.content = login_form_content
            auth_view.update()

    landing_buttons_column = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    landing_content = ft.Column(
        [
            ft.Container(height=50),
            ft.Icon(ft.Icons.CALCULATE, size=80, color=primary_color),
            ft.Text("Interest Calculator", size=32, weight=ft.FontWeight.BOLD, color=primary_color),
            ft.Container(height=40),
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Welcome", size=24, weight=ft.FontWeight.BOLD),
                            ft.Container(height=20),
                            landing_buttons_column,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=40,
                ),
                elevation=5,
                width=400,
            ),
            ft.Container(height=20),
            ft.Text("Secure • Fast • Cloud Sync", size=12, color=ft.Colors.GREY),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
    )

    def show_landing_page():
        # Dynamic Landing Page Logic
        last_user_id = page.client_storage.get("last_user_id")
        
        # Clear existing buttons
        landing_buttons_column.controls.clear()
        
        if last_user_id:
            landing_buttons_column.controls.extend([
                ft.Text(f"Welcome back, {last_user_id}!", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK54),
                ft.Container(height=15),
                ft.ElevatedButton(
                    f"Login as {last_user_id}",
                    width=280,
                    height=55,
                    icon=ft.Icons.FINGERPRINT, # Icon implies quick access/biometric-like feel
                    on_click=quick_login_click,
                    style=ft.ButtonStyle(
                        bgcolor=primary_color,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                ),
                ft.Container(height=15),
                ft.OutlinedButton(
                    "Switch Account",
                    width=280,
                    height=55,
                    icon=ft.Icons.SWAP_HORIZ,
                    on_click=on_existing_user_click,
                     style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10),
                        side=ft.BorderSide(2, primary_color),
                    ),
                ),
                ft.Container(height=15),
                ft.TextButton("Create New Account", on_click=on_new_user_click)
            ])
        else:
             landing_buttons_column.controls.extend([
                 ft.ElevatedButton(
                    "New User",
                    width=280,
                    height=55,
                    icon=ft.Icons.PERSON_ADD,
                    on_click=on_new_user_click,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.TEAL_400,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                ),
                ft.Container(height=15),
                ft.OutlinedButton(
                    "Existing User",
                    width=280,
                    height=55,
                    icon=ft.Icons.LOGIN,
                    on_click=on_existing_user_click,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10),
                        side=ft.BorderSide(2, primary_color),
                    ),
                ),
             ])

        auth_view.content = landing_content
        auth_view.update()

    # Authentication View Container
    auth_view = ft.Container(
        content=landing_content, # Start with landing page
        expand=True,
        visible=True,
        alignment=ft.alignment.center,
    )

    # Main Container (holds home and items views)
    main_container = ft.Column(
            [
                home_view,
                items_view,
            ],
            expand=True,
            visible=False,
        )



    # Layout
    page.on_connect = lambda e: reset_session()
    
    def on_page_disconnect(e):
        """Stop session thread when page disconnects"""
        session_active[0] = False
    
    page.on_disconnect = on_page_disconnect
    
    page.add(auth_view, main_container)
    show_login_screen()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
