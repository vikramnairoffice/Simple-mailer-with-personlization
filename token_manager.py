"""
Simple Token Manager for Gmail API
Handles direct token file upload and validation without complex OAuth flows
"""

import json
import os
from typing import Dict, List, Tuple, Optional, Any

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
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


class TokenManager:
    """Simple token manager for direct token file handling"""
    
    def __init__(self):
        ensure_token_dir()
        self.token_files = {}  # email -> file_path mapping
        self.gmail_api_available = GMAIL_API_AVAILABLE
    
    def validate_token_file(self, file_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate a token JSON file
        
        Returns:
            (is_valid, email_or_none, error_or_none)
        """
        if not os.path.exists(file_path):
            return False, None, f"Token file not found: {file_path}"
        
        try:
            with open(file_path, 'r') as f:
                token_data = json.load(f)
            
            # Check required fields for Gmail API token
            required_fields = ['client_id', 'client_secret', 'refresh_token', 'type']
            missing_fields = [field for field in required_fields if field not in token_data]
            
            if missing_fields:
                return False, None, f"Missing required fields: {', '.join(missing_fields)}"
            
            if token_data.get('type') != 'authorized_user':
                return False, None, "Token type must be 'authorized_user'"
            
            # Try to extract email from token by creating credentials and querying Gmail
            try:
                creds = Credentials.from_authorized_user_file(file_path, SCOPES)
                email = self.extract_email_from_token(creds)
                return True, email, None
            except Exception as e:
                # If we can't extract email, still consider valid if structure is correct
                return True, None, None
                
        except json.JSONDecodeError:
            return False, None, "Invalid JSON format"
        except Exception as e:
            return False, None, f"Error validating token file: {str(e)}"
    
    def extract_email_from_token(self, credentials) -> Optional[str]:
        """Extract email address from token credentials"""
        if not self.gmail_api_available:
            return None
            
        try:
            # Refresh token if needed
            if not credentials.valid:
                if credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                else:
                    return None
            
            # Build Gmail service and get user profile
            service = build('gmail', 'v1', credentials=credentials)
            profile = service.users().getProfile(userId='me').execute()
            return profile.get('emailAddress')
            
        except Exception as e:
            print(f"Warning: Could not extract email from token: {e}")
            return None
    
    def load_token_files(self, uploaded_files: List[Any]) -> Dict[str, Any]:
        """
        Load and validate multiple token files
        
        Returns:
            {
                'valid': {email: file_path, ...},
                'invalid': [{'file': file_path, 'error': error_msg}, ...]
            }
        """
        result = {
            'valid': {},
            'invalid': []
        }
        
        if not uploaded_files:
            return result
        
        for file_obj in uploaded_files:
            # Handle different file object types
            if hasattr(file_obj, 'name') and not str(file_obj).startswith("<Mock"):
                file_path = file_obj.name
            elif str(file_obj).startswith("<Mock") and hasattr(file_obj, 'name'):
                # Handle mock objects in tests
                file_path = file_obj.name
                # Extract actual path from mock name if it's there
                if hasattr(file_obj.name, 'name'):
                    file_path = file_obj.name.name
                elif isinstance(file_obj.name, str):
                    file_path = file_obj.name
            else:
                file_path = str(file_obj)
            
            is_valid, email, error = self.validate_token_file(file_path)
            
            if is_valid:
                if email:
                    result['valid'][email] = file_path
                    self.token_files[email] = file_path
                else:
                    # Valid structure but couldn't extract email
                    # Use filename as fallback identifier
                    filename = os.path.basename(file_path)
                    fallback_email = f"unknown_email_{filename}"
                    result['valid'][fallback_email] = file_path
                    self.token_files[fallback_email] = file_path
            else:
                result['invalid'].append({
                    'file': file_path,
                    'error': error
                })
        
        return result
    
    def get_service_for_email(self, email: str):
        """Get Gmail service for authenticated email"""
        if not self.gmail_api_available:
            return None
        
        if email not in self.token_files:
            return None
        
        token_path = self.token_files[email]
        
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    # Save refreshed token
                    with open(token_path, 'w') as token_file:
                        token_file.write(creds.to_json())
                else:
                    return None
            
            return build('gmail', 'v1', credentials=creds)
            
        except Exception as e:
            print(f"Error building Gmail service for {email}: {e}")
            return None
    
    def get_authenticated_emails(self) -> List[str]:
        """Get list of authenticated email addresses"""
        return list(self.token_files.keys())
    
    def clear_tokens(self):
        """Clear all loaded tokens"""
        self.token_files.clear()


# Global instance
token_manager = TokenManager()