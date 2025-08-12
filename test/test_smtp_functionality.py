#!/usr/bin/env python3
"""
Comprehensive SMTP Functionality and Multithreading Test Suite

This test file validates:
1. SMTP connection and authentication
2. Email sending functionality
3. Multithreading behavior
4. Error handling and recovery
5. Progress tracking
6. Rate limiting
"""

import unittest
import time
import threading
import queue
import tempfile
import os
import smtplib
from unittest.mock import Mock, patch, MagicMock
from mailer import (
    SmtpMailer, AccountErrorTracker, ProgressTracker, 
    send_worker, parse_file_lines, validate_accounts_file, 
    validate_leads_file, get_random_attachment
)

class TestSMTPMailer(unittest.TestCase):
    """Test SMTP mailer functionality"""
    
    def setUp(self):
        self.mailer = SmtpMailer()
        self.test_account = {
            'email': 'test@gmail.com',
            'password': 'testpass123'
        }
    
    def test_smtp_configs_exist(self):
        """Test that SMTP configurations exist for all supported providers"""
        expected_providers = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com']
        
        for provider in expected_providers:
            self.assertIn(provider, self.mailer.smtp_configs)
            config = self.mailer.smtp_configs[provider]
            self.assertIn('server', config)
            self.assertIn('port', config)
            self.assertIsInstance(config['port'], int)
    
    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp_class):
        """Test successful email sending"""
        # Setup mock
        mock_server = Mock()
        mock_smtp_class.return_value = mock_server
        
        # Test sending
        success, error_type, message = self.mailer.send_email(
            self.test_account,
            'recipient@test.com',
            'Test Subject',
            'Test Body'
        )
        
        # Verify results
        self.assertTrue(success)
        self.assertIsNone(error_type)
        self.assertIn('Email sent', message)
        
        # Verify SMTP calls
        mock_smtp_class.assert_called_once()
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with('test@gmail.com', 'testpass123')
        mock_server.send_message.assert_called_once()
        mock_server.quit.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_send_email_auth_failure(self, mock_smtp_class):
        """Test authentication failure handling"""
        mock_server = Mock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, 'Authentication failed')
        mock_smtp_class.return_value = mock_server
        
        success, error_type, message = self.mailer.send_email(
            self.test_account,
            'recipient@test.com',
            'Test Subject',
            'Test Body'
        )
        
        self.assertFalse(success)
        self.assertEqual(error_type, 'AUTH_FAILED')
        self.assertIn('Authentication failed', message)
    
    @patch('smtplib.SMTP')
    def test_send_email_invalid_recipient(self, mock_smtp_class):
        """Test invalid recipient handling"""
        mock_server = Mock()
        mock_server.send_message.side_effect = smtplib.SMTPRecipientsRefused({})
        mock_smtp_class.return_value = mock_server
        
        success, error_type, message = self.mailer.send_email(
            self.test_account,
            'invalid@test.com',
            'Test Subject',
            'Test Body'
        )
        
        self.assertFalse(success)
        self.assertEqual(error_type, 'INVALID_RECIPIENT')
        self.assertIn('Invalid recipient', message)
    
    def test_unsupported_provider(self):
        """Test unsupported email provider handling"""
        unsupported_account = {
            'email': 'test@unsupported.com',
            'password': 'testpass123'
        }
        
        success, error_type, message = self.mailer.send_email(
            unsupported_account,
            'recipient@test.com',
            'Test Subject',
            'Test Body'
        )
        
        self.assertFalse(success)
        self.assertEqual(error_type, 'UNSUPPORTED_PROVIDER')
        self.assertIn('Unsupported email provider', message)
    
    @patch('smtplib.SMTP')
    def test_send_email_with_attachments(self, mock_smtp_class):
        """Test email sending with attachments"""
        mock_server = Mock()
        mock_smtp_class.return_value = mock_server
        
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('Test attachment content')
            temp_file = f.name
        
        try:
            attachments = {'test.txt': temp_file}
            
            success, error_type, message = self.mailer.send_email(
                self.test_account,
                'recipient@test.com',
                'Test Subject',
                'Test Body',
                attachments
            )
            
            self.assertTrue(success)
            self.assertIsNone(error_type)
            mock_server.send_message.assert_called_once()
        finally:
            os.unlink(temp_file)

