"""
Test suite for ui.py integration with token_manager
Tests UI components for direct token upload functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock


class TestUITokenIntegration(unittest.TestCase):
    """Test UI integration with token manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_token_files = [
            Mock(name="/path/to/token1.json"),
            Mock(name="/path/to/token2.json")
        ]
        
        self.mock_load_result = {
            'valid': {
                'user1@gmail.com': '/path/to/token1.json',
                'user2@gmail.com': '/path/to/token2.json'
            },
            'invalid': {}
        }
    
    @patch('ui_token_helpers.token_manager')
    def test_analyze_token_files_valid(self, mock_token_manager):
        """Test analysis of valid token files"""
        from ui_token_helpers import analyze_token_files
        
        mock_token_manager.load_token_files.return_value = self.mock_load_result
        
        result = analyze_token_files(self.mock_token_files)
        
        expected = "Token files loaded: 2 valid accounts found (user1@gmail.com, user2@gmail.com)"
        self.assertIn("2 valid accounts", result)
        self.assertIn("user1@gmail.com", result)
        self.assertIn("user2@gmail.com", result)
    
    @patch('ui_token_helpers.token_manager')
    def test_analyze_token_files_mixed(self, mock_token_manager):
        """Test analysis of mixed valid/invalid token files"""
        from ui_token_helpers import analyze_token_files
        
        mixed_result = {
            'valid': {'user1@gmail.com': '/path/to/token1.json'},
            'invalid': [{'file': '/path/to/bad_token.json', 'error': 'Missing refresh_token'}]
        }
        mock_token_manager.load_token_files.return_value = mixed_result
        
        result = analyze_token_files(self.mock_token_files)
        
        self.assertIn("1 valid accounts", result)
        self.assertIn("1 invalid files", result)
        self.assertIn("user1@gmail.com", result)
    
    @patch('ui_token_helpers.token_manager')
    def test_analyze_token_files_all_invalid(self, mock_token_manager):
        """Test analysis when all token files are invalid"""
        from ui_token_helpers import analyze_token_files
        
        invalid_result = {
            'valid': {},
            'invalid': [
                {'file': '/path/to/bad1.json', 'error': 'Missing refresh_token'},
                {'file': '/path/to/bad2.json', 'error': 'Invalid JSON format'}
            ]
        }
        mock_token_manager.load_token_files.return_value = invalid_result
        
        result = analyze_token_files(self.mock_token_files)
        
        self.assertIn("0 valid accounts", result)
        self.assertIn("2 invalid files", result)
        self.assertIn("Missing refresh_token", result)
    
    def test_analyze_token_files_none(self):
        """Test analysis with no token files"""
        from ui_token_helpers import analyze_token_files
        
        result = analyze_token_files(None)
        
        self.assertEqual(result, "No token files uploaded")
    
    def test_analyze_token_files_empty(self):
        """Test analysis with empty token files list"""
        from ui_token_helpers import analyze_token_files
        
        result = analyze_token_files([])
        
        self.assertEqual(result, "No token files uploaded")
    
    @patch('ui_token_helpers.token_manager')
    def test_get_authenticated_gmail_accounts(self, mock_token_manager):
        """Test getting list of authenticated Gmail accounts"""
        from ui_token_helpers import get_authenticated_gmail_accounts
        
        mock_token_manager.get_authenticated_emails.return_value = [
            "user1@gmail.com",
            "user2@gmail.com",
            "user3@hotmail.com"  # Should be filtered out
        ]
        
        gmail_accounts = get_authenticated_gmail_accounts()
        
        self.assertEqual(len(gmail_accounts), 2)
        self.assertIn("user1@gmail.com", gmail_accounts)
        self.assertIn("user2@gmail.com", gmail_accounts)
        self.assertNotIn("user3@hotmail.com", gmail_accounts)
    
    @patch('ui_token_helpers.token_manager')
    def test_get_authenticated_gmail_accounts_none(self, mock_token_manager):
        """Test getting Gmail accounts when none are authenticated"""
        from ui_token_helpers import get_authenticated_gmail_accounts
        
        mock_token_manager.get_authenticated_emails.return_value = []
        
        gmail_accounts = get_authenticated_gmail_accounts()
        
        self.assertEqual(len(gmail_accounts), 0)
    
    @patch('ui_token_helpers.token_manager')
    def test_validate_gmail_api_setup(self, mock_token_manager):
        """Test validation of Gmail API setup with tokens"""
        from ui_token_helpers import validate_gmail_api_setup
        
        mock_token_manager.get_authenticated_emails.return_value = [
            "user1@gmail.com",
            "user2@gmail.com"
        ]
        
        is_valid, message = validate_gmail_api_setup(self.mock_token_files)
        
        self.assertTrue(is_valid)
        self.assertIn("2 Gmail accounts authenticated", message)
    
    @patch('ui_token_helpers.token_manager')
    def test_validate_gmail_api_setup_no_accounts(self, mock_token_manager):
        """Test validation when no Gmail accounts are authenticated"""
        from ui_token_helpers import validate_gmail_api_setup
        
        mock_token_manager.get_authenticated_emails.return_value = []
        
        is_valid, message = validate_gmail_api_setup(self.mock_token_files)
        
        self.assertFalse(is_valid)
        self.assertIn("No Gmail accounts found", message)
    
    def test_validate_gmail_api_setup_no_files(self):
        """Test validation with no token files"""
        from ui_token_helpers import validate_gmail_api_setup
        
        is_valid, message = validate_gmail_api_setup(None)
        
        self.assertFalse(is_valid)
        self.assertIn("No token files uploaded", message)


