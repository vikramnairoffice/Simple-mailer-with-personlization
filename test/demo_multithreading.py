#!/usr/bin/env python3
"""
Multithreading Demo Script

This script demonstrates the multithreading capabilities of the SMTP mailer
without actually sending emails. It uses mocked email sending to show how
multiple worker threads operate concurrently.
"""

import time
import threading
import queue
import random
from unittest.mock import patch
from mailer import send_worker, AccountErrorTracker, ProgressTracker

def demo_multithreading():
    """Demonstrate multithreading with visual progress"""
    print("="*60)
    print("MULTITHREADING DEMONSTRATION")
    print("="*60)
    
    # Setup test accounts
    accounts = [
        {'email': 'demo1@gmail.com', 'password': 'pass1'},
        {'email': 'demo2@yahoo.com', 'password': 'pass2'},
        {'email': 'demo3@hotmail.com', 'password': 'pass3'},
        {'email': 'demo4@outlook.com', 'password': 'pass4'},
        {'email': 'demo5@aol.com', 'password': 'pass5'}
    ]
    
    # Setup test leads
    leads = [f'lead{i}@test.com' for i in range(20)]
    
    print(f"Accounts: {len(accounts)}")
    print(f"Total leads: {len(leads)}")
    print(f"Leads per account: {len(leads) // len(accounts)}")
    
    # Setup configuration
    config = {
        'subjects': ['Demo Email Subject'],
        'bodies': ['This is a demo email body.'],
        'include_pdfs': False,
        'include_images': False,
        'support_number': None,
        'attachment_format': 'pdf',
        'use_gmail_api': False,
        'gmail_credentials_files': []
    }
    
    # Setup tracking
    error_tracker = AccountErrorTracker()
    progress_tracker = ProgressTracker(len(accounts))
    
    # Mock the SMTP sending to simulate realistic behavior
    def mock_send_email(account, to_addr, subject, body, attachments=None):
        # Simulate variable sending time
        time.sleep(random.uniform(0.1, 0.3))
        
        # Simulate occasional failures
        if random.random() < 0.1:  # 10% failure rate
            error_types = ['AUTH_FAILED', 'RATE_LIMITED', 'SMTP_ERROR']
            error_type = random.choice(error_types)
            return False, error_type, f"Simulated {error_type} for {account['email']}"
        
        return True, None, f"Demo email sent from {account['email']} to {to_addr}"
    
    with patch('mailer.SmtpMailer.send_email', side_effect=mock_send_email):
        print("\nStarting worker threads...")
        
        # Setup queues and threads
        results_queue = queue.Queue()
        threads = []
        leads_per_account = len(leads) // len(accounts)
        
        for i, account in enumerate(accounts):
            # Create leads queue for this account
            leads_queue = queue.Queue()
            
            # Distribute leads
            start_idx = i * leads_per_account
            end_idx = start_idx + leads_per_account
            account_leads = leads[start_idx:end_idx]
            
            # Add leads to queue
            for lead in account_leads:
                leads_queue.put(lead)
            leads_queue.put(None)  # Poison pill
            
            # Initialize progress tracking
            progress_tracker.update_progress(account['email'], 0, len(account_leads))
            
            # Start worker thread
            thread = threading.Thread(
                target=send_worker,
                args=(account, leads_queue, results_queue, config)
            )
            threads.append(thread)
            thread.start()
            print(f"  Started worker for {account['email']} ({len(account_leads)} leads)")
        
        print(f"\nMonitoring progress ({len(threads)} workers active)...")
        print("-" * 60)
        
        # Monitor progress with live updates
        active_workers = len(threads)
        total_sent = 0
        total_errors = 0
        last_update = time.time()
        
        while active_workers > 0:
            try:
                result = results_queue.get(timeout=1)
                
                if result['error_type'] == 'COMPLETED':
                    active_workers -= 1
                    progress_tracker.update_progress(
                        result['account'], 
                        result['sent_count'], 
                        result['sent_count'], 
                        "completed"
                    )
                    print(f"[DONE] {result['account']} completed ({result['sent_count']} sent)")
                
                elif result['success'] is False and result['error_type'] != 'COMPLETED':
                    total_errors += 1
                    error_tracker.add_error(
                        result['account'], 
                        result['error_type'], 
                        result['message']
                    )
                    print(f"[ERROR] {result['account']} - {result['error_type']}")
                
                elif result['success'] is True:
                    total_sent += 1
                    # Update progress for successful sends
                    total_for_account = progress_tracker.account_progress.get(
                        result['account'], {}
                    ).get('total', result['sent_count'])
                    progress_tracker.update_progress(
                        result['account'], 
                        result['sent_count'], 
                        total_for_account
                    )
                    
                    # Show periodic progress updates
                    current_time = time.time()
                    if current_time - last_update > 1.0:  # Update every second
                        print(f"  Progress: {total_sent} sent, {total_errors} errors, {active_workers} workers active")
                        last_update = current_time
                
            except queue.Empty:
                # Show status during quiet periods
                current_time = time.time()
                if current_time - last_update > 2.0:
                    print(f"  Status: {total_sent} sent, {total_errors} errors, {active_workers} workers active")
                    last_update = current_time
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        print("-" * 60)
        print("FINAL RESULTS:")
        print(f"  Total emails sent: {total_sent}")
        print(f"  Total errors: {total_errors}")
        print(f"  Success rate: {total_sent / (total_sent + total_errors) * 100:.1f}%")
        
        if total_errors > 0:
            print(f"\nError Summary: {error_tracker.get_summary()}")
        
        print("\nProgress Report:")
        for account, progress in progress_tracker.account_progress.items():
            sent = progress['sent']
            total = progress['total']
            status = progress['status']
            percentage = int((sent / total * 100)) if total > 0 else 0
            print(f"  {account}: {sent}/{total} ({percentage}%) - {status}")

