import time
import threading
from concurrent.futures import ThreadPoolExecutor
from invoice import InvoiceGenerator
import os

def test_single_attachment_generation():
    """Test time for single attachment generation"""
    print("=== Testing Single Attachment Generation ===")
    
    invoice_gen = InvoiceGenerator()
    
    start_time = time.time()
    invoice_path = invoice_gen.generate_for_recipient(
        "test@example.com", 
        phone_number="1-800-TEST-123",
        output_format="png"
    )
    end_time = time.time()
    
    generation_time = end_time - start_time
    print(f"Single attachment generation time: {generation_time:.3f} seconds")
    print(f"Generated file: {invoice_path}")
    print(f"File exists: {os.path.exists(invoice_path) if invoice_path else 'No path returned'}")
    
    if invoice_path and os.path.exists(invoice_path):
        file_size = os.path.getsize(invoice_path) / 1024  # KB
        print(f"File size: {file_size:.1f} KB")
    
    return generation_time

def generate_attachment_worker(thread_id, num_attachments):
    """Worker function for multi-threaded attachment generation"""
    invoice_gen = InvoiceGenerator()
    thread_times = []
    
    print(f"Thread {thread_id}: Generating {num_attachments} attachments")
    
    for i in range(num_attachments):
        start_time = time.time()
        
        invoice_path = invoice_gen.generate_for_recipient(
            f"test{thread_id}_{i}@example.com", 
            phone_number="1-800-TEST-123",
            output_format="png"
        )
        
        end_time = time.time()
        generation_time = end_time - start_time
        thread_times.append(generation_time)
        
        print(f"Thread {thread_id}, Attachment {i+1}: {generation_time:.3f}s")
    
    avg_time = sum(thread_times) / len(thread_times)
    max_time = max(thread_times)
    min_time = min(thread_times)
    
    print(f"Thread {thread_id} Summary: Avg={avg_time:.3f}s, Min={min_time:.3f}s, Max={max_time:.3f}s")
    return thread_times

def test_multithreaded_attachment_generation():
    """Test attachment generation with multiple threads (simulating email sending)"""
    print("\n=== Testing Multi-threaded Attachment Generation ===")
    print("Simulating 10 threads each generating 5 attachments (like email test)")
    
    num_threads = 10
    attachments_per_thread = 5
    
    start_time = time.time()
    
    # Use ThreadPoolExecutor to simulate the email sending scenario
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for thread_id in range(num_threads):
            future = executor.submit(generate_attachment_worker, thread_id, attachments_per_thread)
            futures.append(future)
        
        # Collect results
        all_times = []
        for future in futures:
            thread_times = future.result()
            all_times.extend(thread_times)
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    # Analysis
    total_attachments = num_threads * attachments_per_thread
    avg_generation_time = sum(all_times) / len(all_times)
    max_generation_time = max(all_times)
    min_generation_time = min(all_times)
    
    print(f"\n=== Multi-threaded Results ===")
    print(f"Total attachments generated: {total_attachments}")
    print(f"Total duration: {total_duration:.2f} seconds")
    print(f"Average generation time: {avg_generation_time:.3f} seconds")
    print(f"Minimum generation time: {min_generation_time:.3f} seconds") 
    print(f"Maximum generation time: {max_generation_time:.3f} seconds")
    print(f"Attachments per second: {total_attachments/total_duration:.2f}")
    
    # Critical analysis for 4.5-second email timing
    print(f"\n=== 4.5-Second Email Timing Analysis ===")
    
    if avg_generation_time < 4.0:
        print(f"✅ GOOD: Avg generation time ({avg_generation_time:.3f}s) fits within 4.5s window")
    else:
        print(f"❌ PROBLEM: Avg generation time ({avg_generation_time:.3f}s) may exceed 4.5s window")
    
    if max_generation_time < 4.0:
        print(f"✅ GOOD: Max generation time ({max_generation_time:.3f}s) fits within 4.5s window")
    else:
        print(f"⚠️  WARNING: Max generation time ({max_generation_time:.3f}s) may cause timing issues")
    
    # Simulate email timing with attachment generation
    print(f"\n=== Simulated Email Timing ===")
    simulated_smtp_time = 0.2  # Simulated SMTP processing time
    total_email_time = avg_generation_time + simulated_smtp_time
    
    print(f"Attachment generation: {avg_generation_time:.3f}s")
    print(f"SMTP processing: {simulated_smtp_time:.3f}s") 
    print(f"Total email time: {total_email_time:.3f}s")
    print(f"Required delay: 4.5s")
    print(f"Remaining delay needed: {4.5 - total_email_time:.3f}s")
    
    if total_email_time <= 4.5:
        print(f"✅ TIMING OK: Email processing fits within 4.5s requirement")
    else:
        print(f"❌ TIMING ISSUE: Email processing exceeds 4.5s requirement")

if __name__ == "__main__":
    # Test single attachment first
    single_time = test_single_attachment_generation()
    
    # Test multi-threaded scenario
    test_multithreaded_attachment_generation()
    
    print(f"\n=== Final Assessment ===")
    print(f"Based on these timing tests, attachment generation during")
    print(f"multi-threaded email sending will impact the 4.5-second timing requirement.")
    print(f"The system needs to account for attachment generation time within")
    print(f"each email's processing window.")