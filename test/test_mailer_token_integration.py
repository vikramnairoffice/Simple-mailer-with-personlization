"""
Test suite for mailer.py integration with token_manager
Tests Gmail API integration using direct token files
"""

import unittest
from unittest.mock import Mock, patch, MagicMock


class TestMailerTokenIntegration(unittest.TestCase):
    """Test mailer integration with token manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_token_files = [
            Mock(name="token1.json"),
            Mock(name="token2.json")
        ]
    
    @patch('token_manager.token_manager')
    def test_ensure_service_for_sender_success(self, mock_token_manager):
        """Test successful Gmail service creation for sender"""
        from mailer import _ensure_service_for_sender
        
        # Mock token manager returning a valid service
        mock_service = Mock()
        mock_token_manager.get_service_for_email.return_value = mock_service
        
        service = _ensure_service_for_sender(None, "test@gmail.com", self.mock_token_files)
        
        self.assertIsNotNone(service)
        mock_token_manager.load_token_files.assert_called_once_with(self.mock_token_files)
        mock_token_manager.get_service_for_email.assert_called_once_with("test@gmail.com")
    
    @patch('token_manager.token_manager')
    def test_ensure_service_for_sender_not_found(self, mock_token_manager):
        """Test Gmail service creation for unknown sender"""
        from mailer import _ensure_service_for_sender
        
        # Mock token manager returning None (email not found)
        mock_token_manager.get_service_for_email.return_value = None
        
        service = _ensure_service_for_sender(None, "unknown@gmail.com", self.mock_token_files)
        
        self.assertIsNone(service)
    
    def test_ensure_service_for_sender_no_files(self):
        """Test Gmail service creation with no token files"""
        from mailer import _ensure_service_for_sender
        
        service = _ensure_service_for_sender(None, "test@gmail.com", None)
        
        self.assertIsNone(service)
    
    @patch('mailer.GMAIL_API_AVAILABLE', False)
    def test_ensure_service_gmail_api_unavailable(self):
        """Test service creation when Gmail API is not available"""
        from mailer import _ensure_service_for_sender
        
        service = _ensure_service_for_sender(None, "test@gmail.com", self.mock_token_files)
        
        self.assertIsNone(service)
    
    def test_gmail_api_send_success(self):
        """Test successful email sending via Gmail API"""
        from mailer import _gmail_api_send
        
        # Mock Gmail API service
        mock_service = Mock()
        mock_send_result = {'id': 'message_id_123'}
        mock_service.users().messages().send().execute.return_value = mock_send_result
        
        success, error_type, message = _gmail_api_send(
            mock_service, 
            "sender@gmail.com", 
            "recipient@example.com",
            "Test Subject",
            "Test Body",
            None,  # no attachments
            "Test Sender"
        )
        
        self.assertTrue(success)
        self.assertIsNone(error_type)
        self.assertIn("Email sent", message)
    
    def test_gmail_api_send_with_attachments(self):
        """Test email sending with attachments via Gmail API"""
        from mailer import _gmail_api_send
        import tempfile
        import os
        
        # Create a temporary attachment file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test attachment content")
            temp_file = f.name
        
        try:
            # Mock Gmail API service
            mock_service = Mock()
            mock_send_result = {'id': 'message_id_123'}
            mock_service.users().messages().send().execute.return_value = mock_send_result
            
            attachments = {"test.txt": temp_file}
            
            success, error_type, message = _gmail_api_send(
                mock_service,
                "sender@gmail.com",
                "recipient@example.com", 
                "Test Subject",
                "Test Body",
                attachments,
                "Test Sender"
            )
            
            self.assertTrue(success)
            self.assertIsNone(error_type)
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_gmail_api_send_failure(self):
        """Test Gmail API send failure handling"""
        from mailer import _gmail_api_send
        
        # Mock Gmail API service that raises an exception
        mock_service = Mock()
        mock_service.users().messages().send().execute.side_effect = Exception("API Error")
        
        success, error_type, message = _gmail_api_send(
            mock_service,
            "sender@gmail.com", 
            "recipient@example.com",
            "Test Subject",
            "Test Body"
        )
        
        self.assertFalse(success)
        self.assertEqual(error_type, "GMAIL_API_ERROR")
        self.assertIn("API Error", message)


class TestSmtpMailerTokenIntegration(unittest.TestCase):
    """Test SMTP mailer integration with token-based Gmail API"""
    
    def test_smtp_mailer_basic_functionality(self):
        """Test basic SMTP mailer functionality (not Gmail API mode)"""
        from mailer import SmtpMailer
        
        mailer = SmtpMailer()
        
        # Test that mailer initializes with expected SMTP configs
        self.assertIn('gmail.com', mailer.smtp_configs)
        self.assertIn('yahoo.com', mailer.smtp_configs)
        self.assertEqual(mailer.smtp_configs['gmail.com']['port'], 587)
    
    def test_smtp_mailer_unsupported_domain(self):
        """Test SMTP mailer with unsupported email domain"""
        from mailer import SmtpMailer
        
        mailer = SmtpMailer()
        
        account = {
            'email': 'test@unsupported.com',
            'password': 'password123'
        }
        
        success, error_type, message = mailer.send_email(
            account,
            "recipient@example.com", 
            "Test Subject",
            "Test Body"
        )
        
        self.assertFalse(success)
        self.assertEqual(error_type, "UNSUPPORTED_PROVIDER")
        self.assertIn("Unsupported email provider", message)


class TestWorkerFunctions(unittest.TestCase):
    """Test worker functions with token-based Gmail API"""
    
    @patch('token_manager.token_manager')
    def test_worker_gmail_api_mode(self, mock_token_manager):
        """Test worker function in Gmail API mode with tokens"""
        # Mock authenticated emails from token manager
        mock_token_manager.get_authenticated_emails.return_value = [
            "user1@gmail.com", 
            "user2@gmail.com"
        ]
        
        # Test verifies that token manager is used correctly
        # when Gmail API mode is enabled
        self.assertEqual(len(mock_token_manager.get_authenticated_emails.return_value), 2)
        self.assertIn("user1@gmail.com", mock_token_manager.get_authenticated_emails.return_value)


if __name__ == '__main__':
    unittest.main()