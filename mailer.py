import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import time
import os
import random
import re
import json
import base64
from threading import Thread, Lock
import queue
from datetime import datetime
import tempfile
import glob
from content import DEFAULT_SUBJECTS, DEFAULT_BODIES, DEFAULT_GMASS_RECIPIENTS, SEND_DELAY_SECONDS, PDF_ATTACHMENT_DIR, IMAGE_ATTACHMENT_DIR, SENDER_NAME_TYPES, DEFAULT_SENDER_NAME_TYPE, generate_sender_name
from invoice import InvoiceGenerator

try:
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    GMAIL_API_AVAILABLE = True
except ImportError:
    print("Gmail API libraries not available. Install with: pip install google-auth-oauthlib google-api-python-client")
    GMAIL_API_AVAILABLE = False

# Gmail API setup
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def _ensure_service_for_sender(creds_json_path, email_hint=None, credential_files=None):
    """Ensure Gmail service exists for sender using new authentication manager"""
    if not GMAIL_API_AVAILABLE:
        return None
    
    try:
        from gmail_auth_manager import gmail_auth_manager
        
        # Load credentials if provided
        if credential_files:
            gmail_auth_manager.load_credentials(credential_files)
        
        # Try to get service for the account
        if email_hint:
            service = gmail_auth_manager.get_service_for_account(email_hint)
            if service:
                return service
            else:
                print(f"Gmail API service not available for {email_hint}. Please authenticate via UI first.")
                return None
        
        return None
        
    except ImportError:
        print("Gmail authentication system not available. Please ensure gmail_auth_manager.py is present.")
        return None
    except Exception as e:
        print(f"Error with Gmail authentication system: {e}")
        return None

def _gmail_api_send(service, sender, to_addr, subject, body_text, attachments=None, sender_name=None):
    """Send email via Gmail API"""
    try:
        message = MIMEMultipart()
        message['to'] = to_addr
        message['from'] = f"{sender_name} <{sender}>" if sender_name else sender
        message['subject'] = subject
        message.attach(MIMEText(body_text, 'plain'))
        
        if attachments:
            for filename, filepath in attachments.items():
                with open(filepath, 'rb') as f:
                    part = MIMEApplication(f.read(), Name=filename)
                    part['Content-Disposition'] = f'attachment; filename="{filename}"'
                    message.attach(part)
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        send_message = service.users().messages().send(
            userId='me', 
            body={'raw': raw_message}
        ).execute()
        
        return True, None, f"Gmail API: Email sent from {sender} to {to_addr}"
    except Exception as e:
        return False, "GMAIL_API_ERROR", f"Gmail API error for {sender}: {e}"

class SmtpMailer:
    """SMTP email sender with support for multiple providers"""
    
    def __init__(self):
        self.smtp_configs = {
            'gmail.com': {'server': 'smtp.gmail.com', 'port': 587},
            'yahoo.com': {'server': 'smtp.mail.yahoo.com', 'port': 587},
            'hotmail.com': {'server': 'smtp-mail.outlook.com', 'port': 587},
            'outlook.com': {'server': 'smtp-mail.outlook.com', 'port': 587},
            'aol.com': {'server': 'smtp.aol.com', 'port': 587}
        }
    
    def send_email(self, account, to_addr, subject, body, attachments=None, sender_name=None):
        """Send email via SMTP"""
        try:
            domain = account['email'].split('@')[1].lower()
            config = self.smtp_configs.get(domain)
            
            if not config:
                return False, "UNSUPPORTED_PROVIDER", f"Unsupported email provider: {domain}"
            
            msg = MIMEMultipart()
            msg['From'] = f"{sender_name} <{account['email']}>" if sender_name else account['email']
            msg['To'] = to_addr
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Add attachments
            if attachments:
                for filename, filepath in attachments.items():
                    with open(filepath, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=filename)
                        part['Content-Disposition'] = f'attachment; filename="{filename}"'
                        msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(config['server'], config['port'])
            server.starttls()
            server.login(account['email'], account['password'])
            server.send_message(msg)
            server.quit()
            
            return True, None, f"Email sent from {account['email']} to {to_addr}"
            
        except smtplib.SMTPAuthenticationError:
            return False, "AUTH_FAILED", f"Authentication failed for {account['email']}"
        except smtplib.SMTPRecipientsRefused:
            return False, "INVALID_RECIPIENT", f"Invalid recipient: {to_addr}"
        except Exception as e:
            return False, "SMTP_ERROR", f"SMTP error for {account['email']}: {e}"

