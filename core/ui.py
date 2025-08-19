import gradio as gr
from mailer import main_worker_new_mode, update_file_stats, update_attachment_stats
from content import DEFAULT_SUBJECTS, DEFAULT_BODIES, DEFAULT_GMASS_RECIPIENTS, SENDER_NAME_TYPES, DEFAULT_SENDER_NAME_TYPE
from ui_token_helpers import (
    analyze_token_files, get_authenticated_gmail_accounts, validate_gmail_api_setup,
    toggle_auth_method, update_gmail_api_status, unified_send_handler
)
import urllib.parse
from mailer import parse_file_lines, validate_accounts_file, convert_mode_to_attachment_flags, main_worker

def send_gmass_test_simple(auth_file, auth_method, mode, subjects_text, bodies_text, gmass_recipients_text, 
                          email_content_mode, attachment_format, invoice_format, support_number, 
                          sender_name_type="business"):
    """Simple GMass test that sends emails and displays URLs in DataFrame format"""
    if mode != "gmass":
        return "Please set mode to 'gmass' for deliverability testing", [["Please set mode to 'gmass'", ""]]
    
    if not auth_file:
        return "Please upload authentication file first", [["Please upload authentication file", ""]]
    
    # Determine use_gmail_api and accounts_file based on auth_method
    if auth_method == "Gmail API":
        use_gmail_api = True
        accounts_file = None
        gmail_credentials_files = auth_file
    else:  # App Password
        use_gmail_api = False
        accounts_file = auth_file
        gmail_credentials_files = None
    
    # Parse accounts (only for App Password method)
    if auth_method == "App Password":
        accounts_lines = parse_file_lines(accounts_file)
        acc_valid, acc_msg, valid_accounts = validate_accounts_file(accounts_lines)
        
        if not acc_valid:
            return f"Accounts file error: {acc_msg}", [["Accounts file error", acc_msg]]
        
        # Get sender emails for URL generation
        sender_emails = [acc['email'] for acc in valid_accounts]
    else:  # Gmail API
        # For Gmail API, we'll get emails from authentication status
        # For now, we'll use placeholder logic
        sender_emails = ["gmail-api@placeholder.com"]  # This should be updated with actual authenticated emails
    
    try:
        # Convert new mode to old format
        include_pdfs, include_images = convert_mode_to_attachment_flags(email_content_mode, attachment_format)
        
        # For invoice mode, use invoice_format instead of attachment_format
        actual_attachment_format = invoice_format if email_content_mode == "Invoice" else attachment_format
        
        # Determine number of accounts for worker
        num_accounts = len(sender_emails) if auth_method == "App Password" else 1
        
        # Use existing main_worker - ensure each SMTP sends to ALL GMass recipients
        results_generator = main_worker(
            accounts_file, None, len(gmass_recipients_text.strip().split('\n')), num_accounts, "gmass", 
            subjects_text, bodies_text, gmass_recipients_text,
            include_pdfs, include_images, support_number, actual_attachment_format,
            use_gmail_api, gmail_credentials_files, sender_name_type
        )
        
        # Wait for completion
        final_log = ""
        for log_html, progress_html, errors_html, summary_html in results_generator:
            final_log = log_html
            if "All tasks complete" in log_html:
                break
        
        # Generate DataFrame data
        table_data = []
        for email in sender_emails:
            if '@' in email:
                username = email.split('@')[0]
                encoded_username = urllib.parse.quote(username)
                url = f"https://www.gmass.co/inbox?q={encoded_username}"
                table_data.append([email, url])
            else:
                table_data.append([f"{email} (Invalid)", "N/A"])
        
        status_message = f"GMass test emails sent successfully! URLs generated for {len(sender_emails)} accounts."
        
        return status_message, table_data
        
    except Exception as e:
        return f"Error during GMass test: {e}", [["Error occurred", str(e)]]

