"""
Gmail OAuth2 Authentication Manager
Handles multiple credential files and per-account authentication with incognito browser support
"""

import os
import json
import subprocess
import webbrowser
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, List, Optional, Tuple

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False

SCOPES = ['https://mail.google.com/']
TOKEN_DIR = "gmail_tokens"

def ensure_token_dir():
    """Ensure token directory exists"""
    if not os.path.exists(TOKEN_DIR):
        os.makedirs(TOKEN_DIR)

def is_colab_environment():
    """Detect if running in Google Colab"""
    try:
        import google.colab
        return True
    except ImportError:
        return False

class CredentialManager:
    """Manages multiple OAuth2 credential files"""
    
    def __init__(self):
        self.credential_files = {}
        self.parsed_credentials = {}
    
    def load_credential_files(self, uploaded_files):
        """Load multiple credential JSON files"""
        self.credential_files.clear()
        self.parsed_credentials.clear()
        
        if not uploaded_files:
            return
            
        for file_obj in uploaded_files:
            if hasattr(file_obj, 'name'):
                file_path = file_obj.name
            else:
                file_path = str(file_obj)
                
            try:
                with open(file_path, 'r') as f:
                    cred_data = json.load(f)
                
                # Extract project info
                client_info = cred_data.get('installed', {})
                project_id = client_info.get('project_id', 'unknown')
                client_id = client_info.get('client_id', 'unknown')
                
                credential_key = f"{project_id}_{client_id[:8]}"
                
                self.credential_files[credential_key] = file_path
                self.parsed_credentials[credential_key] = {
                    'project_id': project_id,
                    'client_id': client_id,
                    'file_path': file_path,
                    'display_name': f"{project_id} ({client_id[:12]}...)"
                }
                
            except Exception as e:
                print(f"Error loading credential file {file_path}: {e}")
                continue
    
    def get_credential_options(self):
        """Get list of available credential options for UI"""
        return [(key, info['display_name']) for key, info in self.parsed_credentials.items()]
    
    def get_credential_file(self, credential_key):
        """Get file path for credential key"""
        return self.credential_files.get(credential_key)

class AuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth2 callback"""
    
    def do_GET(self):
        """Handle OAuth2 callback"""
        if '/auth/callback' in self.path:
            query_params = parse_qs(urlparse(self.path).query)
            
            if 'code' in query_params:
                self.server.auth_code = query_params['code'][0]
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                success_html = """
                <html>
                <head><title>Authentication Successful</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h2 style="color: green;">✅ Authentication Successful!</h2>
                    <p>You can close this window and return to the application.</p>
                    <script>
                        setTimeout(function() { window.close(); }, 3000);
                    </script>
                </body>
                </html>
                """
                self.wfile.write(success_html.encode())
            else:
                self.server.auth_error = query_params.get('error', ['Unknown error'])[0]
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                error_html = """
                <html>
                <head><title>Authentication Failed</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h2 style="color: red;">❌ Authentication Failed</h2>
                    <p>Please try again or contact support.</p>
                </body>
                </html>
                """
                self.wfile.write(error_html.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress log messages"""
        pass