class TestUIGmailModeHandlers(unittest.TestCase):
    """Test UI handlers for Gmail API mode with tokens"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_token_files = [
            Mock(name="token1.json"),
            Mock(name="token2.json")
        ]
    
    def test_toggle_auth_method_gmail_api(self):
        """Test UI toggle to Gmail API mode"""
        from ui_token_helpers import toggle_auth_method
        
        result = toggle_auth_method("Gmail API")
        
        # Should update file input to accept JSON token files
        file_update, instructions_visibility, status_message = result
        
        self.assertIn("Gmail Token JSON Files", file_update['label'])
        self.assertIn(".json", file_update['file_types'])
        self.assertEqual(file_update['file_count'], "multiple")
        self.assertTrue(instructions_visibility)
        self.assertIn("Upload Gmail token JSON files", status_message)
    
    def test_toggle_auth_method_app_password(self):
        """Test UI toggle to App Password mode"""
        from ui_token_helpers import toggle_auth_method
        
        result = toggle_auth_method("App Password")
        
        file_update, instructions_visibility, status_message = result
        
        self.assertIn("Accounts File", file_update['label'])
        self.assertIn(".txt", file_update['file_types'])
        self.assertEqual(file_update['file_count'], "single")
        self.assertFalse(instructions_visibility)
        self.assertIn("App Password method selected", status_message)
    
    @patch('ui_token_helpers.token_manager')
    @patch('ui_token_helpers.validate_gmail_api_setup')
    def test_gmail_api_status_update_valid(self, mock_validate, mock_token_manager):
        """Test Gmail API status update with valid setup"""
        from ui_token_helpers import update_gmail_api_status
        
        mock_validate.return_value = (True, "2 Gmail accounts authenticated")
        mock_token_manager.get_authenticated_emails.return_value = [
            "user1@gmail.com", "user2@gmail.com"
        ]
        
        status_table = update_gmail_api_status(self.mock_token_files, "Gmail API")
        
        expected_data = [
            ["user1@gmail.com", "✅ Authenticated", "Ready"],
            ["user2@gmail.com", "✅ Authenticated", "Ready"]
        ]
        
        self.assertEqual(len(status_table), 2)
        self.assertIn("user1@gmail.com", str(status_table))
        self.assertIn("user2@gmail.com", str(status_table))
    
    @patch('ui_token_helpers.token_manager')
    @patch('ui_token_helpers.validate_gmail_api_setup')
    def test_gmail_api_status_update_invalid(self, mock_validate, mock_token_manager):
        """Test Gmail API status update with invalid setup"""
        from ui_token_helpers import update_gmail_api_status
        
        mock_validate.return_value = (False, "No Gmail accounts found")
        
        status_table = update_gmail_api_status(self.mock_token_files, "Gmail API")
        
        self.assertIn("No Gmail accounts", str(status_table))
    
    def test_gmail_api_status_update_wrong_method(self):
        """Test Gmail API status update when not in Gmail API mode"""
        from ui_token_helpers import update_gmail_api_status
        
        status_table = update_gmail_api_status(self.mock_token_files, "App Password")
        
        expected = [["Not applicable for App Password mode", "", ""]]
        self.assertEqual(status_table, expected)


class TestUIWorkflowIntegration(unittest.TestCase):
    """Test complete UI workflow with token manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_token_files = [
            Mock(name="token1.json"),
            Mock(name="token2.json")
        ]
    
    @patch('mailer.main_worker_new_mode')
    @patch('ui_token_helpers.token_manager')
    def test_unified_send_handler_gmail_api_mode(self, mock_token_manager, mock_worker):
        """Test unified send handler in Gmail API mode"""
        from ui_token_helpers import unified_send_handler
        
        # Mock token manager
        mock_token_manager.get_authenticated_emails.return_value = [
            "user1@gmail.com", "user2@gmail.com"
        ]
        
        # Mock worker generator
        mock_worker.return_value = iter([
            ("Log message", "Progress HTML", "Errors HTML", "Summary HTML")
        ])
        
        # Test Gmail API mode parameters
        result = unified_send_handler(
            auth_file=self.mock_token_files,
            auth_method="Gmail API",
            leads_file=Mock(),
            leads_per_account=10,
            num_accounts_to_use=2,
            mode="leads",
            subjects_text="Test Subject",
            bodies_text="Test Body", 
            gmass_recipients_text="",
            email_content_mode="Attachment",
            attachment_format="pdf",
            invoice_format="pdf",
            support_number="123-456-7890",
            sender_name_type="business"
        )
        
        # Verify worker was called with correct parameters
        mock_worker.assert_called_once()
        call_args, call_kwargs = mock_worker.call_args
        
        # The function should be called with positional arguments
        # Position 12 should be use_gmail_api=True
        # Position 13 should be gmail_credentials_files
        self.assertTrue(call_args[12])  # use_gmail_api
        self.assertEqual(call_args[13], self.mock_token_files)  # gmail_credentials_files
        self.assertIsNone(call_args[0])  # accounts_file


if __name__ == '__main__':
    unittest.main()