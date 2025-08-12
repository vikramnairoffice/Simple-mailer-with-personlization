#!/usr/bin/env python3
"""
Real SMTP Test Script (For Manual Testing with Real Credentials)

WARNING: This script will attempt to send real emails if provided with valid credentials.
Only use with test email accounts and test recipients.

Usage:
1. Update TEST_ACCOUNTS with your test email credentials
2. Update TEST_RECIPIENTS with test email addresses you control
3. Run: python test_real_smtp.py
"""

import time
import threading
import queue
from mailer import SmtpMailer, send_worker, AccountErrorTracker, ProgressTracker

# TEST CONFIGURATION - UPDATE THESE WITH YOUR TEST CREDENTIALS
TEST_ACCOUNTS = [
    # {'email': 'your_test@gmail.com', 'password': 'your_app_password'},
    # {'email': 'your_test@yahoo.com', 'password': 'your_password'},
]

TEST_RECIPIENTS = [
    # 'recipient1@test.com',
    # 'recipient2@test.com',
]

# Test configuration
TEST_CONFIG = {
    'subjects': ['Test Email Subject'],
    'bodies': ['This is a test email body. Please ignore.'],
    'include_pdfs': False,
    'include_images': False,
    'support_number': None,
    'attachment_format': 'pdf',
    'use_gmail_api': False,
    'gmail_credentials_files': []
}

def test_single_account_smtp():
    """Test SMTP sending with a single account"""
    if not TEST_ACCOUNTS:
        print("❌ No test accounts configured. Please update TEST_ACCOUNTS in the script.")
        return False
    
    if not TEST_RECIPIENTS:
        print("❌ No test recipients configured. Please update TEST_RECIPIENTS in the script.")
        return False
    
    print("🧪 Testing Single Account SMTP...")
    
    mailer = SmtpMailer()
    account = TEST_ACCOUNTS[0]
    recipient = TEST_RECIPIENTS[0]
    
    print(f"📧 Sending test email from {account['email']} to {recipient}")
    
    success, error_type, message = mailer.send_email(
        account,
        recipient,
        "SMTP Test Email",
        "This is a test email to verify SMTP functionality.",
        None  # No attachments
    )
    
    if success:
        print("✅ Email sent successfully!")
        print(f"   Message: {message}")
        return True
    else:
        print(f"❌ Email sending failed!")
        print(f"   Error Type: {error_type}")
        print(f"   Message: {message}")
        return False

def test_multithreaded_sending():
    """Test multithreaded email sending"""
    if len(TEST_ACCOUNTS) < 2:
        print("❌ Need at least 2 test accounts for multithreading test.")
        return False
    
    if not TEST_RECIPIENTS:
        print("❌ No test recipients configured.")
        return False
    
    print("🧪 Testing Multithreaded SMTP Sending...")
    
    # Setup tracking
    error_tracker = AccountErrorTracker()
    progress_tracker = ProgressTracker(len(TEST_ACCOUNTS))
    
    # Setup queues and threads
    results_queue = queue.Queue()
    threads = []
    
    print(f"🚀 Starting {len(TEST_ACCOUNTS)} worker threads...")
    
    for i, account in enumerate(TEST_ACCOUNTS):
        # Create leads queue for this account
        leads_queue = queue.Queue()
        
        # Add recipients to queue
        for recipient in TEST_RECIPIENTS:
            leads_queue.put(recipient)
        leads_queue.put(None)  # Poison pill
        
        # Initialize progress tracking
        progress_tracker.update_progress(account['email'], 0, len(TEST_RECIPIENTS))
        
        # Start worker thread
        thread = threading.Thread(
            target=send_worker,
            args=(account, leads_queue, results_queue, TEST_CONFIG)
        )
        threads.append(thread)
        thread.start()
        print(f"   ✓ Started worker for {account['email']}")
    
    # Monitor progress
    active_workers = len(threads)
    total_sent = 0
    total_errors = 0
    
    print("\n📊 Monitoring progress...")
    
    while active_workers > 0:
        try:
            result = results_queue.get(timeout=2)
            
            if result['error_type'] == 'COMPLETED':
                active_workers -= 1
                print(f"   ✅ {result['account']} completed ({result['sent_count']} sent)")
                progress_tracker.update_progress(
                    result['account'], 
                    result['sent_count'], 
                    result['sent_count'], 
                    "completed"
                )
            elif result['success'] is False and result['error_type'] != 'COMPLETED':
                total_errors += 1
                error_tracker.add_error(
                    result['account'], 
                    result['error_type'], 
                    result['message']
                )
                print(f"   ❌ Error from {result['account']}: {result['error_type']}")
            elif result['success'] is True:
                total_sent += 1
                print(f"   📧 Sent: {result['account']} -> {result['lead']}")
                
                # Update progress
                total_for_account = progress_tracker.account_progress.get(
                    result['account'], {}
                ).get('total', result['sent_count'])
                progress_tracker.update_progress(
                    result['account'], 
                    result['sent_count'], 
                    total_for_account
                )
            
        except queue.Empty:
            print(f"   ⏳ Waiting... {active_workers} workers still active")
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Final results
    print("\n📈 Final Results:")
    print(f"   Total emails sent: {total_sent}")
    print(f"   Total errors: {total_errors}")
    
    if total_errors > 0:
        print("\n❌ Error Summary:")
        print(error_tracker.get_summary())
    
    return total_sent > 0