def gradio_ui():
    """Main function to create and return Gradio interface."""
    with gr.Blocks() as demo:
        gr.Markdown("""
        # Multi-Account Email Sender with GMass Deliverability Testing
        <span style='color:gray;'>Upload your accounts and leads files, test deliverability with GMass, then send emails with real-time progress tracking and error monitoring.</span>
        """, elem_id="header")
        
        with gr.Tab("Configuration"):
            with gr.Row():
                subjects_text = gr.Textbox(label="Subjects (one per line)", value="\n".join(DEFAULT_SUBJECTS), lines=4)
                bodies_text = gr.Textbox(label="Bodies (one per line)", value="\n".join(DEFAULT_BODIES), lines=4)
                gmass_recipients_text = gr.Textbox(label="GMass Recipients (one per line, for broadcast mode)", value="\n".join(DEFAULT_GMASS_RECIPIENTS), lines=4)
            
            with gr.Row():
                sender_name_type = gr.Radio(SENDER_NAME_TYPES, value=DEFAULT_SENDER_NAME_TYPE, label="Sender Name Type", info="Business: FirstName + Letters + Word + Letters + Suffix | Personal: FirstName + Letters")
        
        with gr.Tab("Send Emails"):
            # 1. AUTHENTICATION METHOD SELECTION
            with gr.Row():
                auth_method = gr.Radio(
                    choices=["App Password", "Gmail API"], 
                    value="App Password", 
                    label="🔐 Authentication Method",
                    info="Choose how to authenticate your email accounts"
                )
            
            # 2. DYNAMIC FILE UPLOAD SECTION
            with gr.Row():
                auth_file = gr.File(
                    label="Accounts File (email,password)", 
                    file_types=[".txt", ".csv"],
                    file_count="single"
                )
                leads_file = gr.File(label="Leads File (txt/csv, one email per line)")
            
            with gr.Row():
                auth_file_stats = gr.HTML(label="File Statistics")
                leads_stats = gr.HTML(label="Leads Statistics")
            
            # 3. CONDITIONAL INSTRUCTIONS BASED ON SELECTION
            
            # App Password Instructions - Shows when "App Password" is selected
            with gr.Group(visible=True) as app_pass_instructions:
                gr.Markdown("""
                **Format: email,password (one per line)**
                ```
                user1@gmail.com,abcd efgh ijkl mnop
                user2@yahoo.com,password123
                user3@hotmail.com,myapppass
                ```
                """)
            
            # Gmail API Section - Shows when "Gmail API" is selected  
            with gr.Group(visible=False) as gmail_api_section:
                gr.Markdown("**Token-based Gmail API - No OAuth setup needed!**")
                gr.Markdown("Upload your Gmail token JSON files directly. These should contain refresh tokens from your OAuth2 setup.")
                
                # Token status table
                auth_status_table = gr.DataFrame(
                    headers=["Email", "Status", "Action"],
                    datatype=["str", "str", "str"],
                    value=[["No token files uploaded yet", "Pending", "Upload token JSON files first"]],
                    label="Gmail Token Status"
                )
            
            # SMTP Account Selection Section - Shows after validation
            with gr.Group(visible=False) as smtp_selection_section:
                gr.Markdown("### 📋 Select SMTP Accounts to Use")
                gr.Markdown("**Choose which validated accounts to use for sending:**")
                
                smtp_selection_table = gr.DataFrame(
                    headers=["Account", "Status", "Use"],
                    datatype=["str", "str", "bool"],
                    value=[["Upload and validate accounts first", "Pending", False]],
                    label="SMTP Account Selection",
                    interactive=True
                )
                
                selection_status = gr.HTML(value="Upload accounts to see selection options", label="Selection Status")
            
            # Streamlined Attachment/Invoice Selection
            with gr.Row():
                email_content_mode = gr.Radio(["Attachment", "Invoice"], value="Attachment", label="Email Content Type", info="Choose what to include with your emails")
            
            # Conditional inputs based on mode
            with gr.Group(visible=True) as attachment_group:
                with gr.Row():
                    attachment_format = gr.Radio(["pdf", "image"], value="pdf", label="Attachment Format", info="Format for regular attachments from your pdfs/ and images/ folders")
                    attachment_stats = gr.HTML(label="Attachment Statistics")
            
            with gr.Group(visible=False) as invoice_group:
                with gr.Row():
                    support_number = gr.Textbox(label="Support Phone Numbers (one per line)", value="", placeholder="e.g. 123-456-7890\n098-765-4321", lines=2)
                    invoice_format = gr.Radio(["pdf", "image", "heic"], value="pdf", label="Invoice Format", info="Format for generated personalized invoices")
            
            with gr.Row():
                leads_per_account = gr.Number(label="Leads to Send Per Account", value=10, precision=0)
                num_accounts_to_use = gr.Slider(minimum=1, maximum=50, value=1, step=1, label="Number of Concurrent Accounts to Use")
            
            mode = gr.Radio(["gmass", "leads"], value="gmass", label="Mode", info="GMass Broadcast: every account sends to all recipients. Leads Distribution: split leads across accounts.")
            
            with gr.Group(visible=True) as gmass_preview_group:
                gr.Markdown("""### GMass URL Preview
                **URLs will be generated after sending when in GMass mode**""")
                
                
                gmass_status = gr.Textbox(label="GMass Status", value="Ready for GMass mode", interactive=False)
                gmass_urls_display = gr.DataFrame(
                    headers=["Gmail Account", "GMass URL"],
                    datatype=["str", "str"],
                    label="Gmail Accounts & GMass URLs",
                    value=[["URLs will appear here after sending", ""]],
                    interactive=False
                )
            
            start_btn = gr.Button("📧 Start Sending", variant="primary")
            
            with gr.Row():
                progress_html = gr.HTML(label="Progress", value="")
                log_box = gr.HTML(label="Log", value="")
            
            with gr.Row():
                account_errors_display = gr.HTML(label="Account Errors", value="No errors yet")
                error_summary = gr.HTML(label="Error Summary")
            
            # Function to toggle authentication method UI
            def toggle_auth_method_ui(auth_method):
                """Toggle the single upload box label and instructions based on auth method selection"""
                file_update, instructions_visible, status_message = toggle_auth_method(auth_method)
                
                return (
                    gr.update(**file_update),  # auth_file
                    gr.update(visible=not instructions_visible),   # app_pass_instructions (reversed)
                    gr.update(visible=instructions_visible),   # gmail_api_section
                    status_message
                )
            
            # Function to analyze uploaded auth file based on method
            def analyze_auth_file(file, auth_method):
                """Analyze uploaded file based on authentication method"""
                if not file:
                    return "No file uploaded"
                
                if auth_method == "App Password":
                    # Use existing file stats for accounts file
                    return update_file_stats(file, None)[0]  # Return only accounts stats
                else:  # Gmail API
                    return analyze_token_files(file)
            
            # Function to toggle visibility based on email content mode
            def toggle_content_groups(mode):
                if mode == "Attachment":
                    return gr.update(visible=True), gr.update(visible=False)
                else:  # Invoice
                    return gr.update(visible=False), gr.update(visible=True)
            
            # Function to toggle GMass preview section based on mode
            def toggle_gmass_preview(mode):
                return gr.update(visible=(mode == "gmass"))
            
            # Function to update attachment stats based on new mode
            def update_attachment_stats_new_mode(mode, attachment_format):
                if mode == "Attachment":
                    if attachment_format == "pdf":
                        return update_attachment_stats(True, False)
                    else:  # image
                        return update_attachment_stats(False, True)
                else:  # Invoice mode
                    return "Invoice mode: Personalized invoices will be generated"
            
            # Function to validate accounts and show selection table
            def validate_and_show_selection(auth_file, auth_method):
                """Validate uploaded accounts and show selection table"""
                if not auth_file:
                    return (
                        gr.update(visible=False),  # Hide selection section
                        [["No file uploaded", "❌ Pending", False]],
                        "Upload accounts to see selection options"
                    )
                
                try:
                    if auth_method == "App Password":
                        # Validate accounts file
                        from mailer import parse_file_lines, validate_accounts_file
                        
                        accounts_lines = parse_file_lines(auth_file)
                        acc_valid, acc_msg, valid_accounts = validate_accounts_file(accounts_lines)
                        
                        if not acc_valid:
                            return (
                                gr.update(visible=False),
                                [["Validation failed", "❌ Error", False]],
                                f"Error: {acc_msg}"
                            )
                        
                        # Create selection table with working accounts
                        validated_accounts = [{"email": acc["email"], "status": "Working"} for acc in valid_accounts]
                        
                        from ui_token_helpers import create_selection_table_from_validation
                        validation_results = {"working": [{"email": acc["email"]} for acc in valid_accounts]}
                        table_data = create_selection_table_from_validation(validation_results)
                        
                        selection_msg = f"✅ {len(valid_accounts)} accounts validated. Select which ones to use:"
                        
                        return (
                            gr.update(visible=True),  # Show selection section
                            table_data,
                            selection_msg
                        )
                    
                    else:  # Gmail API
                        # Validate token files
                        from ui_token_helpers import get_authenticated_gmail_accounts
                        
                        gmail_accounts = get_authenticated_gmail_accounts()
                        
                        if not gmail_accounts:
                            return (
                                gr.update(visible=False),
                                [["No Gmail accounts found", "❌ Error", False]],
                                "No authenticated Gmail accounts found in tokens"
                            )
                        
                        # Create selection table for Gmail accounts
                        table_data = []
                        for email in gmail_accounts:
                            table_data.append([email, "Working", True])  # All selected by default
                        
                        selection_msg = f"✅ {len(gmail_accounts)} Gmail accounts authenticated. Select which ones to use:"
                        
                        return (
                            gr.update(visible=True),  # Show selection section
                            table_data,
                            selection_msg
                        )
                        
                except Exception as e:
                    return (
                        gr.update(visible=False),
                        [["Error during validation", "❌ Error", False]],
                        f"Validation error: {str(e)}"
                    )
            
            # Function to handle sending with account selection
            def send_with_selection(auth_file, auth_method, leads_file, leads_per_account, num_accounts_to_use, mode,
                                  subjects_text, bodies_text, gmass_recipients_text, email_content_mode, attachment_format,
                                  invoice_format, support_number, sender_name_type, selection_table_data):
                """Handle sending with selected accounts only"""
                
                if not selection_table_data:
                    return ("No accounts selected", "", "", "", "Selection Error", [["Error", "No accounts selected"]])
                
                # Extract selected emails from table data
                selected_emails = []
                for row in selection_table_data:
                    if len(row) >= 3 and row[2]:  # Check if checkbox is True
                        selected_emails.append(row[0])
                
                if not selected_emails:
                    return ("No accounts selected", "", "", "", "Selection Error", [["Error", "No accounts selected"]])
                
                # Use the selection-aware send handler
                from ui_token_helpers import unified_send_handler_with_selection
                
                return unified_send_handler_with_selection(
                    auth_file, auth_method, leads_file, leads_per_account, len(selected_emails), mode,
                    subjects_text, bodies_text, gmass_recipients_text, email_content_mode, attachment_format,
                    invoice_format, support_number, sender_name_type, selected_emails
                )
            
            # Authentication method change handler
            auth_method.change(
                fn=toggle_auth_method_ui,
                inputs=[auth_method],
                outputs=[auth_file, app_pass_instructions, gmail_api_section, auth_file_stats]
            )
            
            # File change handlers
            auth_file.change(
                fn=analyze_auth_file,
                inputs=[auth_file, auth_method],
                outputs=[auth_file_stats]
            )
            leads_file.change(
                fn=lambda leads_file: update_file_stats(None, leads_file)[1],  # Return only leads stats
                inputs=[leads_file],
                outputs=[leads_stats]
            )
            
            # New handlers for streamlined mode
            email_content_mode.change(toggle_content_groups, inputs=[email_content_mode], outputs=[attachment_group, invoice_group])
            email_content_mode.change(update_attachment_stats_new_mode, inputs=[email_content_mode, attachment_format], outputs=[attachment_stats])
            attachment_format.change(update_attachment_stats_new_mode, inputs=[email_content_mode, attachment_format], outputs=[attachment_stats])
            
            # Handler to toggle GMass preview based on mode selection
            mode.change(toggle_gmass_preview, inputs=[mode], outputs=[gmass_preview_group])
            
            # Gmail token status handlers
            # Update token status when auth file changes in Gmail API mode
            auth_file.change(
                fn=update_gmail_api_status,
                inputs=[auth_file, auth_method],
                outputs=[auth_status_table]
            )
            
            # SMTP Selection handlers - Show selection table after validation
            auth_file.change(
                fn=validate_and_show_selection,
                inputs=[auth_file, auth_method],
                outputs=[smtp_selection_section, smtp_selection_table, selection_status]
            )
            
            # Also update selection when auth method changes
            auth_method.change(
                fn=validate_and_show_selection,
                inputs=[auth_file, auth_method],
                outputs=[smtp_selection_section, smtp_selection_table, selection_status]
            )
            
            # Use the new send handler with account selection
            start_btn.click(
                send_with_selection,
                inputs=[auth_file, auth_method, leads_file, leads_per_account, num_accounts_to_use, mode, 
                       subjects_text, bodies_text, gmass_recipients_text, email_content_mode, attachment_format, invoice_format,
                       support_number, sender_name_type, smtp_selection_table],
                outputs=[log_box, progress_html, account_errors_display, error_summary, gmass_status, gmass_urls_display]
            )
    
    return demo

def main():
    """Main entry point for console script."""
    app = gradio_ui()
    app.launch(
        share=True,
        server_name="0.0.0.0", 
        server_port=7863,
        debug=False
    )

if __name__ == "__main__":
    main()