class TestAccountErrorTracker(unittest.TestCase):
    """Test error tracking functionality"""
    
    def setUp(self):
        self.tracker = AccountErrorTracker()
    
    def test_add_error(self):
        """Test adding errors to tracker"""
        self.tracker.add_error('test@gmail.com', 'AUTH_FAILED', 'Authentication failed')
        
        self.assertIn('test@gmail.com', self.tracker.account_errors)
        errors = self.tracker.account_errors['test@gmail.com']
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]['type'], 'AUTH_FAILED')
        self.assertEqual(errors[0]['message'], 'Authentication failed')
        self.assertIn('timestamp', errors[0])
    
    def test_multiple_errors(self):
        """Test adding multiple errors for same account"""
        account = 'test@gmail.com'
        
        self.tracker.add_error(account, 'AUTH_FAILED', 'Auth error 1')
        self.tracker.add_error(account, 'RATE_LIMITED', 'Rate limit error')
        self.tracker.add_error(account, 'AUTH_FAILED', 'Auth error 2')
        
        errors = self.tracker.account_errors[account]
        self.assertEqual(len(errors), 3)
        self.assertEqual(errors[0]['type'], 'AUTH_FAILED')
        self.assertEqual(errors[1]['type'], 'RATE_LIMITED')
        self.assertEqual(errors[2]['type'], 'AUTH_FAILED')
    
    def test_get_summary(self):
        """Test error summary generation"""
        # No errors initially
        summary = self.tracker.get_summary()
        self.assertEqual(summary, 'No errors')
        
        # Add some errors
        self.tracker.add_error('test1@gmail.com', 'AUTH_FAILED', 'Error 1')
        self.tracker.add_error('test1@gmail.com', 'RATE_LIMITED', 'Error 2')
        self.tracker.add_error('test2@yahoo.com', 'SMTP_ERROR', 'Error 3')
        
        summary = self.tracker.get_summary()
        self.assertIn('3 errors', summary)
        self.assertIn('2 accounts', summary)
    
    def test_html_report(self):
        """Test HTML error report generation"""
        # No errors initially
        html = self.tracker.get_html_report()
        self.assertEqual(html, 'No errors yet')
        
        # Add error
        self.tracker.add_error('test@gmail.com', 'AUTH_FAILED', 'Test error')
        
        html = self.tracker.get_html_report()
        self.assertIn('test@gmail.com', html)
        self.assertIn('Authentication Failed', html)
        self.assertIn('Test error', html)

class TestProgressTracker(unittest.TestCase):
    """Test progress tracking functionality"""
    
    def setUp(self):
        self.tracker = ProgressTracker(3)
    
    def test_update_progress(self):
        """Test progress updates"""
        account = 'test@gmail.com'
        
        self.tracker.update_progress(account, 5, 10, 'sending')
        
        self.assertIn(account, self.tracker.account_progress)
        progress = self.tracker.account_progress[account]
        self.assertEqual(progress['sent'], 5)
        self.assertEqual(progress['total'], 10)
        self.assertEqual(progress['status'], 'sending')
        self.assertIn('last_update', progress)
    
    def test_html_report(self):
        """Test HTML progress report generation"""
        # No progress initially
        html = self.tracker.get_html_report()
        self.assertIn('No progress data', html)
        
        # Add progress
        self.tracker.update_progress('test1@gmail.com', 3, 10)
        self.tracker.update_progress('test2@yahoo.com', 7, 10)
        
        html = self.tracker.get_html_report()
        self.assertIn('test1@gmail.com', html)
        self.assertIn('test2@yahoo.com', html)
        self.assertIn('3/10', html)
        self.assertIn('7/10', html)
        self.assertIn('Overall', html)

