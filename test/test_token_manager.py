"""
Test suite for token_manager.py
Tests token validation, storage, and Gmail API service creation
"""

import unittest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock


class TestTokenManager(unittest.TestCase):
    """Test token manager functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_token_data = {
            "client_id": "123456789.apps.googleusercontent.com",
            "client_secret": "GOCSPX-abcdefghijklmnop",
            "refresh_token": "1//04abc123def456ghi789",
            "type": "authorized_user"
        }
        
        self.invalid_token_data = {
            "client_id": "123456789.apps.googleusercontent.com",
            "client_secret": "GOCSPX-abcdefghijklmnop",
            # Missing refresh_token
            "type": "authorized_user"
        }
        
        # Create temp directory for testing
        self.test_token_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.test_token_dir):
            shutil.rmtree(self.test_token_dir)
    
    def create_test_token_file(self, email="test@gmail.com", token_data=None):
        """Helper to create test token file"""
        if token_data is None:
            token_data = self.sample_token_data
        
        file_path = os.path.join(self.test_token_dir, f"token_{email.replace('@', '_at_').replace('.', '_dot_')}.json")
        with open(file_path, 'w') as f:
            json.dump(token_data, f)
        return file_path
    
    @patch('token_manager.TokenManager.extract_email_from_token')
    def test_validate_token_file_valid(self, mock_extract_email):
        """Test validation of valid token file"""
        from token_manager import TokenManager
        
        # Mock email extraction to avoid actual API calls
        mock_extract_email.return_value = "test@gmail.com"
        
        manager = TokenManager()
        file_path = self.create_test_token_file()
        
        is_valid, email, error = manager.validate_token_file(file_path)
        
        self.assertTrue(is_valid)
        self.assertEqual(email, "test@gmail.com")
        self.assertIsNone(error)
    
    def test_validate_token_file_invalid(self):
        """Test validation of invalid token file"""
        from token_manager import TokenManager
        
        manager = TokenManager()
        file_path = self.create_test_token_file(token_data=self.invalid_token_data)
        
        is_valid, email, error = manager.validate_token_file(file_path)
        
        self.assertFalse(is_valid)
        self.assertIsNone(email)
        self.assertIsNotNone(error)
    
    def test_validate_token_file_not_exists(self):
        """Test validation of non-existent file"""
        from token_manager import TokenManager
        
        manager = TokenManager()
        
        is_valid, email, error = manager.validate_token_file("nonexistent.json")
        
        self.assertFalse(is_valid)
        self.assertIsNone(email)
        self.assertIn("not found", error.lower())
    
    def test_load_token_files_single(self):
        """Test loading single token file"""
        from token_manager import TokenManager
        
        manager = TokenManager()
        file_path = self.create_test_token_file("user1@gmail.com")
        
        # Create mock file object with proper name attribute
        mock_file = Mock()
        mock_file.name = file_path
        
        result = manager.load_token_files([mock_file])
        
        self.assertEqual(len(result['valid']), 1)
        self.assertEqual(len(result['invalid']), 0)
        # Should have a valid email or fallback
        self.assertTrue(len(result['valid']) > 0)
    
    def test_load_token_files_multiple(self):
        """Test loading multiple token files"""
        from token_manager import TokenManager
        
        manager = TokenManager()
        file1 = self.create_test_token_file("user1@gmail.com")
        file2 = self.create_test_token_file("user2@gmail.com")
        
        # Create proper mock file objects
        mock_file1 = Mock()
        mock_file1.name = file1
        mock_file2 = Mock()
        mock_file2.name = file2
        
        result = manager.load_token_files([mock_file1, mock_file2])
        
        self.assertEqual(len(result['valid']), 2)
        self.assertEqual(len(result['invalid']), 0)
    
    def test_load_token_files_mixed_valid_invalid(self):
        """Test loading mix of valid and invalid token files"""
        from token_manager import TokenManager
        
        manager = TokenManager()
        valid_file = self.create_test_token_file("valid@gmail.com")
        invalid_file = self.create_test_token_file("invalid@gmail.com", self.invalid_token_data)
        
        # Create proper mock file objects
        mock_valid = Mock()
        mock_valid.name = valid_file
        mock_invalid = Mock()
        mock_invalid.name = invalid_file
        
        result = manager.load_token_files([mock_valid, mock_invalid])
        
        self.assertEqual(len(result['valid']), 1)
        self.assertEqual(len(result['invalid']), 1)
    
    def test_extract_email_from_token_with_userinfo(self):
        """Test email extraction when token has user info"""
        from token_manager import TokenManager
        
        manager = TokenManager()
        
        # Mock Gmail service and user profile
        with patch('token_manager.build') as mock_build:
            mock_service = Mock()
            mock_profile = Mock()
            mock_profile.execute.return_value = {'emailAddress': 'discovered@gmail.com'}
            mock_service.users().getProfile().execute = mock_profile.execute
            mock_build.return_value = mock_service
            
            # Mock credentials
            mock_creds = Mock()
            
            email = manager.extract_email_from_token(mock_creds)
            
            self.assertEqual(email, 'discovered@gmail.com')
    
    @patch('token_manager.Credentials.from_authorized_user_file')
    def test_get_service_for_email_success(self, mock_creds_from_file):
        """Test successful Gmail service creation"""
        from token_manager import TokenManager
        
        manager = TokenManager()
        manager.token_files = {"test@gmail.com": "/path/to/token.json"}
        
        # Mock valid credentials
        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds_from_file.return_value = mock_creds
        
        with patch('token_manager.build') as mock_build:
            mock_service = Mock()
            mock_build.return_value = mock_service
            
            service = manager.get_service_for_email("test@gmail.com")
            
            self.assertIsNotNone(service)
            mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_creds)
    
    @patch('token_manager.Credentials.from_authorized_user_file')
    def test_get_service_for_email_refresh_needed(self, mock_creds_from_file):
        """Test Gmail service creation with token refresh"""
        from token_manager import TokenManager
        
        manager = TokenManager()
        
        # Create actual temp file for this test
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_token_data, f)
            temp_file = f.name
        
        try:
            manager.token_files = {"test@gmail.com": temp_file}
            
            # Mock expired credentials that can be refreshed
            mock_creds = Mock()
            mock_creds.valid = False
            mock_creds.expired = True
            mock_creds.refresh_token = "refresh_token_here"
            mock_creds.to_json.return_value = '{"refreshed": true}'
            mock_creds_from_file.return_value = mock_creds
            
            with patch('token_manager.build') as mock_build, \
                 patch('token_manager.Request') as mock_request, \
                 patch('builtins.open', create=True) as mock_open:
                
                mock_service = Mock()
                mock_build.return_value = mock_service
                
                # After refresh, credentials become valid
                def mock_refresh(request):
                    mock_creds.valid = True
                mock_creds.refresh.side_effect = mock_refresh
                
                service = manager.get_service_for_email("test@gmail.com")
                
                self.assertIsNotNone(service)
                mock_creds.refresh.assert_called_once()
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_get_service_for_email_not_found(self):
        """Test Gmail service creation for unknown email"""
        from token_manager import TokenManager
        
        manager = TokenManager()
        manager.token_files = {}
        
        service = manager.get_service_for_email("unknown@gmail.com")
        
        self.assertIsNone(service)
    
    def test_get_authenticated_emails(self):
        """Test getting list of authenticated email addresses"""
        from token_manager import TokenManager
        
        manager = TokenManager()
        manager.token_files = {
            "user1@gmail.com": "/path/to/token1.json",
            "user2@gmail.com": "/path/to/token2.json"
        }
        
        emails = manager.get_authenticated_emails()
        
        self.assertEqual(len(emails), 2)
        self.assertIn("user1@gmail.com", emails)
        self.assertIn("user2@gmail.com", emails)
    
    def test_token_manager_singleton_behavior(self):
        """Test that TokenManager maintains state correctly"""
        from token_manager import token_manager
        
        # Clear any existing state
        token_manager.token_files = {}
        
        # Add some tokens
        token_manager.token_files["test@gmail.com"] = "/path/to/token.json"
        
        # Import again and check state is maintained
        from token_manager import token_manager as tm2
        
        self.assertEqual(tm2.token_files["test@gmail.com"], "/path/to/token.json")


class TestTokenManagerIntegration(unittest.TestCase):
    """Integration tests for token manager with Gmail API"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.test_token_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up integration test fixtures"""
        import shutil
        if os.path.exists(self.test_token_dir):
            shutil.rmtree(self.test_token_dir)
    
    @patch('token_manager.GMAIL_API_AVAILABLE', True)
    def test_token_manager_availability_check(self):
        """Test that token manager checks Gmail API availability"""
        from token_manager import TokenManager
        
        manager = TokenManager()
        self.assertTrue(hasattr(manager, 'gmail_api_available'))
    
    @patch('token_manager.GMAIL_API_AVAILABLE', False)
    def test_token_manager_handles_missing_gmail_api(self):
        """Test graceful handling when Gmail API is not available"""
        from token_manager import TokenManager
        
        manager = TokenManager()
        service = manager.get_service_for_email("test@gmail.com")
        
        self.assertIsNone(service)


if __name__ == '__main__':
    unittest.main()