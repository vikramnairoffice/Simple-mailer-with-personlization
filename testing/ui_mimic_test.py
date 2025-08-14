#!/usr/bin/env python3
"""
Test that mimics exactly what the UI is doing
"""
import sys
import os
sys.path.append('..')

from mailer import SmtpMailer
from invoice import InvoiceGenerator
from content import generate_sender_name
import random

def test_ui_email_sending():
    print("UI Email Sending Mimic Test")
    print("=" * 50)
    
    # Read accounts
    with open('apppass.txt', 'r') as f:
        accounts = []
        for line in f:
            line = line.strip()
            if line and ',' in line:
                email, password = line.split(',', 1)
                accounts.append({'email': email.strip(), 'password': password.strip()})
    
    # Read leads (first recipient)
    with open('leadstest.txt', 'r') as f:
        leads = [line.strip() for line in f if line.strip()]
    
    if not leads:
        print("No leads found")
        return
    
    recipient = leads[0]
    print(f"Test recipient: {recipient}")
    
    # Initialize components like the UI does
    mailer = SmtpMailer()
    invoice_gen = InvoiceGenerator()
    
    # Test each account
    for account in accounts:
        print(f"\nTesting account: {account['email']}")
        
        try:
            # Generate content like UI does
            subject = "Test Email from UI Mimic"
            body = "This email mimics exactly what the UI should send."
            
            # Generate sender name like UI
            sender_name = generate_sender_name('business')
            print(f"Generated sender name: {sender_name}")
            
            # Generate invoice with phone numbers like UI
            support_numbers = ["(888)-124 4567", "(888)-124 4567"]
            support_number = random.choice(support_numbers)
            
            # Generate invoice for HEIC format
            print("Generating invoice...")
            invoice_path = invoice_gen.generate_for_recipient(
                recipient, 
                support_number, 
                'heic'  # HEIC format like UI setting
            )
            print(f"Invoice generated: {invoice_path}")
            
            # Create attachments dict like UI
            prefix = random.choice(["INV", "PO"])
            invoice_filename = f"{prefix}_{random.randint(1000,9999)}.png"  # HEIC becomes PNG
            attachments = {invoice_filename: invoice_path}
            
            print(f"Attachment: {invoice_filename} -> {invoice_path}")
            
            # Send email exactly like the UI worker does
            print("Sending email...")
            success, error_type, message = mailer.send_email(
                account, recipient, subject, body, attachments, sender_name
            )
            
            if success:
                print(f"SUCCESS: {message}")
            else:
                print(f"ERROR ({error_type}): {message}")
                
        except Exception as e:
            print(f"ERROR: Exception occurred: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_ui_email_sending()