class TestFileValidation(unittest.TestCase):
    """Test file parsing and validation"""
    
    def test_validate_accounts_file(self):
        """Test accounts file validation"""
        # Valid accounts
        valid_lines = [
            'user1@gmail.com,password1',
            'user2@yahoo.com,password2'
        ]
        
        is_valid, message, accounts = validate_accounts_file(valid_lines)
        self.assertTrue(is_valid)
        self.assertEqual(len(accounts), 2)
        self.assertEqual(accounts[0]['email'], 'user1@gmail.com')
        self.assertEqual(accounts[0]['password'], 'password1')
        
        # Invalid format (no comma)
        invalid_lines = ['user1@gmail.com password1']
        is_valid, message, accounts = validate_accounts_file(invalid_lines)
        self.assertFalse(is_valid)
        self.assertIn('Invalid format', message)
        
        # Invalid email
        invalid_lines = ['invalid_email,password1']
        is_valid, message, accounts = validate_accounts_file(invalid_lines)
        self.assertFalse(is_valid)
        self.assertIn('Invalid email format', message)
    
    def test_validate_leads_file(self):
        """Test leads file validation"""
        # Valid leads
        valid_lines = [
            'lead1@gmail.com',
            'lead2@yahoo.com',
            'lead3@hotmail.com'
        ]
        
        is_valid, message, leads = validate_leads_file(valid_lines)
        self.assertTrue(is_valid)
        self.assertEqual(len(leads), 3)
        
        # Invalid email
        invalid_lines = ['invalid_email', 'valid@email.com']
        is_valid, message, leads = validate_leads_file(invalid_lines)
        self.assertFalse(is_valid)
        self.assertIn('Invalid email format', message)

class TestMultithreading(unittest.TestCase):
    """Test multithreading functionality"""
    
    def setUp(self):
        self.test_account = {
            'email': 'test@gmail.com',
            'password': 'testpass123'
        }
        self.test_config = {
            'subjects': ['Test Subject'],
            'bodies': ['Test Body'],
            'include_pdfs': False,
            'include_images': False,
            'support_number': None,
            'attachment_format': 'pdf',
            'use_gmail_api': False,
            'gmail_credentials_files': []
        }
    
    @patch('mailer.SmtpMailer.send_email')
    @patch('time.sleep')  # Speed up tests
    def test_send_worker_success(self, mock_sleep, mock_send):
        """Test worker thread for successful sending"""
        # Setup mocks
        mock_send.return_value = (True, None, 'Email sent successfully')
        
        # Setup queues
        leads_queue = queue.Queue()
        results_queue = queue.Queue()
        
        # Add test leads
        test_leads = ['lead1@test.com', 'lead2@test.com']
        for lead in test_leads:
            leads_queue.put(lead)
        leads_queue.put(None)  # Poison pill
        
        # Run worker
        send_worker(self.test_account, leads_queue, results_queue, self.test_config)
        
        # Verify results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Should have 2 successful sends + 1 completion message
        self.assertEqual(len(results), 3)
        
        # Check successful sends
        successful_sends = [r for r in results if r['success'] is True]
        self.assertEqual(len(successful_sends), 2)
        
        # Check completion message
        completion_msg = [r for r in results if r['error_type'] == 'COMPLETED']
        self.assertEqual(len(completion_msg), 1)
        self.assertEqual(completion_msg[0]['sent_count'], 2)
    
    @patch('mailer.SmtpMailer.send_email')
    @patch('time.sleep')
    def test_send_worker_auth_failure(self, mock_sleep, mock_send):
        """Test worker thread with authentication failures"""
        # Setup mock for auth failure
        mock_send.return_value = (False, 'AUTH_FAILED', 'Authentication failed')
        
        # Setup queues
        leads_queue = queue.Queue()
        results_queue = queue.Queue()
        
        # Add test leads
        leads_queue.put('lead1@test.com')
        leads_queue.put(None)  # Poison pill
        
        # Run worker
        send_worker(self.test_account, leads_queue, results_queue, self.test_config)
        
        # Verify results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Should have 1 failed send + 1 completion message
        failed_sends = [r for r in results if r['success'] is False and r['error_type'] != 'COMPLETED']
        self.assertEqual(len(failed_sends), 1)
        self.assertEqual(failed_sends[0]['error_type'], 'AUTH_FAILED')
    
    def test_multiple_workers_concurrent(self):
        """Test multiple worker threads running concurrently"""
        with patch('mailer.SmtpMailer.send_email') as mock_send, \
             patch('time.sleep'):
            
            # Setup mock
            mock_send.return_value = (True, None, 'Email sent successfully')
            
            # Setup multiple accounts
            accounts = [
                {'email': 'test1@gmail.com', 'password': 'pass1'},
                {'email': 'test2@yahoo.com', 'password': 'pass2'},
                {'email': 'test3@hotmail.com', 'password': 'pass3'}
            ]
            
            # Setup queues and threads
            results_queue = queue.Queue()
            threads = []
            
            for account in accounts:
                leads_queue = queue.Queue()
                leads_queue.put('lead@test.com')
                leads_queue.put(None)  # Poison pill
                
                thread = threading.Thread(
                    target=send_worker,
                    args=(account, leads_queue, results_queue, self.test_config)
                )
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join(timeout=5)  # 5 second timeout
                self.assertFalse(thread.is_alive(), "Thread should have completed")
            
            # Verify results from all workers
            results = []
            while not results_queue.empty():
                results.append(results_queue.get())
            
            # Should have results from all 3 workers
            accounts_that_completed = set()
            for result in results:
                if result['error_type'] == 'COMPLETED':
                    accounts_that_completed.add(result['account'])
            
            self.assertEqual(len(accounts_that_completed), 3)
    
    def test_worker_error_handling(self):
        """Test worker thread error handling"""
        with patch('mailer.SmtpMailer.send_email') as mock_send, \
             patch('time.sleep'):
            
            # Setup mock to raise exception
            mock_send.side_effect = Exception("Network error")
            
            # Setup queues
            leads_queue = queue.Queue()
            results_queue = queue.Queue()
            
            leads_queue.put('lead@test.com')
            leads_queue.put(None)  # Poison pill
            
            # Run worker
            send_worker(self.test_account, leads_queue, results_queue, self.test_config)
            
            # Verify error was caught
            results = []
            while not results_queue.empty():
                results.append(results_queue.get())
            
            # Should have worker error result
            worker_errors = [r for r in results if r['error_type'] == 'WORKER_ERROR']
            self.assertTrue(len(worker_errors) > 0)

