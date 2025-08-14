#!/usr/bin/env python3
"""
Direct test of UI's main_worker function
"""
import sys
import os
sys.path.append('..')

from mailer import main_worker
import tempfile

class MockFile:
    def __init__(self, filepath):
        self.name = filepath

def test_ui_main_worker():
    print("Testing UI main_worker function directly")
    print("=" * 50)
    
    # Create mock file objects like Gradio does
    accounts_file = MockFile("apppass.txt")
    leads_file = MockFile("leadstest.txt")
    
    # UI parameters
    leads_per_account = 10
    num_accounts_to_use = 3
    mode = "leads"
    subjects_text = "Test Subject from UI"
    bodies_text = "Test body from UI with HEIC attachment."
    gmass_recipients_text = ""
    include_pdfs = False
    include_images = False
    support_number = "(888)-124 4567\n(888)-124 4567"
    attachment_format = "heic"
    use_gmail_api = False
    gmail_credentials_files = None
    sender_name_type = "business"
    
    print("Calling main_worker with parameters:")
    print(f"- Accounts file: {accounts_file.name}")
    print(f"- Leads file: {leads_file.name}")
    print(f"- Concurrent accounts: {num_accounts_to_use}")
    print(f"- Support numbers: {support_number}")
    print(f"- Attachment format: {attachment_format}")
    print(f"- Include PDFs: {include_pdfs}")
    print(f"- Include Images: {include_images}")
    print("")
    
    try:
        # Call the main_worker function exactly like the UI does
        for result in main_worker(
            accounts_file, leads_file, leads_per_account, num_accounts_to_use, mode,
            subjects_text, bodies_text, gmass_recipients_text, include_pdfs, include_images,
            support_number, attachment_format, use_gmail_api, gmail_credentials_files, sender_name_type
        ):
            log_msg, progress_html, errors_html, summary_html = result
            print(f"LOG: {log_msg}")
            print(f"PROGRESS: {progress_html[:100] if progress_html else 'None'}...")
            print(f"ERRORS: {errors_html[:100] if errors_html else 'None'}...")
            print(f"SUMMARY: {summary_html[:100] if summary_html else 'None'}...")
            print("-" * 30)
            
    except Exception as e:
        print(f"ERROR in main_worker: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ui_main_worker()