def demo_error_tracking():
    """Demonstrate error tracking capabilities"""
    print("\n" + "="*60)
    print("ERROR TRACKING DEMONSTRATION")
    print("="*60)
    
    tracker = AccountErrorTracker()
    
    # Simulate various errors
    test_errors = [
        ('user1@gmail.com', 'AUTH_FAILED', 'Invalid app password'),
        ('user1@gmail.com', 'RATE_LIMITED', 'Sending too fast'),
        ('user2@yahoo.com', 'SMTP_ERROR', 'Connection timeout'),
        ('user3@hotmail.com', 'INVALID_RECIPIENT', 'Recipient not found'),
        ('user1@gmail.com', 'AUTH_FAILED', 'Password changed'),
        ('user4@aol.com', 'SUSPENDED', 'Account suspended'),
    ]
    
    print("Adding sample errors...")
    for email, error_type, message in test_errors:
        tracker.add_error(email, error_type, message)
        print(f"  {email}: {error_type}")
    
    print(f"\nSummary: {tracker.get_summary()}")
    
    print("\nError types tracked:")
    for error_code, error_name in tracker.error_types.items():
        print(f"  {error_code}: {error_name}")

def demo_progress_tracking():
    """Demonstrate progress tracking capabilities"""
    print("\n" + "="*60)
    print("PROGRESS TRACKING DEMONSTRATION")
    print("="*60)
    
    tracker = ProgressTracker(3)
    
    accounts = ['demo1@gmail.com', 'demo2@yahoo.com', 'demo3@hotmail.com']
    
    print("Simulating progress updates...")
    
    # Simulate progress for each account
    for i, account in enumerate(accounts):
        total_emails = 10
        
        for sent in range(total_emails + 1):
            if sent == 0:
                status = "starting"
            elif sent == total_emails:
                status = "completed"
            else:
                status = "sending"
            
            tracker.update_progress(account, sent, total_emails, status)
            
            if sent % 3 == 0 or sent == total_emails:  # Show progress every 3 emails
                print(f"\n{account} progress update:")
                percentage = int((sent / total_emails * 100))
                bar_width = int(percentage / 5)  # 20 char width bar
                bar = "#" * bar_width + "-" * (20 - bar_width)
                print(f"  {bar} {sent}/{total_emails} ({percentage}%) - {status}")
            
            time.sleep(0.1)  # Small delay for demonstration

if __name__ == '__main__':
    demo_multithreading()
    demo_error_tracking()
    demo_progress_tracking()
    
    print("\n" + "="*60)
    print("DEMONSTRATION COMPLETE")
    print("="*60)
    print("\nKey features demonstrated:")
    print("  [OK] Concurrent worker threads")
    print("  [OK] Real-time progress tracking") 
    print("  [OK] Error classification and reporting")
    print("  [OK] Rate limiting simulation")
    print("  [OK] Thread synchronization")
    print("  [OK] Result aggregation")