def test_error_scenarios():
    """Test various error scenarios"""
    print("🧪 Testing Error Scenarios...")
    
    mailer = SmtpMailer()
    
    # Test 1: Invalid credentials
    print("\n1. Testing invalid credentials...")
    invalid_account = {'email': 'test@gmail.com', 'password': 'wrong_password'}
    success, error_type, message = mailer.send_email(
        invalid_account,
        'test@test.com',
        'Test',
        'Test body'
    )
    
    if not success and error_type == 'AUTH_FAILED':
        print("   ✅ Auth failure correctly detected")
    else:
        print(f"   ⚠️  Unexpected result: {error_type}")
    
    # Test 2: Unsupported provider
    print("\n2. Testing unsupported email provider...")
    unsupported_account = {'email': 'test@unsupported.com', 'password': 'password'}
    success, error_type, message = mailer.send_email(
        unsupported_account,
        'test@test.com',
        'Test',
        'Test body'
    )
    
    if not success and error_type == 'UNSUPPORTED_PROVIDER':
        print("   ✅ Unsupported provider correctly detected")
    else:
        print(f"   ⚠️  Unexpected result: {error_type}")
    
    # Test 3: Rate limiting simulation
    print("\n3. Testing rate limiting...")
    if TEST_ACCOUNTS and TEST_RECIPIENTS:
        account = TEST_ACCOUNTS[0]
        recipient = TEST_RECIPIENTS[0]
        
        start_time = time.time()
        
        # Send multiple emails rapidly
        for i in range(3):
            success, error_type, message = mailer.send_email(
                account,
                recipient,
                f"Rate Test Email {i+1}",
                f"This is rate test email number {i+1}",
                None
            )
            print(f"   Email {i+1}: {'✅ Success' if success else f'❌ {error_type}'}")
        
        end_time = time.time()
        print(f"   Total time for 3 emails: {end_time - start_time:.2f} seconds")

def main():
    """Run all tests"""
    print("="*60)
    print("REAL SMTP FUNCTIONALITY TEST")
    print("="*60)
    
    if not TEST_ACCOUNTS:
        print("\n⚠️  WARNING: No test accounts configured!")
        print("Please update TEST_ACCOUNTS in this script with your test credentials.")
        print("Note: Use app passwords for Gmail accounts.")
        return
    
    if not TEST_RECIPIENTS:
        print("\n⚠️  WARNING: No test recipients configured!")
        print("Please update TEST_RECIPIENTS in this script with test email addresses.")
        return
    
    print(f"\n📋 Test Configuration:")
    print(f"   Accounts: {len(TEST_ACCOUNTS)}")
    print(f"   Recipients: {len(TEST_RECIPIENTS)}")
    
    # Confirm before proceeding
    response = input("\n⚠️  This will send REAL emails. Continue? (y/N): ")
    if response.lower() != 'y':
        print("Test cancelled.")
        return
    
    print("\n" + "="*60)
    
    # Run tests
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Single account
    total_tests += 1
    if test_single_account_smtp():
        tests_passed += 1
    
    print("\n" + "-"*60)
    
    # Test 2: Multithreading (if multiple accounts)
    if len(TEST_ACCOUNTS) >= 2:
        total_tests += 1
        if test_multithreaded_sending():
            tests_passed += 1
        print("\n" + "-"*60)
    
    # Test 3: Error scenarios
    test_error_scenarios()
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == '__main__':
    main()