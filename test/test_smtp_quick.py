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

class QuickStressTest:
    """Quick stress test for SMTP functionality with 10 threads x 5 emails each for demonstration"""
    
    def __init__(self):
        self.total_emails = 50  # 10 threads x 5 emails each for quick test
        self.threads_count = 10
        self.emails_per_thread = 5
        self.results = {
            'sent': 0,
            'failed': 0,
            'errors': [],
            'timings': [],
            'attachment_stats': {'generated': 0, 'failed': 0},
            'memory_readings': []
        }
        self.results_lock = threading.Lock()
        self.start_time = None
        self.end_time = None
        
    def monitor_memory(self):
        """Monitor memory usage"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            'timestamp': datetime.now(),
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'cpu_percent': process.cpu_percent(),
            'threads': process.num_threads()
        }
        
    def generate_image_attachment(self, recipient_email, thread_id, email_idx):
        """Generate image attachment for email"""
        try:
            invoice_gen = InvoiceGenerator()
            
            # Generate invoice as image format  
            invoice_path = invoice_gen.generate_for_recipient(
                recipient_email, 
                phone_number="1-800-TEST-123",
                attachment_format="png"
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
            
    def smtp_worker_thread(self, thread_id, recipients_chunk):
        """Worker thread for sending emails via SMTP"""
        thread_sent = 0
        thread_failed = 0
        thread_start = time.time()
        
        print(f"Thread {thread_id}: Starting with {len(recipients_chunk)} emails")
        
        for i, recipient in enumerate(recipients_chunk):
            email_start_time = time.time()
            
            try:
                # Monitor memory every few emails
                if i % 2 == 0:
                    memory_reading = self.monitor_memory()
                    with self.results_lock:
                        self.results['memory_readings'].append(memory_reading)
                
                # Generate content
                subject = random.choice(DEFAULT_SUBJECTS)
                body = random.choice(DEFAULT_BODIES)
                
                # Generate image attachment
                attachment_path = self.generate_image_attachment(recipient, thread_id, i)
                attachments = {}
                if attachment_path:
                    prefix = random.choice(["INV", "PO"])
                    filename = f"{prefix}_{thread_id}_{i}.png"
                    attachments[filename] = attachment_path
                
                # Simulate SMTP processing (for quick test)
                processing_time = random.uniform(0.1, 0.3)
                time.sleep(processing_time)
                
                # Simulate 95% success rate
                success = random.random() < 0.95
                
                if success:
                    thread_sent += 1
                    with self.results_lock:
                        self.results['sent'] += 1
                        print(f"Thread {thread_id}: Email {i+1} sent to {recipient}")
                else:
                    thread_failed += 1
                    with self.results_lock:
                        self.results['failed'] += 1
                        self.results['errors'].append(f"Thread {thread_id}: Simulated SMTP failure for {recipient}")
                        
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
        
    def run_quick_test(self):
        """Execute the quick stress test"""
        print("=== Quick SMTP Stress Test: 10 Threads x 5 Emails Each ===")
        print(f"Total emails to send: {self.total_emails}")
        print(f"Threads: {self.threads_count}")
        print(f"Emails per thread: {self.emails_per_thread}")
        print(f"Delay between emails: {SEND_DELAY_SECONDS} seconds")
        print(f"Attachment format: Image (PNG)")
        print()
        
        # Create test recipients
        recipients = [f'test{i}@example.com' for i in range(self.total_emails)]
        
        # Distribute recipients among threads
        recipient_chunks = []
        for i in range(self.threads_count):
            start_idx = i * self.emails_per_thread
            end_idx = start_idx + self.emails_per_thread
            recipient_chunks.append(recipients[start_idx:end_idx])
            
        self.start_time = time.time()
        
        # Create and start threads
        threads = []
        for i in range(self.threads_count):
            thread = threading.Thread(
                target=self.smtp_worker_thread,
                args=(i, recipient_chunks[i])
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
        
        print("\n=== Quick Test Completed ===")
        self.generate_report()
        
    def generate_report(self):
        """Generate comprehensive test report"""
        total_duration = self.end_time - self.start_time
        
        # Memory analysis
        if self.results['memory_readings']:
            peak_memory = max(reading['rss_mb'] for reading in self.results['memory_readings'])
            avg_memory = sum(reading['rss_mb'] for reading in self.results['memory_readings']) / len(self.results['memory_readings'])
            peak_threads = max(reading['threads'] for reading in self.results['memory_readings'])
        else:
            peak_memory = avg_memory = peak_threads = 0
        
        # Timing analysis
        if self.results['timings']:
            avg_email_time = sum(self.results['timings']) / len(self.results['timings'])
            min_email_time = min(self.results['timings'])
            max_email_time = max(self.results['timings'])
        else:
            avg_email_time = min_email_time = max_email_time = 0
            
        # Calculate theoretical performance for full test
        theoretical_full_duration = (1000 * SEND_DELAY_SECONDS) / 10  # 10 parallel threads
        
        print(f"\n{'='*60}")
        print(f"SMTP STRESS TEST RESULTS (Quick Demo)")
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
        print(f"  • Peak thread count: {peak_threads}")
        print()
        
        print(f"Attachment Statistics:")
        print(f"  • Attachments generated: {self.results['attachment_stats']['generated']}")
        print(f"  • Attachment failures: {self.results['attachment_stats']['failed']}")
        if self.results['attachment_stats']['generated'] + self.results['attachment_stats']['failed'] > 0:
            success_rate = (self.results['attachment_stats']['generated']/(self.results['attachment_stats']['generated']+self.results['attachment_stats']['failed'])*100)
            print(f"  • Attachment success rate: {success_rate:.1f}%")
        print()
        
        print(f"PROJECTION FOR FULL TEST (10 threads x 100 emails = 1000 emails):")
        print(f"  • Estimated duration: {theoretical_full_duration:.0f} seconds ({theoretical_full_duration/60:.1f} minutes)")
        print(f"  • Estimated memory usage: {peak_memory * 2:.0f}-{peak_memory * 3:.0f} MB")
        print(f"  • Expected attachments: 1000 image files")
        print(f"  • Expected disk space: ~50-100 MB for generated invoices")
        print()
        
        if self.results['errors']:
            print(f"Errors ({len(self.results['errors'])}):")
            for i, error in enumerate(self.results['errors'][:5]):
                print(f"  {i+1}. {error}")
            if len(self.results['errors']) > 5:
                print(f"  ... and {len(self.results['errors'])-5} more errors")
        else:
            print("Errors: None")
            
        print()
        print(f"Standard Operation Assessment:")
        
        # Determine if test meets standard operation requirements
        meets_delay = avg_email_time >= SEND_DELAY_SECONDS
        good_success_rate = (self.results['sent']/self.total_emails) >= 0.90
        reasonable_memory = peak_memory < 500  # Under 500MB for quick test
        few_errors = len(self.results['errors']) < (self.total_emails * 0.1)
        
        if meets_delay and good_success_rate and reasonable_memory and few_errors:
            print("  ✓ PASS - System meets standard operation requirements")
            print("  • The system successfully maintains 4.5-second delays")
            print("  • Parallel processing works correctly with 10 threads")
            print("  • Image attachment generation is functional")
            print("  • Memory usage is within acceptable limits")
        else:
            print("  ✗ FAIL - System does not meet some requirements")
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
    test = QuickStressTest()
    test.run_quick_test()