class TestRateLimiting(unittest.TestCase):
    """Test rate limiting functionality"""
    
    @patch('time.sleep')
    def test_rate_limiting_delay(self, mock_sleep):
        """Test that rate limiting delays are applied"""
        with patch('mailer.SmtpMailer.send_email') as mock_send:
            mock_send.return_value = (True, None, 'Email sent successfully')
            
            # Setup
            account = {'email': 'test@gmail.com', 'password': 'pass'}
            leads_queue = queue.Queue()
            results_queue = queue.Queue()
            config = {
                'subjects': ['Test Subject'],
                'bodies': ['Test Body'],
                'include_pdfs': False,
                'include_images': False,
                'support_number': None,
                'attachment_format': 'pdf',
                'use_gmail_api': False,
                'gmail_credentials_files': []
            }
            
            # Add multiple leads
            for i in range(3):
                leads_queue.put(f'lead{i}@test.com')
            leads_queue.put(None)  # Poison pill
            
            # Run worker
            send_worker(account, leads_queue, results_queue, config)
            
            # Verify sleep was called for rate limiting
            # Should be called once per email (3 times)
            self.assertEqual(mock_sleep.call_count, 3)

def create_test_files():
    """Create temporary test files for integration testing"""
    # Create test accounts file
    accounts_content = """test1@gmail.com,password1
test2@yahoo.com,password2
test3@hotmail.com,password3"""
    
    accounts_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    accounts_file.write(accounts_content)
    accounts_file.close()
    
    # Create test leads file
    leads_content = """lead1@test.com
lead2@test.com
lead3@test.com
lead4@test.com
lead5@test.com"""
    
    leads_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    leads_file.write(leads_content)
    leads_file.close()
    
    return accounts_file.name, leads_file.name

