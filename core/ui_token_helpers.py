"""
UI Helper Functions for Token-Based Gmail API
Provides functions for token file analysis and Gmail account management
"""

from token_manager import token_manager


def analyze_token_files(token_files):
    """Analyze uploaded token files and return status summary"""
    if not token_files:
        return "No token files uploaded"
    
    if isinstance(token_files, list) and len(token_files) == 0:
        return "No token files uploaded"
    
    try:
        result = token_manager.load_token_files(token_files)
        
        valid_count = len(result['valid'])
        invalid_count = len(result['invalid'])
        
        status_parts = []
        
        if valid_count > 0:
            emails = list(result['valid'].keys())
            email_list = ", ".join(emails[:3])  # Show first 3 emails
            if len(emails) > 3:
                email_list += f" and {len(emails) - 3} more"
            
            status_parts.append(f"Token files loaded: {valid_count} valid accounts found ({email_list})")
        else:
            status_parts.append(f"Token files loaded: {valid_count} valid accounts found")
        
        if invalid_count > 0:
            error_summary = []
            for invalid_item in result['invalid'][:2]:  # Show first 2 errors
                error_summary.append(invalid_item['error'])
            
            error_text = "; ".join(error_summary)
            if len(result['invalid']) > 2:
                error_text += f" and {len(result['invalid']) - 2} more errors"
            
            status_parts.append(f"{invalid_count} invalid files ({error_text})")
        
        return " | ".join(status_parts)
        
    except Exception as e:
        return f"Error analyzing token files: {str(e)}"


def get_authenticated_gmail_accounts():
    """Get list of authenticated Gmail accounts from token manager"""
    try:
        all_emails = token_manager.get_authenticated_emails()
        # Filter to only Gmail accounts
        gmail_accounts = [email for email in all_emails if email.lower().endswith('@gmail.com')]
        return gmail_accounts
    except Exception as e:
        print(f"Error getting authenticated Gmail accounts: {e}")
        return []


def validate_gmail_api_setup(token_files):
    """Validate Gmail API setup with token files"""
    if not token_files:
        return False, "No token files uploaded"
    
    try:
        gmail_accounts = get_authenticated_gmail_accounts()
        
        if len(gmail_accounts) == 0:
            return False, "No Gmail accounts found in uploaded token files"
        
        return True, f"{len(gmail_accounts)} Gmail accounts authenticated and ready"
        
    except Exception as e:
        return False, f"Error validating Gmail API setup: {str(e)}"


def toggle_auth_method(auth_method):
    """Toggle UI elements based on authentication method"""
    if auth_method == "Gmail API":
        return (
            {
                "label": "Gmail Token JSON Files",
                "file_types": [".json"],
                "file_count": "multiple"
            },
            True,  # Show Gmail instructions
            "Upload Gmail token JSON files directly - no OAuth setup needed"
        )
    else:  # App Password
        return (
            {
                "label": "Accounts File (email,password)",
                "file_types": [".txt", ".csv"],
                "file_count": "single"
            },
            False,  # Hide Gmail instructions
            "App Password method selected - Upload accounts file with email,password format"
        )


def update_gmail_api_status(token_files, auth_method):
    """Update Gmail API status table"""
    if auth_method != "Gmail API":
        return [["Not applicable for App Password mode", "", ""]]
    
    if not token_files:
        return [["No token files uploaded", "❌ Pending", "Upload token files first"]]
    
    try:
        is_valid, message = validate_gmail_api_setup(token_files)
        
        if is_valid:
            gmail_accounts = get_authenticated_gmail_accounts()
            status_data = []
            for email in gmail_accounts:
                status_data.append([email, "✅ Authenticated", "Ready"])
            return status_data
        else:
            return [["Error", "❌ Failed", message]]
            
    except Exception as e:
        return [["Error", "❌ Failed", f"Error: {str(e)}"]]


def unified_send_handler(auth_file, auth_method, leads_file, leads_per_account, num_accounts_to_use, mode, 
                        subjects_text, bodies_text, gmass_recipients_text, email_content_mode, 
                        attachment_format, invoice_format, support_number, sender_name_type):
    """Handle both GMass and Leads modes with new authentication method selection"""
    
    # Import main worker here to avoid circular imports
    try:
        from mailer import main_worker_new_mode
    except ImportError:
        return ("Error: Could not import mailer functions", "", "", "", "Import Error", [["Error", "Import failed"]])
    
    # Determine use_gmail_api and accounts_file based on auth_method
    if auth_method == "Gmail API":
        use_gmail_api = True
        accounts_file = None  # No accounts file needed for Gmail API
        gmail_credentials_files = auth_file  # Use auth_file as credentials
    else:  # App Password
        use_gmail_api = False
        accounts_file = auth_file  # Use auth_file as accounts file
        gmail_credentials_files = None  # No credentials needed for App Password
    
    # Call the main worker
    try:
        results_generator = main_worker_new_mode(
            accounts_file, leads_file, leads_per_account, num_accounts_to_use, mode, 
            subjects_text, bodies_text, gmass_recipients_text, email_content_mode, 
            attachment_format, invoice_format, support_number, use_gmail_api, 
            gmail_credentials_files, sender_name_type
        )
        
        # Get the final results
        final_results = None
        for result in results_generator:
            final_results = result
        
        # For GMass mode, also generate URLs
        if mode == "gmass" and auth_file:
            try:
                if auth_method == "App Password":
                    # Parse accounts file for email extraction
                    from mailer import parse_file_lines, validate_accounts_file
                    accounts_lines = parse_file_lines(accounts_file)
                    acc_valid, acc_msg, valid_accounts = validate_accounts_file(accounts_lines)
                    
                    if acc_valid:
                        sender_emails = [acc['email'] for acc in valid_accounts]
                else:  # Gmail API
                    # Get emails from token manager
                    sender_emails = get_authenticated_gmail_accounts()
                
                # Generate GMass URLs
                import urllib.parse
                table_data = []
                for email in sender_emails:
                    if '@' in email:
                        username = email.split('@')[0]
                        encoded_username = urllib.parse.quote(username)
                        url = f"https://www.gmass.co/inbox?q={encoded_username}"
                        table_data.append([email, url])
                    else:
                        table_data.append([f"{email} (Invalid)", "N/A"])
                
                # Update GMass status and URLs
                gmass_status_update = f"Sending complete! Check {len(sender_emails)} GMass URLs below"
                return (*final_results, gmass_status_update, table_data)
            except Exception as e:
                print(f"Error generating GMass URLs: {e}")
                pass
        
        # For leads mode or if GMass URL generation fails
        return (*final_results, "Not applicable for Leads mode", [["N/A", "N/A"]])
        
    except Exception as e:
        return (f"Error during sending: {str(e)}", "", "", "", "Sending Error", [["Error", str(e)]])