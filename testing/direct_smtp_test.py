#!/usr/bin/env python3
"""
Direct SMTP test to verify what's really happening with the accounts
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

def test_smtp_account(email, password, recipient):
    """Test a single SMTP account"""
    print(f"\nTesting SMTP account: {email}")
    
    try:
        # Determine SMTP server based on email domain
        if '@gmail.com' in email:
            smtp_server = "smtp.gmail.com"
            port = 587
        elif '@yahoo.com' in email:
            smtp_server = "smtp.mail.yahoo.com"
            port = 587
        elif '@hotmail.com' in email or '@outlook.com' in email:
            smtp_server = "smtp-mail.outlook.com"
            port = 587
        else:
            print(f"ERROR: Unsupported email domain: {email}")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = recipient
        msg['Subject'] = "SMTP Test - Direct Connection"
        
        body = f"This is a direct SMTP test from {email}. If you receive this, the account is working properly."
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to server
        print(f"Connecting to {smtp_server}:{port}...")
        context = ssl.create_default_context()
        server = smtplib.SMTP(smtp_server, port)
        server.starttls(context=context)
        
        # Login
        print(f"Authenticating {email}...")
        server.login(email, password)
        print(f"SUCCESS: Authentication successful for {email}")
        
        # Send email
        print(f"Sending test email to {recipient}...")
        text = msg.as_string()
        server.sendmail(email, recipient, text)
        print(f"SUCCESS: Email sent successfully from {email}")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"ERROR: Authentication failed for {email}: {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"ERROR: SMTP error for {email}: {e}")
        return False
    except Exception as e:
        print(f"ERROR: General error for {email}: {e}")
        return False

def main():
    print("Direct SMTP Account Testing")
    print("=" * 50)
    
    # Read accounts from apppass.txt
    accounts_file = "apppass.txt"
    if not os.path.exists(accounts_file):
        print(f"ERROR: File not found: {accounts_file}")
        return
    
    # Read test recipient from leadstest.txt (just use first one)
    leads_file = "leadstest.txt"
    if not os.path.exists(leads_file):
        print(f"ERROR: File not found: {leads_file}")
        return
    
    with open(leads_file, 'r') as f:
        recipients = [line.strip() for line in f if line.strip()]
    
    if not recipients:
        print("ERROR: No recipients found in leadstest.txt")
        return
    
    test_recipient = recipients[0]  # Use first recipient for test
    print(f"Test recipient: {test_recipient}")
    
    # Read and test each account
    results = {}
    with open(accounts_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or ',' not in line:
                continue
                
            email, password = line.split(',', 1)
            email = email.strip()
            password = password.strip()
            
            success = test_smtp_account(email, password, test_recipient)
            results[email] = success
    
    # Summary
    print("\n" + "=" * 50)
    print("SMTP Test Results Summary:")
    print("=" * 50)
    
    working_accounts = 0
    total_accounts = len(results)
    
    for email, success in results.items():
        status = "WORKING" if success else "FAILED"
        print(f"{email}: {status}")
        if success:
            working_accounts += 1
    
    print(f"\nFinal Result: {working_accounts}/{total_accounts} accounts working")
    
    if working_accounts == 0:
        print("ERROR: No accounts are working - this explains why you didn't receive emails!")
    elif working_accounts < total_accounts:
        print("WARNING: Some accounts are not working - this explains partial failures")
    else:
        print("SUCCESS: All accounts are working - emails should be delivered")

if __name__ == "__main__":
    main()