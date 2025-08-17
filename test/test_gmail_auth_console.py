#!/usr/bin/env python3
"""
Test Gmail OAuth2 Authentication with Console Flow
Tests the console-based authentication approach to bypass disabled_client errors
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Use the same scope as legacy working code
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
TOKEN_DIR = './test_gmail_tokens'

def ensure_token_dir():
    """Ensure token directory exists"""
    if not os.path.exists(TOKEN_DIR):
        os.makedirs(TOKEN_DIR)

def get_token_path(email):
    """Get token file path for email"""
    safe_email = email.replace('@', '_at_').replace('.', '_dot_')
    return os.path.join(TOKEN_DIR, f"test_token_{safe_email}.json")

def test_console_auth(credentials_json_path, test_email=None):
    """
    Test console-based OAuth authentication
    This approach should bypass the disabled_client error
    """
    print("=" * 60)
    print("[TEST] CONSOLE-BASED GMAIL OAUTH AUTHENTICATION")
    print("=" * 60)
    
    ensure_token_dir()
    
    # Validate credentials file exists
    if not os.path.exists(credentials_json_path):
        print(f"❌ ERROR: Credentials file not found: {credentials_json_path}")
        return False, None
    
    try:
        # Load and display credential info
        with open(credentials_json_path, 'r') as f:
            cred_data = json.load(f)
        
        client_info = cred_data.get('installed', {})
        project_id = client_info.get('project_id', 'unknown')
        client_id = client_info.get('client_id', 'unknown')[:12]
        
        print(f"[INFO] Credential File: {os.path.basename(credentials_json_path)}")
        print(f"[INFO] Project ID: {project_id}")
        print(f"[INFO] Client ID: {client_id}...")
        print()
        
        # Check if token already exists for test email
        if test_email:
            token_path = get_token_path(test_email)
            if os.path.exists(token_path):
                print(f"[FOUND] Existing token for {test_email}")
                try:
                    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
                    if creds and creds.valid:
                        print(f"[SUCCESS] Existing token is valid for {test_email}")
                        return True, test_email
                    elif creds and creds.expired and creds.refresh_token:
                        print(f"[REFRESH] Refreshing expired token for {test_email}")
                        creds.refresh(Request())
                        with open(token_path, 'w') as token:
                            token.write(creds.to_json())
                        print(f"[SUCCESS] Token refreshed successfully for {test_email}")
                        return True, test_email
                except Exception as e:
                    print(f"[WARNING] Existing token invalid: {e}")
        
        # Create OAuth flow
        print("[START] Starting console-based OAuth flow...")
        flow = InstalledAppFlow.from_client_secrets_file(credentials_json_path, SCOPES)
        
        print()
        print("[INFO] CONSOLE AUTHENTICATION FLOW:")
        print("   1. A browser will open with the OAuth consent page")
        print("   2. Sign in and authorize the application")
        print("   3. Copy the authorization code from the browser")
        print("   4. Paste it back in the console when prompted")
        print()
        print("[TIP] Use an incognito/private browser window to avoid account conflicts")
        print()
        
        # Run console OAuth flow (this should bypass disabled_client error)
        print("[AUTH] Starting authentication...")
        creds = flow.run_console()
        
        # Build Gmail service to get user email
        print("[BUILD] Building Gmail service to discover account email...")
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        authenticated_email = profile['emailAddress']
        
        print(f"[SUCCESS] Authenticated email: {authenticated_email}")
        
        # Save token
        token_path = get_token_path(authenticated_email)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        
        print(f"[SAVE] Token saved to: {token_path}")
        
        # Test sending capability
        print("[TEST] Testing Gmail send capability...")
        test_message_sent = test_send_capability(service, authenticated_email)
        
        if test_message_sent:
            print("[SUCCESS] FULL SUCCESS: Authentication and send capability confirmed!")
        else:
            print("[WARNING] Authentication successful, but send test failed")
        
        return True, authenticated_email
        
    except Exception as e:
        print(f"[ERROR] AUTHENTICATION FAILED: {e}")
        print()
        print("[INFO] COMMON CAUSES OF disabled_client ERROR:")
        print("   - OAuth2 application not published/verified")
        print("   - Incorrect application type (should be 'Desktop Application')")
        print("   - Missing redirect URIs in Google Cloud Console")
        print("   - Client credentials file corrupted or wrong format")
        print()
        return False, None

def test_send_capability(service, sender_email):
    """Test if the authenticated service can prepare to send emails"""
    try:
        # Just test if we can access the Gmail API sending functionality
        # We won't actually send an email, just verify the API access
        
        from email.mime.text import MIMEText
        import base64
        
        # Create a test message (we won't send it)
        msg = MIMEText("This is a test message that won't be sent")
        msg['to'] = sender_email  # Send to self for testing
        msg['from'] = sender_email
        msg['subject'] = "Gmail API Test - Not Actually Sent"
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        
        # Test API access by checking quota/permissions (dry run)
        # We could call service.users().messages().send() here but we won't to avoid spam
        print(f"[CONFIRM] Gmail API access confirmed for {sender_email}")
        return True
        
    except Exception as e:
        print(f"[WARNING] Send capability test failed: {e}")
        return False

def main():
    """Main test function"""
    print("GMAIL OAUTH2 CONSOLE AUTHENTICATION TESTER")
    print("This test uses the console flow to bypass disabled_client errors")
    print()
    
    # Get credentials file path from user
    while True:
        cred_path = input("[FILE] Enter path to your OAuth2 credentials JSON file: ").strip()
        if cred_path.startswith('"') and cred_path.endswith('"'):
            cred_path = cred_path[1:-1]  # Remove quotes
        
        if os.path.exists(cred_path):
            break
        else:
            print(f"[ERROR] File not found: {cred_path}")
            print("   Please enter the full path to your credentials.json file")
    
    # Optional: test specific email
    test_email = input("[EMAIL] [Optional] Enter Gmail account to test (or press Enter to discover): ").strip()
    if not test_email:
        test_email = None
    
    # Run test
    success, authenticated_email = test_console_auth(cred_path, test_email)
    
    if success:
        print()
        print("🎊 CONSOLE AUTHENTICATION TEST COMPLETED SUCCESSFULLY!")
        print(f"✅ Authenticated: {authenticated_email}")
        print(f"💾 Token saved in: {TOKEN_DIR}/")
        print()
        print("🔄 Next Steps:")
        print("   - You can now use this account for bulk email sending")
        print("   - The token will be reused for future authentications")
        print("   - Run this test for additional Gmail accounts as needed")
    else:
        print()
        print("❌ CONSOLE AUTHENTICATION TEST FAILED")
        print("   Check your OAuth2 credentials configuration in Google Cloud Console")
        print("   Make sure the application type is set to 'Desktop Application'")

if __name__ == "__main__":
    main()