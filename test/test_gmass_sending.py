import unittest
from unittest.mock import Mock, patch
import tempfile
import os
from mailer import main_worker, parse_file_lines
from content import DEFAULT_GMASS_RECIPIENTS

class TestGmassSending(unittest.TestCase):
    """Test GMass sending ensures each SMTP sends to all recipients"""
    
    def setUp(self):
        """Set up test data"""
        self.gmass_recipients = DEFAULT_GMASS_RECIPIENTS[:3]  # Use first 3 for testing
        self.test_accounts = [
            {"email": "test1@gmail.com", "password": "pass1"},
            {"email": "test2@yahoo.com", "password": "pass2"}
        ]
        
    def create_temp_accounts_file(self):
        """Create temporary accounts file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            for acc in self.test_accounts:
                f.write(f"{acc['email']},{acc['password']}\n")
            return f.name
    
    def test_gmass_mode_sends_all_recipients_to_each_smtp(self):
        """Test that in GMass mode, each SMTP sends to ALL recipients"""
        # Mock the email sending function
        sent_emails = []
        
        def mock_send_email(account, to_addr, subject, body, attachments=None, sender_name=None):
            sent_emails.append({
                'from': account['email'],
                'to': to_addr,
                'subject': subject
            })
            return True, None, f"Mock sent from {account['email']} to {to_addr}"
        
        accounts_file_path = self.create_temp_accounts_file()
        
        try:
            with patch('mailer.SmtpMailer.send_email', side_effect=mock_send_email):
                # Create mock file object
                class MockFile:
                    def __init__(self, path):
                        self.name = path
                
                accounts_file = MockFile(accounts_file_path)
                
                # Run GMass mode
                results = list(main_worker(
                    accounts_file=accounts_file,
                    leads_file=None,
                    leads_per_account=len(self.gmass_recipients),
                    num_accounts_to_use=len(self.test_accounts),
                    mode="gmass",
                    subjects_text="Test Subject",
                    bodies_text="Test Body", 
                    gmass_recipients_text="\n".join(self.gmass_recipients),
                    include_pdfs=False,
                    include_images=False,
                    support_number="",
                    attachment_format="pdf",
                    use_gmail_api=False,
                    gmail_credentials_files=None,
                    sender_name_type="business"
                ))
            
            # Verify each SMTP sent to all GMass recipients
            emails_by_sender = {}
            for email in sent_emails:
                sender = email['from']
                if sender not in emails_by_sender:
                    emails_by_sender[sender] = []
                emails_by_sender[sender].append(email['to'])
            
            # Each SMTP should have sent to all GMass recipients
            for account in self.test_accounts:
                sender_email = account['email']
                self.assertIn(sender_email, emails_by_sender)
                
                # Check that this sender sent to all GMass recipients
                sent_recipients = emails_by_sender[sender_email]
                self.assertEqual(len(sent_recipients), len(self.gmass_recipients))
                
                for recipient in self.gmass_recipients:
                    self.assertIn(recipient, sent_recipients)
            
            # Total emails should be: num_accounts × num_gmass_recipients
            expected_total = len(self.test_accounts) * len(self.gmass_recipients)
            self.assertEqual(len(sent_emails), expected_total)
            
        finally:
            if os.path.exists(accounts_file_path):
                os.unlink(accounts_file_path)
    
    def test_leads_mode_distributes_recipients(self):
        """Test that in leads mode, recipients are distributed across SMTPs"""
        # This is a comparison test to ensure GMass mode behaves differently
        sent_emails = []
        
        def mock_send_email(account, to_addr, subject, body, attachments=None, sender_name=None):
            sent_emails.append({
                'from': account['email'],
                'to': to_addr,
                'subject': subject
            })
            return True, None, f"Mock sent from {account['email']} to {to_addr}"
        
        # Create leads file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as leads_file:
            for recipient in self.gmass_recipients:
                leads_file.write(f"{recipient}\n")
            leads_file_path = leads_file.name
        
        accounts_file_path = self.create_temp_accounts_file()
        
        try:
            with patch('mailer.SmtpMailer.send_email', side_effect=mock_send_email):
                class MockFile:
                    def __init__(self, path):
                        self.name = path
                
                accounts_file = MockFile(accounts_file_path)
                leads_file = MockFile(leads_file_path)
                
                # Run leads mode with distribution
                results = list(main_worker(
                    accounts_file=accounts_file,
                    leads_file=leads_file,
                    leads_per_account=2,  # Each account sends to 2 leads max
                    num_accounts_to_use=len(self.test_accounts),
                    mode="leads",
                    subjects_text="Test Subject",
                    bodies_text="Test Body",
                    gmass_recipients_text="",
                    include_pdfs=False,
                    include_images=False,
                    support_number="",
                    attachment_format="pdf",
                    use_gmail_api=False,
                    gmail_credentials_files=None,
                    sender_name_type="business"
                ))
            
            # In leads mode, recipients should be distributed
            emails_by_sender = {}
            for email in sent_emails:
                sender = email['from']
                if sender not in emails_by_sender:
                    emails_by_sender[sender] = []
                emails_by_sender[sender].append(email['to'])
            
            # Each sender should have sent to a subset (not all) of recipients
            total_sent = 0
            for account in self.test_accounts:
                sender_email = account['email']
                if sender_email in emails_by_sender:
                    sent_count = len(emails_by_sender[sender_email])
                    total_sent += sent_count
                    # Should not exceed leads_per_account
                    self.assertLessEqual(sent_count, 2)
            
            # Total should be distributed, not multiplied
            self.assertLessEqual(total_sent, len(self.gmass_recipients))
            
        finally:
            if os.path.exists(accounts_file_path):
                os.unlink(accounts_file_path)
            if os.path.exists(leads_file_path):
                os.unlink(leads_file_path)

if __name__ == "__main__":
    unittest.main()