def cleanup_test_files(accounts_file, leads_file):
    """Clean up temporary test files"""
    try:
        os.unlink(accounts_file)
        os.unlink(leads_file)
    except:
        pass

class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflow"""
    
    def setUp(self):
        self.accounts_file, self.leads_file = create_test_files()
    
    def tearDown(self):
        cleanup_test_files(self.accounts_file, self.leads_file)
    
    def test_file_parsing_integration(self):
        """Test complete file parsing workflow"""
        # Test accounts file parsing
        with open(self.accounts_file, 'r') as f:
            accounts_lines = [line.strip() for line in f.readlines()]
        
        is_valid, message, accounts = validate_accounts_file(accounts_lines)
        self.assertTrue(is_valid)
        self.assertEqual(len(accounts), 3)
        
        # Test leads file parsing
        with open(self.leads_file, 'r') as f:
            leads_lines = [line.strip() for line in f.readlines()]
        
        is_valid, message, leads = validate_leads_file(leads_lines)
        self.assertTrue(is_valid)
        self.assertEqual(len(leads), 5)

def run_performance_test():
    """Run a simple performance test"""
    print("\n" + "="*50)
    print("PERFORMANCE TEST")
    print("="*50)
    
    # Test creating many error tracker entries
    start_time = time.time()
    tracker = AccountErrorTracker()
    
    for i in range(1000):
        tracker.add_error(f'test{i}@gmail.com', 'AUTH_FAILED', f'Test error {i}')
    
    end_time = time.time()
    print(f"Added 1000 errors in {end_time - start_time:.3f} seconds")
    
    # Test HTML report generation
    start_time = time.time()
    html_report = tracker.get_html_report()
    end_time = time.time()
    print(f"Generated HTML report in {end_time - start_time:.3f} seconds")
    print(f"HTML report length: {len(html_report)} characters")

def run_stress_test():
    """Run stress test with many concurrent workers"""
    print("\n" + "="*50)
    print("STRESS TEST - 10 CONCURRENT WORKERS")
    print("="*50)
    
    with patch('mailer.SmtpMailer.send_email') as mock_send, \
         patch('time.sleep'):
        
        # Setup mock
        mock_send.return_value = (True, None, 'Email sent successfully')
        
        # Setup many accounts
        num_workers = 10
        accounts = [
            {'email': f'test{i}@gmail.com', 'password': f'pass{i}'}
            for i in range(num_workers)
        ]
        
        config = {
            'subjects': ['Test Subject'],
            'bodies': ['Test Body'],
            'include_pdfs': False,
            'include_images': False,
            'support_number': None,
            'attachment_format': 'pdf',
            'use_gmail_api': False,
            'gmail_credentials_files': []
        }
        
        # Setup queues and threads
        results_queue = queue.Queue()
        threads = []
        start_time = time.time()
        
        for account in accounts:
            leads_queue = queue.Queue()
            # Add 5 leads per worker
            for j in range(5):
                leads_queue.put(f'lead{j}@test.com')
            leads_queue.put(None)  # Poison pill
            
            thread = threading.Thread(
                target=send_worker,
                args=(account, leads_queue, results_queue, config)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        successful_sends = len([r for r in results if r['success'] is True])
        completed_workers = len([r for r in results if r['error_type'] == 'COMPLETED'])
        
        print(f"Time taken: {end_time - start_time:.3f} seconds")
        print(f"Workers completed: {completed_workers}/{num_workers}")
        print(f"Total successful sends: {successful_sends}")
        print(f"Total results: {len(results)}")

if __name__ == '__main__':
    print("="*70)
    print("SMTP FUNCTIONALITY AND MULTITHREADING TEST SUITE")
    print("="*70)
    
    # Run unit tests
    print("\nRunning unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run performance tests
    run_performance_test()
    
    # Run stress tests
    run_stress_test()
    
    print("\n" + "="*50)
    print("ALL TESTS COMPLETED")
    print("="*50)