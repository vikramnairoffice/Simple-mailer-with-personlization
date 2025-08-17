import gradio as gr
from mailer import main_worker_new_mode, update_file_stats, update_attachment_stats
from content import DEFAULT_SUBJECTS, DEFAULT_BODIES, DEFAULT_GMASS_RECIPIENTS, SENDER_NAME_TYPES, DEFAULT_SENDER_NAME_TYPE
from gmail_auth_ui import update_auth_status_from_accounts, authenticate_single_account, get_credential_summary, create_gmail_auth_interface
import urllib.parse
from mailer import parse_file_lines, validate_accounts_file, convert_mode_to_attachment_flags, main_worker

def send_gmass_test_simple(accounts_file, mode, subjects_text, bodies_text, gmass_recipients_text, 
                          email_content_mode, attachment_format, invoice_format, support_number, 
                          use_gmail_api, gmail_credentials_files, sender_name_type="business"):
    """Simple GMass test that sends emails and displays URLs in plain text format"""
    if mode != "gmass":
        return "❌ Please set mode to 'gmass' for deliverability testing", ""
    
    if not accounts_file:
        return "❌ Please upload accounts file first", ""
    
    # Parse accounts
    accounts_lines = parse_file_lines(accounts_file)
    acc_valid, acc_msg, valid_accounts = validate_accounts_file(accounts_lines)
    
    if not acc_valid:
        return f"❌ Accounts file error: {acc_msg}", ""
    
    try:
        # Convert new mode to old format
        include_pdfs, include_images = convert_mode_to_attachment_flags(email_content_mode, attachment_format)
        
        # For invoice mode, use invoice_format instead of attachment_format
        actual_attachment_format = invoice_format if email_content_mode == "Invoice" else attachment_format
        
        # Get sender emails for URL generation
        sender_emails = [acc['email'] for acc in valid_accounts]
        
        # Use existing main_worker - ensure each SMTP sends to ALL GMass recipients
        results_generator = main_worker(
            accounts_file, None, len(gmass_recipients_text.strip().split('\n')), len(valid_accounts), "gmass", 
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
        
        # Generate URLs for manual checking
        urls_text = "GMass URLs for manual deliverability checking:\n\n"
        for email in sender_emails:
            if '@' in email:
                username = email.split('@')[0]
                encoded_username = urllib.parse.quote(username)
                url = f"https://www.gmass.co/inbox?q={encoded_username}"
                urls_text += f"{email}: {url}\n"
        
        urls_text += "\n💡 Visit these URLs manually to check deliverability results."
        
        status_message = f"✅ GMass test emails sent successfully! URLs generated for {len(sender_emails)} accounts."
        
        return status_message, urls_text
        
    except Exception as e:
        return f"❌ Error during GMass test: {e}", ""

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
            with gr.Row():
                accounts_file = gr.File(label="Accounts File (txt/csv, format: email,password)")
                leads_file = gr.File(label="Leads File (txt/csv, one email per line)")
            
            with gr.Row():
                accounts_stats = gr.HTML(label="Accounts Statistics")
                leads_stats = gr.HTML(label="Leads Statistics")
            
            with gr.Row():
                use_gmail_api = gr.Checkbox(label="🔧 Use Gmail API for @gmail.com accounts", value=False)
            
            # Gmail Authentication Section (NEW IMPROVED INTERFACE!)
            gmail_auth_components = create_gmail_auth_interface()
            
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
            
            mode = gr.Radio(["leads", "gmass"], value="leads", label="Mode", info="Leads Distribution: split leads across accounts. GMass Broadcast: every account sends to all recipients.")
            
            with gr.Group():
                gr.Markdown("""### 📊 GMass URL Preview
                **Send test emails to GMass recipients and get URLs for manual checking**""")
                
                with gr.Row():
                    gmass_test_btn = gr.Button("🧪 Send Test Emails to GMass", variant="secondary")
                
                gmass_status = gr.Textbox(label="GMass Test Status", value="Ready to send test emails", interactive=False)
                gmass_urls_display = gr.Textbox(label="GMass URLs", value="URLs will appear here after sending test emails", interactive=False, lines=10)
            
            start_btn = gr.Button("📧 Start Sending (Legacy)", variant="secondary")
            
            with gr.Row():
                progress_html = gr.HTML(label="Progress", value="")
                log_box = gr.HTML(label="Log", value="")
            
            with gr.Row():
                account_errors_display = gr.HTML(label="Account Errors", value="No errors yet")
                error_summary = gr.HTML(label="Error Summary")
            
            # Function to toggle visibility based on email content mode
            def toggle_content_groups(mode):
                if mode == "Attachment":
                    return gr.update(visible=True), gr.update(visible=False)
                else:  # Invoice
                    return gr.update(visible=False), gr.update(visible=True)
            
            # Function to update attachment stats based on new mode
            def update_attachment_stats_new_mode(mode, attachment_format):
                if mode == "Attachment":
                    if attachment_format == "pdf":
                        return update_attachment_stats(True, False)
                    else:  # image
                        return update_attachment_stats(False, True)
                else:  # Invoice mode
                    return "Invoice mode: Personalized invoices will be generated"
            
            # File change handlers
            accounts_file.change(update_file_stats, inputs=[accounts_file, leads_file], outputs=[accounts_stats, leads_stats])
            leads_file.change(update_file_stats, inputs=[accounts_file, leads_file], outputs=[accounts_stats, leads_stats])
            
            # New handlers for streamlined mode
            email_content_mode.change(toggle_content_groups, inputs=[email_content_mode], outputs=[attachment_group, invoice_group])
            email_content_mode.change(update_attachment_stats_new_mode, inputs=[email_content_mode, attachment_format], outputs=[attachment_stats])
            attachment_format.change(update_attachment_stats_new_mode, inputs=[email_content_mode, attachment_format], outputs=[attachment_stats])
            
            # Gmail authentication handlers (NEW INTERFACE!)
            # Update auth status when accounts file changes
            def update_auth_display_with_new_interface(acc_file):
                return update_auth_status_from_accounts(acc_file, gmail_auth_components['credential_files'])
            
            accounts_file.change(
                fn=update_auth_display_with_new_interface,
                inputs=[accounts_file],
                outputs=[gmail_auth_components['auth_status_display']]
            )
            
            
            gmass_test_btn.click(
                send_gmass_test_simple,
                inputs=[accounts_file, mode, subjects_text, bodies_text, gmass_recipients_text, 
                       email_content_mode, attachment_format, invoice_format, support_number, 
                       use_gmail_api, gmail_auth_components['credential_files'], sender_name_type],
                outputs=[gmass_status, gmass_urls_display]
            )
            
            start_btn.click(
                main_worker_new_mode,
                inputs=[accounts_file, leads_file, leads_per_account, num_accounts_to_use, mode, 
                       subjects_text, bodies_text, gmass_recipients_text, email_content_mode, attachment_format, invoice_format,
                       support_number, use_gmail_api, gmail_auth_components['credential_files'], sender_name_type],
                outputs=[log_box, progress_html, account_errors_display, error_summary]
            )
    
    return demo

def main():
    """Main entry point for console script."""
    app = gradio_ui()
    app.launch(
        share=True,
        server_name="0.0.0.0", 
        server_port=7861,
        debug=False
    )

if __name__ == "__main__":
    main()