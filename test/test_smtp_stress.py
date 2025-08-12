import threading
import queue
import time
import psutil
import os
import random
import tempfile
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from mailer import SmtpMailer
from invoice import InvoiceGenerator
from content import SEND_DELAY_SECONDS, DEFAULT_SUBJECTS, DEFAULT_BODIES

class MemoryMonitor:
    """Monitor memory usage during test execution"""
    def __init__(self):
        self.memory_readings = []
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Start memory monitoring in background thread"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop memory monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
            
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent()
            
            self.memory_readings.append({
                'timestamp': datetime.now(),
                'rss_mb': memory_info.rss / 1024 / 1024,  # RSS in MB
                'vms_mb': memory_info.vms / 1024 / 1024,  # VMS in MB
                'cpu_percent': cpu_percent,
                'threads': process.num_threads()
            })
            time.sleep(1)  # Sample every second
            
    def get_peak_memory(self):
        """Get peak memory usage"""
        if not self.memory_readings:
            return 0
        return max(reading['rss_mb'] for reading in self.memory_readings)
        
    def get_average_memory(self):
        """Get average memory usage"""
        if not self.memory_readings:
            return 0
        return sum(reading['rss_mb'] for reading in self.memory_readings) / len(self.memory_readings)

class EmailStressTest:
    """Stress test for SMTP functionality with 10 threads x 100 emails each"""
    
    def __init__(self):
        self.total_emails = 1000  # 10 threads x 100 emails each
        self.threads_count = 10
        self.emails_per_thread = 100
        self.memory_monitor = MemoryMonitor()
        self.results = {
            'sent': 0,
            'failed': 0,
            'errors': [],
            'timings': [],
            'attachment_stats': {'generated': 0, 'failed': 0}
        }
        self.results_lock = threading.Lock()
        self.start_time = None
        self.end_time = None
        
    def create_test_accounts(self):
        """Create test SMTP accounts for stress testing"""
        # These are dummy accounts for testing - replace with actual test accounts
        test_accounts = []
        for i in range(self.threads_count):
            test_accounts.append({
                'email': f'testaccount{i}@example.com',
                'password': 'testpassword123'
            })
        return test_accounts
        
    def create_test_recipients(self):
        """Create test recipient email addresses"""
        recipients = []
        for i in range(self.total_emails):
            recipients.append(f'recipient{i}@testdomain.com')
        return recipients
        
    def generate_image_attachment(self, recipient_email, thread_id):
        """Generate image attachment for email"""
        try:
            invoice_gen = InvoiceGenerator()
            
            # Generate invoice as image format
            invoice_path = invoice_gen.generate_for_recipient(
                recipient_email, 
                phone_number="1-800-TEST-123",
                attachment_format="png"  # Force image format
            )
            
            if invoice_path and os.path.exists(invoice_path):
                with self.results_lock:
                    self.results['attachment_stats']['generated'] += 1
                return invoice_path
            else:
                with self.results_lock:
                    self.results['attachment_stats']['failed'] += 1
                return None
                
        except Exception as e:
            with self.results_lock:
                self.results['attachment_stats']['failed'] += 1
                self.results['errors'].append(f"Attachment generation error: {e}")
            return None
            
    def smtp_worker_thread(self, thread_id, account, recipients_chunk):
        """Worker thread for sending emails via SMTP"""
        mailer = SmtpMailer()
        thread_sent = 0
        thread_failed = 0
        thread_start = time.time()
        
        print(f"Thread {thread_id}: Starting with {len(recipients_chunk)} emails")
        
        for i, recipient in enumerate(recipients_chunk):
            email_start_time = time.time()
            
            try:
                # Generate content
                subject = random.choice(DEFAULT_SUBJECTS)
                body = random.choice(DEFAULT_BODIES)
                
                # Generate image attachment
                attachment_path = self.generate_image_attachment(recipient, thread_id)
                attachments = {}
                if attachment_path:
                    prefix = random.choice(["INV", "PO"])
                    filename = f"{prefix}_{thread_id}_{i}.png"
                    attachments[filename] = attachment_path
                
                # Simulate SMTP sending (replace with actual sending for real test)
                # For stress test, we'll simulate the process without actual email sending
                success = self.simulate_smtp_send(account, recipient, subject, body, attachments)
                
                if success:
                    thread_sent += 1
                    with self.results_lock:
                        self.results['sent'] += 1
                else:
                    thread_failed += 1
                    with self.results_lock:
                        self.results['failed'] += 1
                        
                # Enforce 4.5 second delay
                email_duration = time.time() - email_start_time
                remaining_delay = SEND_DELAY_SECONDS - email_duration
                if remaining_delay > 0:
                    time.sleep(remaining_delay)
                    
                # Record timing
                total_email_time = time.time() - email_start_time
                with self.results_lock:
                    self.results['timings'].append(total_email_time)
                    
            except Exception as e:
                thread_failed += 1
                with self.results_lock:
                    self.results['failed'] += 1
                    self.results['errors'].append(f"Thread {thread_id} email {i}: {e}")
                    
        thread_duration = time.time() - thread_start
        print(f"Thread {thread_id}: Completed - Sent: {thread_sent}, Failed: {thread_failed}, Duration: {thread_duration:.2f}s")
        
    def simulate_smtp_send(self, account, recipient, subject, body, attachments):
        """Simulate SMTP sending for stress test"""
        # For actual testing, use: mailer.send_email(account, recipient, subject, body, attachments)
        # This simulation includes processing time similar to real SMTP
        processing_time = random.uniform(0.1, 0.5)  # Simulate SMTP processing
        time.sleep(processing_time)
        
        # Simulate 95% success rate
        return random.random() < 0.95
        
    def run_stress_test(self):
        """Execute the stress test with 10 threads x 100 emails each"""
        print("=== SMTP Stress Test: 10 Threads x 100 Emails Each ===")
        print(f"Total emails to send: {self.total_emails}")
        print(f"Threads: {self.threads_count}")
        print(f"Emails per thread: {self.emails_per_thread}")
        print(f"Delay between emails: {SEND_DELAY_SECONDS} seconds")
        print(f"Attachment format: Image (PNG)")
        print()
        
        # Create test data
        accounts = self.create_test_accounts()
        recipients = self.create_test_recipients()
        
        # Distribute recipients among threads
        recipient_chunks = []
        for i in range(self.threads_count):
            start_idx = i * self.emails_per_thread
            end_idx = start_idx + self.emails_per_thread
            recipient_chunks.append(recipients[start_idx:end_idx])
            
        # Start memory monitoring
        self.memory_monitor.start_monitoring()
        self.start_time = time.time()
        
        # Create and start threads
        threads = []
        for i in range(self.threads_count):
            thread = threading.Thread(
                target=self.smtp_worker_thread,
                args=(i, accounts[i], recipient_chunks[i])
            )
            threads.append(thread)
            
        # Start all threads
        print("Starting all threads...")
        for thread in threads:
            thread.start()
            
        # Wait for all threads to complete
        for i, thread in enumerate(threads):
            thread.join()
            print(f"Thread {i} completed")
            
        self.end_time = time.time()
        self.memory_monitor.stop_monitoring()
        
        print("\n=== Stress Test Completed ===")
        self.generate_report()
        
    def generate_report(self):
        """Generate comprehensive test report"""
        total_duration = self.end_time - self.start_time
        peak_memory = self.memory_monitor.get_peak_memory()
        avg_memory = self.memory_monitor.get_average_memory()
        
        # Timing analysis
        if self.results['timings']:
            avg_email_time = sum(self.results['timings']) / len(self.results['timings'])
            min_email_time = min(self.results['timings'])
            max_email_time = max(self.results['timings'])
        else:
            avg_email_time = min_email_time = max_email_time = 0
            
        # Calculate emails per second
        emails_per_second = self.results['sent'] / total_duration if total_duration > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"SMTP STRESS TEST RESULTS")
        print(f"{'='*60}")
        print(f"Test Configuration:")
        print(f"  • Threads: {self.threads_count}")
        print(f"  • Emails per thread: {self.emails_per_thread}")
        print(f"  • Total emails: {self.total_emails}")
        print(f"  • Delay requirement: {SEND_DELAY_SECONDS} seconds")
        print()
        
        print(f"Performance Results:")
        print(f"  • Total duration: {total_duration:.2f} seconds")
        print(f"  • Emails sent successfully: {self.results['sent']}")
        print(f"  • Emails failed: {self.results['failed']}")
        print(f"  • Success rate: {(self.results['sent']/self.total_emails*100):.1f}%")
        print(f"  • Emails per second: {emails_per_second:.2f}")
        print()
        
        print(f"Timing Analysis:")
        print(f"  • Average email time: {avg_email_time:.2f} seconds")
        print(f"  • Minimum email time: {min_email_time:.2f} seconds")
        print(f"  • Maximum email time: {max_email_time:.2f} seconds")
        print(f"  • Delay compliance: {'✓ PASS' if avg_email_time >= SEND_DELAY_SECONDS else '✗ FAIL'}")
        print()
        
        print(f"Memory Usage:")
        print(f"  • Peak memory (RSS): {peak_memory:.2f} MB")
        print(f"  • Average memory (RSS): {avg_memory:.2f} MB")
        print()
        
        print(f"Attachment Statistics:")
        print(f"  • Attachments generated: {self.results['attachment_stats']['generated']}")
        print(f"  • Attachment failures: {self.results['attachment_stats']['failed']}")
        print(f"  • Attachment success rate: {(self.results['attachment_stats']['generated']/(self.results['attachment_stats']['generated']+self.results['attachment_stats']['failed'])*100):.1f}%")
        print()
        
        if self.results['errors']:
            print(f"Errors ({len(self.results['errors'])}):")
            for i, error in enumerate(self.results['errors'][:10]):  # Show first 10 errors
                print(f"  {i+1}. {error}")
            if len(self.results['errors']) > 10:
                print(f"  ... and {len(self.results['errors'])-10} more errors")
        else:
            print("Errors: None")
            
        print()
        print(f"Standard Operation Assessment:")
        
        # Determine if test meets standard operation requirements
        meets_delay = avg_email_time >= SEND_DELAY_SECONDS
        good_success_rate = (self.results['sent']/self.total_emails) >= 0.90
        reasonable_memory = peak_memory < 1000  # Under 1GB
        few_errors = len(self.results['errors']) < (self.total_emails * 0.1)  # Less than 10% error rate
        
        if meets_delay and good_success_rate and reasonable_memory and few_errors:
            print("  ✓ PASS - System meets standard operation requirements")
        else:
            print("  ✗ FAIL - System does not meet standard operation requirements")
            if not meets_delay:
                print(f"    • Delay requirement not met (avg: {avg_email_time:.2f}s < required: {SEND_DELAY_SECONDS}s)")
            if not good_success_rate:
                print(f"    • Success rate too low ({(self.results['sent']/self.total_emails*100):.1f}% < 90%)")
            if not reasonable_memory:
                print(f"    • Memory usage too high ({peak_memory:.2f} MB)")
            if not few_errors:
                print(f"    • Too many errors ({len(self.results['errors'])} errors)")
                
        print(f"{'='*60}")

if __name__ == "__main__":
    # Run the stress test
    test = EmailStressTest()
    test.run_stress_test()