class AccountErrorTracker:
    """Track and categorize email sending errors"""
    
    def __init__(self):
        self.account_errors = {}
        self.error_types = {
            'AUTH_FAILED': 'Authentication Failed',
            'RATE_LIMITED': 'Rate Limited',
            'INVALID_RECIPIENT': 'Invalid Recipient', 
            'SMTP_ERROR': 'SMTP Error',
            'GMAIL_API_ERROR': 'Gmail API Error',
            'SUSPENDED': 'Account Suspended',
            'QUOTA_EXCEEDED': 'Quota Exceeded',
            'CONNECTION_ERROR': 'Connection Error',
            'TIMEOUT': 'Timeout',
            'BLOCKED': 'Account Blocked',
            'UNSUPPORTED_PROVIDER': 'Unsupported Provider',
            'OTHER': 'Other Error'
        }
    
    def add_error(self, account_email, error_type, error_msg):
        """Add an error for an account"""
        if account_email not in self.account_errors:
            self.account_errors[account_email] = []
        
        self.account_errors[account_email].append({
            'type': error_type,
            'message': error_msg,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })
    
    def get_html_report(self):
        """Get HTML formatted error report"""
        if not self.account_errors:
            return "No errors yet"
        
        html = "<div style='font-family: monospace; font-size: 12px;'>"
        for account, errors in self.account_errors.items():
            html += f"<h4>{account} ({len(errors)} errors)</h4>"
            for error in errors[-3:]:  # Show last 3 errors
                error_name = self.error_types.get(error['type'], error['type'])
                html += f"<p>{error['timestamp']} - {error_name}: {error['message']}</p>"
        html += "</div>"
        return html
    
    def get_summary(self):
        """Get error summary"""
        if not self.account_errors:
            return "No errors"
        
        total_errors = sum(len(errors) for errors in self.account_errors.values())
        total_accounts = len(self.account_errors)
        return f"Total: {total_errors} errors across {total_accounts} accounts"

class ProgressTracker:
    """Track email sending progress per account"""
    
    def __init__(self, total_accounts):
        self.total_accounts = total_accounts
        self.account_progress = {}
        self.start_time = datetime.now()
    
    def update_progress(self, account_email, sent, total, status="sending"):
        """Update progress for an account"""
        self.account_progress[account_email] = {
            'sent': sent,
            'total': total,
            'status': status,
            'last_update': datetime.now()
        }
    
    def get_html_report(self):
        """Get HTML formatted progress report"""
        if not self.account_progress:
            return "No progress data"
        
        html = "<div style='font-family: monospace; font-size: 12px;'>"
        html += f"<h4>Progress ({len(self.account_progress)}/{self.total_accounts} accounts active)</h4>"
        
        total_sent = 0
        total_target = 0
        
        for account, progress in self.account_progress.items():
            sent = progress['sent']
            total = progress['total']
            status = progress['status']
            
            total_sent += sent
            total_target += total
            
            percentage = int((sent / total * 100)) if total > 0 else 0
            bar_width = int(percentage / 5)  # 20 char width bar
            bar = "█" * bar_width + "░" * (20 - bar_width)
            
            html += f"<p>{account}: {bar} {sent}/{total} ({percentage}%) - {status}</p>"
        
        overall_percentage = int((total_sent / total_target * 100)) if total_target > 0 else 0
        elapsed = datetime.now() - self.start_time
        html += f"<p><b>Overall: {total_sent}/{total_target} ({overall_percentage}%) - {elapsed}</b></p>"
        html += "</div>"
        return html