class GmailAuthManager:
    """Main Gmail authentication manager"""
    
    def __init__(self):
        ensure_token_dir()
        self.credential_manager = CredentialManager()
        self.account_credential_mapping = {}
        self.authentication_status = {}
    
    def load_credentials(self, uploaded_files):
        """Load credential files"""
        self.credential_manager.load_credential_files(uploaded_files)
    
    def get_gmail_accounts(self, accounts_data):
        """Extract Gmail accounts from account data"""
        gmail_accounts = []
        if not accounts_data:
            return gmail_accounts
            
        try:
            content = accounts_data.decode('utf-8') if isinstance(accounts_data, bytes) else accounts_data
            for line in content.strip().split('\n'):
                if ',' in line:
                    email = line.split(',')[0].strip()
                    if '@gmail.com' in email.lower():
                        gmail_accounts.append(email)
        except Exception as e:
            print(f"Error parsing accounts: {e}")
            
        return gmail_accounts
    
    def get_token_path(self, account_email, credential_key):
        """Get token file path for account-credential combination"""
        safe_email = account_email.replace('@', '_at_').replace('.', '_dot_')
        return os.path.join(TOKEN_DIR, f"token_{safe_email}_{credential_key}.json")
    
    def is_account_authenticated(self, account_email, credential_key):
        """Check if account is authenticated with given credential"""
        token_path = self.get_token_path(account_email, credential_key)
        
        if not os.path.exists(token_path):
            return False
            
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            if creds and creds.valid:
                return True
            elif creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
                return True
        except Exception:
            pass
            
        return False
    
    def launch_incognito_browser(self, url):
        """Launch URL in incognito browser with proper Windows support and verification"""
        import platform
        import shutil
        
        system = platform.system().lower()
        
        # Windows-specific browser paths and commands
        if system == "windows":
            browsers_to_try = [
                # Chrome variations for Windows
                ['chrome.exe', '--incognito', '--new-window', '--no-first-run', '--disable-default-apps'],
                ['google-chrome.exe', '--incognito', '--new-window', '--no-first-run', '--disable-default-apps'],
                [r'C:\Program Files\Google\Chrome\Application\chrome.exe', '--incognito', '--new-window', '--no-first-run'],
                [r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe', '--incognito', '--new-window', '--no-first-run'],
                # Edge for Windows
                ['msedge.exe', '--inprivate', '--new-window'],
                [r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', '--inprivate', '--new-window'],
                # Firefox for Windows  
                ['firefox.exe', '--private-window'],
                [r'C:\Program Files\Mozilla Firefox\firefox.exe', '--private-window'],
                # Brave for Windows
                ['brave.exe', '--incognito', '--new-window'],
                # PowerShell command for Chrome (fallback)
                ['powershell', '-Command', f'Start-Process chrome -ArgumentList "--incognito","--new-window","{url}"']
            ]
        else:
            # Mac/Linux browser commands
            browsers_to_try = [
                # Chrome variations
                ['google-chrome', '--incognito', '--new-window', '--no-first-run'],
                ['chrome', '--incognito', '--new-window', '--no-first-run'], 
                ['chromium', '--incognito', '--new-window', '--no-first-run'],
                ['google-chrome-stable', '--incognito', '--new-window', '--no-first-run'],
                # Firefox
                ['firefox', '--private-window'],
                # Edge (Linux/Mac)
                ['microsoft-edge', '--inprivate'],
                ['msedge', '--inprivate'],
                # Brave
                ['brave-browser', '--incognito', '--new-window'],
                ['brave', '--incognito', '--new-window'],
                # Safari (Mac only, no incognito flag)
                ['safari']
            ]
        
        print(f"[INFO] Attempting to launch incognito browser on {system}...")
        
        for browser_cmd in browsers_to_try:
            try:
                # Check if browser exists (except for PowerShell commands)
                if not browser_cmd[0].startswith('powershell') and not browser_cmd[0].startswith('C:\\'):
                    if not shutil.which(browser_cmd[0]):
                        continue
                
                print(f"   Trying: {' '.join(browser_cmd[:2])}...")
                
                # Use different approach for PowerShell vs direct execution
                if browser_cmd[0] == 'powershell':
                    result = subprocess.run(browser_cmd, capture_output=True, text=True, timeout=10)
                else:
                    # For direct browser commands, don't use check=True to avoid failures
                    result = subprocess.run(browser_cmd + [url], capture_output=True, text=True, timeout=10)
                
                # If command executed without throwing exception, consider it successful
                print(f"   [SUCCESS] Successfully launched: {browser_cmd[0]}")
                
                # Give user clear indication
                print("[INFO] Incognito browser should have opened with Gmail OAuth.")
                print("   If no browser opened, please manually copy this URL to an incognito window:")
                print(f"   {url}")
                
                return True
                
            except subprocess.TimeoutExpired:
                print(f"   [TIMEOUT] Timeout launching {browser_cmd[0]}")
                continue
            except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
                print(f"   [ERROR] Failed to launch {browser_cmd[0]}: {e}")
                continue
        
        # Last resort: print URL and ask user to copy manually
        print("[ERROR] Could not automatically launch incognito browser.")
        print("📋 Please manually open this URL in an incognito/private window:")
        print(f"   {url}")
        print()
        print("[IMPORTANT] Use incognito mode to avoid polluting your browser with OAuth tokens!")
        
        # Don't use webbrowser.open() as fallback since it pollutes browser
        return False
    
    def start_callback_server(self, port=0):
        """Start HTTP server for OAuth callback"""
        server = HTTPServer(('localhost', port), AuthCallbackHandler)
        server.auth_code = None
        server.auth_error = None
        return server
    
    def authenticate_account_local(self, account_email, credential_key):
        """Authenticate account in local environment with incognito browser"""
        if not GMAIL_API_AVAILABLE:
            return False, "Gmail API libraries not available"
            
        credential_file = self.credential_manager.get_credential_file(credential_key)
        if not credential_file:
            return False, "Credential file not found"
        
        try:
            # Start callback server
            callback_server = self.start_callback_server()
            callback_port = callback_server.server_port
            redirect_uri = f"http://localhost:{callback_port}/auth/callback"
            
            # Create OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(credential_file, SCOPES)
            flow.redirect_uri = redirect_uri
            
            # Get authorization URL
            auth_url, _ = flow.authorization_url(
                prompt='consent',
                state=f"{account_email}_{credential_key}"
            )
            
            # Launch incognito browser
            if not self.launch_incognito_browser(auth_url):
                callback_server.server_close()
                return False, "Failed to launch browser"
            
            # Wait for callback with timeout
            def run_server():
                callback_server.timeout = 300  # 5 minutes
                callback_server.handle_request()
            
            server_thread = threading.Thread(target=run_server)
            server_thread.daemon = True
            server_thread.start()
            server_thread.join(timeout=300)
            
            if callback_server.auth_code:
                # Exchange code for token
                flow.fetch_token(code=callback_server.auth_code)
                
                # Save token
                token_path = self.get_token_path(account_email, credential_key)
                with open(token_path, 'w') as token:
                    token.write(flow.credentials.to_json())
                
                callback_server.server_close()
                return True, "Authentication successful"
                
            elif callback_server.auth_error:
                callback_server.server_close()
                return False, f"Authentication failed: {callback_server.auth_error}"
            else:
                callback_server.server_close()
                return False, "Authentication timeout"
                
        except Exception as e:
            return False, f"Authentication error: {str(e)}"
    
    def authenticate_account_colab(self, account_email, credential_key):
        """Authenticate account in Colab environment with manual flow"""
        if not GMAIL_API_AVAILABLE:
            return False, "Gmail API libraries not available"
            
        credential_file = self.credential_manager.get_credential_file(credential_key)
        if not credential_file:
            return False, "Credential file not found"
        
        try:
            from IPython.display import HTML, display
            
            # Create OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(credential_file, SCOPES)
            auth_url, _ = flow.authorization_url(prompt='consent')
            
            # Display authorization link
            html_content = f"""
            <div style="border: 2px solid #4285f4; padding: 20px; margin: 10px; border-radius: 8px;">
                <h3 style="color: #4285f4; margin-top: 0;">🔐 Authorize {account_email}</h3>
                <p><strong>Step 1:</strong> Click the link below to open authorization in <strong>incognito tab</strong>:</p>
                <div style="text-align: center; margin: 15px 0;">
                    <a href="{auth_url}" target="_blank" 
                       style="background: #4285f4; color: white; padding: 12px 24px; text-decoration: none; 
                              border-radius: 5px; font-weight: bold; display: inline-block;">
                       🌐 Authorize in Incognito Tab
                    </a>
                </div>
                <p><strong>Step 2:</strong> After authorization, you'll see a code. Copy it and paste below.</p>
                <p style="font-size: 12px; color: #666; margin-bottom: 0;">
                    💡 Tip: Right-click the link above and select "Open in incognito window"
                </p>
            </div>
            """
            display(HTML(html_content))
            
            # Get authorization code from user
            auth_code = input(f"📋 Paste authorization code for {account_email}: ").strip()
            
            if not auth_code:
                return False, "No authorization code provided"
            
            # Exchange code for token
            flow.fetch_token(code=auth_code)
            
            # Save token
            token_path = self.get_token_path(account_email, credential_key)
            with open(token_path, 'w') as token:
                token.write(flow.credentials.to_json())
            
            return True, "Authentication successful"
            
        except Exception as e:
            return False, f"Authentication error: {str(e)}"
    
    def authenticate_account(self, account_email, credential_key):
        """Authenticate account (auto-detects environment)"""
        if is_colab_environment():
            return self.authenticate_account_colab(account_email, credential_key)
        else:
            return self.authenticate_account_local(account_email, credential_key)
    
    def authenticate_with_credential_only_local(self, credential_key):
        """Authenticate with credential file only - discovers email from OAuth response (local)"""
        if not GMAIL_API_AVAILABLE:
            return False, "Gmail API libraries not available", None
            
        credential_file = self.credential_manager.get_credential_file(credential_key)
        if not credential_file:
            return False, "Credential file not found", None
        
        try:
            # Start callback server
            callback_server = self.start_callback_server()
            callback_port = callback_server.server_port
            redirect_uri = f"http://localhost:{callback_port}/auth/callback"
            
            # Create OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(credential_file, SCOPES)
            flow.redirect_uri = redirect_uri
            
            # Get authorization URL (no email hint needed)
            auth_url, _ = flow.authorization_url(
                prompt='consent',
                state=f"credential_only_{credential_key}"
            )
            
            print(f"[AUTH] Starting credential-only authentication for {credential_key}")
            
            # Launch incognito browser
            if not self.launch_incognito_browser(auth_url):
                callback_server.server_close()
                return False, "Failed to launch browser", None
            
            # Wait for callback with timeout
            def run_server():
                callback_server.timeout = 300  # 5 minutes
                callback_server.handle_request()
            
            server_thread = threading.Thread(target=run_server)
            server_thread.daemon = True
            server_thread.start()
            server_thread.join(timeout=300)
            
            if callback_server.auth_code:
                # Exchange code for token
                flow.fetch_token(code=callback_server.auth_code)
                
                # Get user info to discover email
                service = build('gmail', 'v1', credentials=flow.credentials)
                profile = service.users().getProfile(userId='me').execute()
                discovered_email = profile['emailAddress']
                
                print(f"[SUCCESS] Discovered email: {discovered_email}")
                
                # Save token with discovered email
                token_path = self.get_token_path(discovered_email, credential_key)
                with open(token_path, 'w') as token:
                    token.write(flow.credentials.to_json())
                
                callback_server.server_close()
                return True, "Authentication successful", discovered_email
                
            elif callback_server.auth_error:
                callback_server.server_close()
                return False, f"Authentication failed: {callback_server.auth_error}", None
            else:
                callback_server.server_close()
                return False, "Authentication timeout", None
                
        except Exception as e:
            return False, f"Authentication error: {str(e)}", None
    
    def authenticate_with_credential_only_colab(self, credential_key):
        """Authenticate with credential file only - discovers email from OAuth response (Colab)"""
        if not GMAIL_API_AVAILABLE:
            return False, "Gmail API libraries not available", None
            
        credential_file = self.credential_manager.get_credential_file(credential_key)
        if not credential_file:
            return False, "Credential file not found", None
        
        try:
            from IPython.display import HTML, display
            
            # Create OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(credential_file, SCOPES)
            auth_url, _ = flow.authorization_url(prompt='consent')
            
            # Display authorization link
            cred_info = self.credential_manager.parsed_credentials[credential_key]
            html_content = f"""
            <div style="border: 2px solid #4285f4; padding: 20px; margin: 10px; border-radius: 8px;">
                <h3 style="color: #4285f4; margin-top: 0;">🔐 Quick Authenticate with {cred_info['display_name']}</h3>
                <p><strong>Step 1:</strong> Click the link below to open authorization in <strong>incognito tab</strong>:</p>
                <div style="text-align: center; margin: 15px 0;">
                    <a href="{auth_url}" target="_blank" 
                       style="background: #4285f4; color: white; padding: 12px 24px; text-decoration: none; 
                              border-radius: 5px; font-weight: bold; display: inline-block;">
                       🌐 Authorize in Incognito Tab
                    </a>
                </div>
                <p><strong>Step 2:</strong> After authorization, copy the authorization code and paste below.</p>
                <p style="font-size: 12px; color: #666; margin-bottom: 0;">
                    💡 The system will automatically discover your email address from the OAuth response
                </p>
            </div>
            """
            display(HTML(html_content))
            
            # Get authorization code from user
            auth_code = input(f"📋 Paste authorization code for {cred_info['display_name']}: ").strip()
            
            if not auth_code:
                return False, "No authorization code provided", None
            
            # Exchange code for token
            flow.fetch_token(code=auth_code)
            
            # Get user info to discover email
            service = build('gmail', 'v1', credentials=flow.credentials)
            profile = service.users().getProfile(userId='me').execute()
            discovered_email = profile['emailAddress']
            
            print(f"[SUCCESS] Discovered email: {discovered_email}")
            
            # Save token with discovered email
            token_path = self.get_token_path(discovered_email, credential_key)
            with open(token_path, 'w') as token:
                token.write(flow.credentials.to_json())
            
            return True, "Authentication successful", discovered_email
            
        except Exception as e:
            return False, f"Authentication error: {str(e)}", None
    
    def authenticate_with_credential_only(self, credential_key):
        """Authenticate with credential only (auto-detects environment)"""
        if is_colab_environment():
            return self.authenticate_with_credential_only_colab(credential_key)
        else:
            return self.authenticate_with_credential_only_local(credential_key)
    
    def get_authentication_status(self, gmail_accounts):
        """Get authentication status for all Gmail accounts"""
        status = {}
        credential_options = self.credential_manager.get_credential_options()
        
        if not credential_options:
            return {}
        
        for account in gmail_accounts:
            account_status = {}
            for cred_key, cred_name in credential_options:
                is_auth = self.is_account_authenticated(account, cred_key)
                account_status[cred_key] = {
                    'authenticated': is_auth,
                    'credential_name': cred_name,
                    'last_auth': 'Recently' if is_auth else 'Never'
                }
            
            # Set default credential (first one or first authenticated)
            default_cred = None
            for cred_key, info in account_status.items():
                if info['authenticated']:
                    default_cred = cred_key
                    break
            if not default_cred and credential_options:
                default_cred = credential_options[0][0]
            
            status[account] = {
                'credentials': account_status,
                'default_credential': default_cred
            }
        
        return status
    
    def get_service_for_account(self, account_email, credential_key=None):
        """Get Gmail service for authenticated account"""
        if not credential_key:
            # Try to find any authenticated credential for this account
            credential_options = self.credential_manager.get_credential_options()
            for cred_key, _ in credential_options:
                if self.is_account_authenticated(account_email, cred_key):
                    credential_key = cred_key
                    break
        
        if not credential_key:
            return None
            
        token_path = self.get_token_path(account_email, credential_key)
        
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    with open(token_path, 'w') as token:
                        token.write(creds.to_json())
                else:
                    return None
            
            return build('gmail', 'v1', credentials=creds)
            
        except Exception as e:
            print(f"Error building service for {account_email}: {e}")
            return None

# Global instance
gmail_auth_manager = GmailAuthManager()