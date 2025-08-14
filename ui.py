import gradio as gr
from mailer import main_worker, update_file_stats, update_attachment_stats
from content import DEFAULT_SUBJECTS, DEFAULT_BODIES, DEFAULT_GMASS_RECIPIENTS, SENDER_NAME_TYPES, DEFAULT_SENDER_NAME_TYPE
from gmass_scraper import run_gmass_test_with_urls_only, fetch_gmass_scores_only, start_real_send_with_selected_smtps
from gmail_auth_ui import update_auth_status_from_accounts, authenticate_single_account, get_credential_summary, create_gmail_auth_interface

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
            
            with gr.Row():
                support_number = gr.Textbox(label="Support Phone Numbers (one per line)", value="", placeholder="e.g. 123-456-7890\n098-765-4321", lines=2)
                attachment_format = gr.Radio(["pdf", "image", "heic"], value="pdf", label="Attachment Format")
            
            with gr.Row():
                include_pdfs = gr.Checkbox(label="📄 Include PDF attachments", value=True)
                include_images = gr.Checkbox(label="🖼️ Include Image attachments", value=True)
                attachment_stats = gr.HTML(label="Attachment Statistics")
            
            with gr.Row():
                leads_per_account = gr.Number(label="Leads to Send Per Account", value=10, precision=0)
                num_accounts_to_use = gr.Slider(minimum=1, maximum=50, value=1, step=1, label="Number of Concurrent Accounts to Use")
            
            mode = gr.Radio(["leads", "gmass"], value="leads", label="Mode", info="Leads Distribution: split leads across accounts. GMass Broadcast: every account sends to all recipients.")
            
            with gr.Group():
                gr.Markdown("""### 📊 GMass Deliverability Testing (2-Stage Workflow)
                **Stage 1:** Send test emails → Get URLs for manual checking  
                **Stage 2:** Optional automated scraping (click 'Get Scores' only if desired)""")
                scrape_gmass_scores = gr.Checkbox(label="Auto-scrape GMass scores", value=True, visible=False)
                
                with gr.Row():
                    gmass_test_btn = gr.Button("🧪 Send Test Emails to GMass", variant="secondary")
                    get_scores_btn = gr.Button("📊 Get Scores (Optional Playwright Scraping)", variant="secondary")
                    real_send_btn = gr.Button("🚀 Start Real Send with Selected SMTPs", variant="primary")
                
                gmass_status = gr.HTML(label="GMass Test Status", value="")
                gmass_results_table = gr.HTML(label="Deliverability Results", value="<p>No results yet. Run GMass test first.</p>")
            
            start_btn = gr.Button("📧 Start Sending (Legacy)", variant="secondary")
            
            with gr.Row():
                progress_html = gr.HTML(label="Progress", value="")
                log_box = gr.HTML(label="Log", value="")
            
            with gr.Row():
                account_errors_display = gr.HTML(label="Account Errors", value="No errors yet")
                error_summary = gr.HTML(label="Error Summary")
            
            # File change handlers
            accounts_file.change(update_file_stats, inputs=[accounts_file, leads_file], outputs=[accounts_stats, leads_stats])
            leads_file.change(update_file_stats, inputs=[accounts_file, leads_file], outputs=[accounts_stats, leads_stats])
            include_pdfs.change(update_attachment_stats, inputs=[include_pdfs, include_images], outputs=attachment_stats)
            include_images.change(update_attachment_stats, inputs=[include_pdfs, include_images], outputs=attachment_stats)
            
            # Gmail authentication handlers (NEW INTERFACE!)
            # Update auth status when accounts file changes
            def update_auth_display_with_new_interface(acc_file):
                return update_auth_status_from_accounts(acc_file, gmail_auth_components['credential_files'])
            
            accounts_file.change(
                fn=update_auth_display_with_new_interface,
                inputs=[accounts_file],
                outputs=[gmail_auth_components['auth_status_display']]
            )
            
            def update_gmass_visibility(mode_value):
                return gr.update(value=mode_value == "gmass")
            
            mode.change(update_gmass_visibility, inputs=[mode], outputs=[scrape_gmass_scores])
            
            gmass_test_btn.click(
                run_gmass_test_with_urls_only,
                inputs=[accounts_file, mode, subjects_text, bodies_text, gmass_recipients_text, 
                       include_pdfs, include_images, support_number, attachment_format, 
                       use_gmail_api, gmail_auth_components['credential_files'], sender_name_type],
                outputs=[gmass_status, gmass_results_table]
            )
            
            get_scores_btn.click(
                fetch_gmass_scores_only,
                inputs=[accounts_file],
                outputs=[gmass_status, gmass_results_table]
            )
            
            real_send_btn.click(
                start_real_send_with_selected_smtps,
                inputs=[accounts_file, leads_file, leads_per_account, subjects_text, bodies_text, 
                       include_pdfs, include_images, support_number, attachment_format, 
                       use_gmail_api, gmail_auth_components['credential_files'], sender_name_type],
                outputs=[log_box, progress_html, account_errors_display, error_summary]
            )
            
            start_btn.click(
                main_worker,
                inputs=[accounts_file, leads_file, leads_per_account, num_accounts_to_use, mode, 
                       subjects_text, bodies_text, gmass_recipients_text, include_pdfs, include_images, 
                       support_number, attachment_format, use_gmail_api, gmail_auth_components['credential_files'], sender_name_type],
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