def parse_file_lines(file_obj):
    """Parse lines from uploaded file"""
    if not file_obj:
        return []
    
    try:
        with open(file_obj.name, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        return lines
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

def validate_accounts_file(accounts_lines):
    """Validate accounts file format"""
    if not accounts_lines:
        return False, "No accounts found", []
    
    valid_accounts = []
    for i, line in enumerate(accounts_lines):
        if ',' not in line:
            return False, f"Line {i+1}: Invalid format (missing comma)", []
        
        email, password = line.split(',', 1)
        email = email.strip()
        password = password.strip()
        
        if not email or not password:
            return False, f"Line {i+1}: Empty email or password", []
        
        if '@' not in email:
            return False, f"Line {i+1}: Invalid email format", []
        
        valid_accounts.append({'email': email, 'password': password})
    
    return True, f"Valid: {len(valid_accounts)} accounts", valid_accounts

def validate_leads_file(leads_lines):
    """Validate leads file format"""
    if not leads_lines:
        return False, "No leads found", []
    
    valid_leads = []
    for i, line in enumerate(leads_lines):
        email = line.strip()
        if not email:
            continue
        
        if '@' not in email:
            return False, f"Line {i+1}: Invalid email format", []
        
        valid_leads.append(email)
    
    return True, f"Valid: {len(valid_leads)} leads", valid_leads

def update_file_stats(accounts_file, leads_file):
    """Update file statistics display"""
    accounts_html = "No file uploaded"
    leads_html = "No file uploaded"
    
    if accounts_file:
        accounts_lines = parse_file_lines(accounts_file)
        acc_valid, acc_msg, valid_accounts = validate_accounts_file(accounts_lines)
        color = "green" if acc_valid else "red"
        accounts_html = f"<span style='color: {color};'>{acc_msg}</span>"
    
    if leads_file:
        leads_lines = parse_file_lines(leads_file)
        leads_valid, leads_msg, valid_leads = validate_leads_file(leads_lines)
        color = "green" if leads_valid else "red"
        leads_html = f"<span style='color: {color};'>{leads_msg}</span>"
    
    return accounts_html, leads_html

def update_attachment_stats(include_pdfs, include_images):
    """Update attachment statistics display"""
    pdf_count = len(glob.glob(os.path.join(PDF_ATTACHMENT_DIR, "*.pdf"))) if os.path.exists(PDF_ATTACHMENT_DIR) else 0
    img_count = len(glob.glob(os.path.join(IMAGE_ATTACHMENT_DIR, "*.jpg")) + 
                   glob.glob(os.path.join(IMAGE_ATTACHMENT_DIR, "*.png"))) if os.path.exists(IMAGE_ATTACHMENT_DIR) else 0
    
    stats = []
    if include_pdfs:
        stats.append(f"PDFs: {pdf_count}")
    if include_images:
        stats.append(f"Images: {img_count}")
    
    if not stats:
        return "No attachments selected"
    
    return " | ".join(stats)

def get_random_attachment(include_pdfs, include_images, attachment_format):
    """Get random attachment file"""
    attachments = {}
    
    # Get PDF attachments
    if include_pdfs and os.path.exists(PDF_ATTACHMENT_DIR):
        pdf_files = glob.glob(os.path.join(PDF_ATTACHMENT_DIR, "*.pdf"))
        if pdf_files:
            pdf_file = random.choice(pdf_files)
            attachments[os.path.basename(pdf_file)] = pdf_file
    
    # Get image attachments
    if include_images and os.path.exists(IMAGE_ATTACHMENT_DIR):
        img_files = (glob.glob(os.path.join(IMAGE_ATTACHMENT_DIR, "*.jpg")) +
                    glob.glob(os.path.join(IMAGE_ATTACHMENT_DIR, "*.png")))
        if img_files:
            img_file = random.choice(img_files)
            attachments[os.path.basename(img_file)] = img_file
    
    return attachments

# Global lock for file operations
file_lock = Lock()

def remove_email_from_leads_file(leads_file_path, email_to_remove):
    """Thread-safe removal of email from leads file"""
    if not leads_file_path or not os.path.exists(leads_file_path):
        return
    
    with file_lock:
        try:
            # Read current leads
            with open(leads_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Filter out the sent email
            remaining_lines = []
            for line in lines:
                email = line.strip()
                if email and email != email_to_remove:
                    remaining_lines.append(line)
            
            # Write back the remaining leads
            with open(leads_file_path, 'w', encoding='utf-8') as f:
                f.writelines(remaining_lines)
                
        except Exception as e:
            print(f"Error removing {email_to_remove} from leads file: {e}")

def send_worker(account, leads_queue, results_queue, config):
    """Worker thread for sending emails from one account"""
    mailer = SmtpMailer()
    invoice_gen = InvoiceGenerator()
    sent_count = 0
    
    # Setup Gmail API if needed
    gmail_service = None
    if config['use_gmail_api'] and account['email'].endswith('@gmail.com'):
        if config['gmail_credentials_files']:
            try:
                gmail_service = _ensure_service_for_sender(
                    config['gmail_credentials_files'][0].name if config.get('gmail_credentials_files') else None, 
                    account['email'],
                    config.get('gmail_credentials_files')
                )
            except:
                pass
    
    while True:
        try:
            # Get next lead
            lead_email = leads_queue.get(timeout=1)
            if lead_email is None:  # Poison pill
                break
            
            # Generate content
            subject = random.choice(config['subjects'])
            body = random.choice(config['bodies'])
            
            # Generate sender name
            sender_name = generate_sender_name(config.get('sender_name_type', 'business'))
            
            # Get attachments
            attachments = get_random_attachment(
                config['include_pdfs'], 
                config['include_images'], 
                config['attachment_format']
            )
            
            # Generate invoice if phone number provided
            if config['support_number']:
                try:
                    # Parse phone numbers from multiline string and select one randomly
                    phone_numbers = [num.strip() for num in config['support_number'].split('\n') if num.strip()]
                    selected_phone = random.choice(phone_numbers) if phone_numbers else config['support_number']
                    
                    invoice_path = invoice_gen.generate_for_recipient(
                        lead_email, 
                        selected_phone, 
                        config['attachment_format']
                    )
                    prefix = random.choice(["INV", "PO"])
                    # Get correct file extension based on attachment format
                    if config['attachment_format'] == 'pdf':
                        extension = 'pdf'
                    elif config['attachment_format'] == 'heic':
                        extension = 'heic'
                    else:  # default to png for image format
                        extension = 'png'
                    invoice_filename = f"{prefix}_{random.randint(1000,9999)}.{extension}"
                    attachments[invoice_filename] = invoice_path
                except Exception as e:
                    print(f"Error generating invoice: {e}")
                    pass
            
            # Send email
            success = False
            error_type = None
            message = ""
            
            if gmail_service and account['email'].endswith('@gmail.com'):
                success, error_type, message = _gmail_api_send(
                    gmail_service, account['email'], lead_email, subject, body, attachments, sender_name
                )
            else:
                success, error_type, message = mailer.send_email(
                    account, lead_email, subject, body, attachments, sender_name
                )
            
            if success:
                sent_count += 1
                # Remove email from leads file immediately after successful send
                if config.get('leads_file_path') and config.get('mode') == 'leads':
                    remove_email_from_leads_file(config['leads_file_path'], lead_email)
            
            # Report result
            results_queue.put({
                'account': account['email'],
                'lead': lead_email,
                'success': success,
                'error_type': error_type,
                'message': message,
                'sent_count': sent_count
            })
            
            # Rate limiting
            time.sleep(SEND_DELAY_SECONDS)
            
        except queue.Empty:
            continue
        except Exception as e:
            results_queue.put({
                'account': account['email'],
                'lead': None,
                'success': False,
                'error_type': 'WORKER_ERROR',
                'message': f"Worker error: {e}",
                'sent_count': sent_count
            })
            break
    
    # Signal completion
    results_queue.put({
        'account': account['email'],
        'lead': None,
        'success': None,
        'error_type': 'COMPLETED',
        'message': f"Account {account['email']} completed with {sent_count} emails sent",
        'sent_count': sent_count
    })

def main_worker(accounts_file, leads_file, leads_per_account, num_accounts_to_use, mode, 
                subjects_text, bodies_text, gmass_recipients_text, include_pdfs, include_images, 
                support_number, attachment_format, use_gmail_api, gmail_credentials_files, sender_name_type="business"):
    """Main worker function for email sending"""
    
    # Parse and validate inputs
    if not accounts_file:
        yield "ERROR: No accounts file provided", "", "", ""
        return
    
    accounts_lines = parse_file_lines(accounts_file)
    acc_valid, acc_msg, valid_accounts = validate_accounts_file(accounts_lines)
    
    if not acc_valid:
        yield f"ERROR: Accounts validation failed: {acc_msg}", "", "", ""
        return
    
    # Parse subjects and bodies
    subjects = [s.strip() for s in subjects_text.split('\n') if s.strip()]
    bodies = [b.strip() for b in bodies_text.split('\n') if b.strip()]
    
    if not subjects:
        subjects = DEFAULT_SUBJECTS
    if not bodies:
        bodies = DEFAULT_BODIES
    
    # Handle different modes
    if mode == "gmass":
        # GMass mode - use gmass recipients
        gmass_recipients = [r.strip() for r in gmass_recipients_text.split('\n') if r.strip()]
        if not gmass_recipients:
            gmass_recipients = DEFAULT_GMASS_RECIPIENTS
        all_leads = gmass_recipients
    else:
        # Leads mode - use leads file
        if not leads_file:
            yield "ERROR: No leads file provided for leads mode", "", "", ""
            return
        
        leads_lines = parse_file_lines(leads_file)
        leads_valid, leads_msg, valid_leads = validate_leads_file(leads_lines)
        
        if not leads_valid:
            yield f"ERROR: Leads validation failed: {leads_msg}", "", "", ""
            return
        
        all_leads = valid_leads
    
    # Limit accounts
    accounts_to_use = valid_accounts[:num_accounts_to_use]
    
    # Setup tracking
    error_tracker = AccountErrorTracker()
    progress_tracker = ProgressTracker(len(accounts_to_use))
    
    # Create worker configuration
    config = {
        'subjects': subjects,
        'bodies': bodies,
        'include_pdfs': include_pdfs,
        'include_images': include_images,
        'support_number': support_number,
        'attachment_format': attachment_format,
        'use_gmail_api': use_gmail_api,
        'gmail_credentials_files': gmail_credentials_files,
        'mode': mode,
        'leads_file_path': leads_file.name if leads_file and mode == 'leads' else None,
        'sender_name_type': sender_name_type
    }
    
    # Distribute leads among accounts
    leads_per_account = int(leads_per_account)
    
    # Create queues and start workers
    leads_queues = {}
    results_queue = queue.Queue()
    worker_threads = {}
    
    # Pre-calculate lead distribution for leads mode
    if mode == "leads":
        # Equal distribution with leads_per_account as cap
        total_leads = len(all_leads)
        num_accounts = len(accounts_to_use)
        
        # Calculate base leads per account and remainder
        base_leads_per_account = total_leads // num_accounts
        remainder = total_leads % num_accounts
        
        # Apply cap: each account gets min(calculated_leads, leads_per_account)
        leads_distribution = []
        start_idx = 0
        
        for i in range(num_accounts):
            # First 'remainder' accounts get +1 extra lead
            account_lead_count = base_leads_per_account + (1 if i < remainder else 0)
            # Apply the cap
            account_lead_count = min(account_lead_count, leads_per_account)
            
            end_idx = start_idx + account_lead_count
            account_leads = all_leads[start_idx:end_idx]
            leads_distribution.append(account_leads)
            start_idx = end_idx
    
    for i, account in enumerate(accounts_to_use):
        leads_queue = queue.Queue()
        leads_queues[account['email']] = leads_queue
        
        # Distribute leads
        if mode == "leads":
            # Use pre-calculated equal distribution
            account_leads = leads_distribution[i]
        else:
            # GMass mode - ALL accounts send to ALL recipients (no limit)
            account_leads = all_leads
        
        # Add leads to queue
        for lead in account_leads:
            leads_queue.put(lead)
        leads_queue.put(None)  # Poison pill
        
        # Start worker thread
        worker = Thread(
            target=send_worker,
            args=(account, leads_queue, results_queue, config)
        )
        worker.start()
        worker_threads[account['email']] = worker
        
        # Initialize progress
        progress_tracker.update_progress(account['email'], 0, len(account_leads))
    
    # Monitor progress
    active_workers = len(worker_threads)
    
    while active_workers > 0:
        try:
            result = results_queue.get(timeout=2)
            
            if result['error_type'] == 'COMPLETED':
                active_workers -= 1
                progress_tracker.update_progress(
                    result['account'], 
                    result['sent_count'], 
                    result['sent_count'], 
                    "completed"
                )
            elif result['success'] is False and result['error_type'] != 'COMPLETED':
                error_tracker.add_error(
                    result['account'], 
                    result['error_type'], 
                    result['message']
                )
            elif result['success'] is True:
                # Update progress for successful sends
                total_for_account = progress_tracker.account_progress.get(
                    result['account'], {}
                ).get('total', result['sent_count'])
                progress_tracker.update_progress(
                    result['account'], 
                    result['sent_count'], 
                    total_for_account
                )
            
            # Yield current status
            log_msg = f"Processing... {active_workers} workers active"
            progress_html = progress_tracker.get_html_report()
            errors_html = error_tracker.get_html_report()
            summary_html = error_tracker.get_summary()
            
            yield log_msg, progress_html, errors_html, summary_html
            
        except queue.Empty:
            # Timeout - yield current status
            log_msg = f"Processing... {active_workers} workers active"
            progress_html = progress_tracker.get_html_report()
            errors_html = error_tracker.get_html_report()
            summary_html = error_tracker.get_summary()
            
            yield log_msg, progress_html, errors_html, summary_html
    
    # Wait for all threads to complete
    for worker in worker_threads.values():
        worker.join()
    
    # Final status
    final_log = "All tasks complete"
    final_progress = progress_tracker.get_html_report()
    final_errors = error_tracker.get_html_report()
    final_summary = error_tracker.get_summary()
    
    yield final_log, final_progress, final_errors, final_summary