"""
Gmail Authentication UI Components
Provides Gradio interface for per-account Gmail OAuth2 authentication
"""

import gradio as gr
from gmail_auth_manager import gmail_auth_manager, is_colab_environment

def create_auth_status_html(gmail_accounts, auth_status, credential_options):
    """Create HTML table showing authentication status"""
    if not gmail_accounts or not credential_options:
        return "<p>ℹ️ No Gmail accounts found or no credential files loaded.</p>"
    
    html = """
    <style>
    .auth-table {
        border-collapse: collapse;
        width: 100%;
        margin: 10px 0;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .auth-table th {
        background-color: #4285f4;
        color: white;
        padding: 12px 8px;
        text-align: left;
        font-weight: 600;
    }
    .auth-table td {
        padding: 10px 8px;
        border-bottom: 1px solid #ddd;
        vertical-align: middle;
    }
    .auth-table tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    .auth-table tr:hover {
        background-color: #e3f2fd;
    }
    .status-authenticated {
        color: #4caf50;
        font-weight: 600;
    }
    .status-pending {
        color: #ff9800;
        font-weight: 600;
    }
    .status-failed {
        color: #f44336;
        font-weight: 600;
    }
    .auth-button {
        background: #4285f4;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        transition: background-color 0.3s;
    }
    .auth-button:hover {
        background: #3367d6;
    }
    .auth-button:disabled {
        background: #ccc;
        cursor: not-allowed;
    }
    .reauth-button {
        background: #ff9800;
        font-size: 11px;
        padding: 6px 12px;
    }
    .reauth-button:hover {
        background: #f57c00;
    }
    .credential-select {
        padding: 4px 8px;
        border: 1px solid #ddd;
        border-radius: 3px;
        font-size: 12px;
        max-width: 200px;
    }
    .account-email {
        font-weight: 600;
        color: #1976d2;
    }
    </style>
    
    <div style="margin: 15px 0;">
        <h4 style="color: #4285f4; margin-bottom: 10px;">📧 Gmail Authentication Status</h4>
        <table class="auth-table">
            <thead>
                <tr>
                    <th>Gmail Account</th>
                    <th>Credential File</th>
                    <th>Status</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for account in gmail_accounts:
        account_info = auth_status.get(account, {})
        default_cred = account_info.get('default_credential')
        credentials_info = account_info.get('credentials', {})
        
        if default_cred and default_cred in credentials_info:
            cred_info = credentials_info[default_cred]
            is_authenticated = cred_info['authenticated']
            cred_name = cred_info['credential_name']
            
            if is_authenticated:
                status_html = '<span class="status-authenticated">✅ Authenticated</span>'
                button_html = f'''<button class="auth-button reauth-button" 
                                    data-account="{account}" 
                                    data-credential="{default_cred}"
                                    onclick="triggerGradioAuth('{account}', '{default_cred}')">
                                    🔄 Re-auth
                                  </button>'''
            else:
                status_html = '<span class="status-pending">❌ Not Authenticated</span>'
                env_text = "Colab" if is_colab_environment() else "Incognito"
                button_html = f'''<button class="auth-button" 
                                    data-account="{account}" 
                                    data-credential="{default_cred}"
                                    onclick="triggerGradioAuth('{account}', '{default_cred}')">
                                    🌐 Auth ({env_text})
                                  </button>'''
            
            # Credential selector
            cred_select_html = f'<select class="credential-select" id="cred_{account}" onchange="update_credential(\'{account}\')">'
            for cred_key, cred_display in credential_options:
                selected = 'selected' if cred_key == default_cred else ''
                auth_indicator = '✅' if credentials_info.get(cred_key, {}).get('authenticated', False) else ''
                cred_select_html += f'<option value="{cred_key}" {selected}>{auth_indicator} {cred_display}</option>'
            cred_select_html += '</select>'
            
        else:
            status_html = '<span class="status-failed">⚠️ No Credentials</span>'
            button_html = '<span style="color: #999; font-size: 12px;">No credentials available</span>'
            cred_select_html = '<span style="color: #999; font-size: 12px;">None</span>'
        
        html += f"""
                <tr>
                    <td class="account-email">{account}</td>
                    <td>{cred_select_html}</td>
                    <td>{status_html}</td>
                    <td>{button_html}</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
    </div>
    
    <div style="margin-top: 15px; padding: 10px; background: #f0f8ff; border-left: 4px solid #4285f4; font-size: 13px;">
        <strong>💡 Instructions:</strong><br>
        • Upload credential JSON files first<br>
        • Select appropriate credential file for each account<br>
        • Click 🌐 Auth button to authenticate each account individually<br>
        • Authentication opens in incognito/private browser window<br>
        • Re-authenticate anytime using 🔄 Re-auth button
    </div>
    
    <script>
    function triggerGradioAuth(email, credKey) {
        console.log('Triggering authentication for:', email, credKey);
        
        // Find the hidden Gradio inputs by searching for specific patterns
        const inputs = document.querySelectorAll('input');
        const buttons = document.querySelectorAll('button');
        
        let emailInput = null;
        let credInput = null; 
        let triggerBtn = null;
        
        // Find inputs by their labels or nearby text
        inputs.forEach(input => {
            const label = input.parentElement?.querySelector('label')?.textContent || '';
            const container = input.closest('[data-testid]') || input.closest('.gr-form') || input.parentElement;
            const containerText = container?.textContent || '';
            
            if (label.includes('Account to Authenticate') || containerText.includes('Account to Authenticate')) {
                emailInput = input;
            }
            if (label.includes('Credential Key') || containerText.includes('Credential Key')) {
                credInput = input;
            }
        });
        
        // Find trigger button
        buttons.forEach(button => {
            const label = button.textContent || '';
            const container = button.closest('[data-testid]') || button.closest('.gr-form') || button.parentElement;
            const containerText = container?.textContent || '';
            
            if (label.includes('Authenticate Account') || containerText.includes('Authenticate Account')) {
                triggerBtn = button;
            }
        });
        
        console.log('Found elements:', !!emailInput, !!credInput, !!triggerBtn);
        
        if (emailInput && credInput && triggerBtn) {
            // Set values
            emailInput.value = email;
            credInput.value = credKey;
            
            // Trigger events to notify Gradio
            const inputEvent = new Event('input', { bubbles: true });
            const changeEvent = new Event('change', { bubbles: true });
            
            emailInput.dispatchEvent(inputEvent);
            emailInput.dispatchEvent(changeEvent);
            credInput.dispatchEvent(inputEvent);
            credInput.dispatchEvent(changeEvent);
            
            // Click trigger button after a short delay
            setTimeout(() => {
                triggerBtn.click();
                console.log('Authentication triggered');
            }, 200);
        } else {
            console.log('Could not find required elements, falling back to manual authentication');
            alert(`Please use manual authentication below for ${email}`);
        }
    }
    
    function update_credential(email) {
        console.log('Update credential for:', email);
        // This would refresh the authentication status
    }
    
    // Auto-setup when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Gmail Auth UI JavaScript loaded');
    });
    </script>
    """
    
    return html

def authenticate_single_account(account_email, credential_key, gmail_accounts_data, credential_files):
    """Authenticate a single Gmail account"""
    if not account_email or not credential_key:
        return "❌ Error: Missing account email or credential selection", ""
    
    try:
        # Load credentials if not already loaded
        if credential_files:
            gmail_auth_manager.load_credentials(credential_files)
        
        # Authenticate the account
        success, message = gmail_auth_manager.authenticate_account(account_email, credential_key)
        
        if success:
            status_msg = f"✅ Successfully authenticated {account_email}"
            
            # Update authentication status display
            gmail_accounts = gmail_auth_manager.get_gmail_accounts(gmail_accounts_data)
            auth_status = gmail_auth_manager.get_authentication_status(gmail_accounts)
            credential_options = gmail_auth_manager.credential_manager.get_credential_options()
            updated_html = create_auth_status_html(gmail_accounts, auth_status, credential_options)
            
            return status_msg, updated_html
        else:
            return f"❌ Authentication failed for {account_email}: {message}", ""
            
    except Exception as e:
        return f"❌ Error during authentication: {str(e)}", ""

def authenticate_quick_auth(credential_key, credential_files, gmail_accounts_data):
    """Quick authenticate with credential only - discovers email automatically"""
    if not credential_key:
        return "Error: Please select a credential file", ""
    
    try:
        # Load credentials if not already loaded
        if credential_files:
            gmail_auth_manager.load_credentials(credential_files)
        
        # Authenticate with credential only (discovers email automatically)
        success, message, discovered_email = gmail_auth_manager.authenticate_with_credential_only(credential_key)
        
        if success and discovered_email:
            status_msg = f"Successfully authenticated {discovered_email} using credential-only flow"
            
            # Update authentication status display
            gmail_accounts = gmail_auth_manager.get_gmail_accounts(gmail_accounts_data)
            auth_status = gmail_auth_manager.get_authentication_status(gmail_accounts)
            credential_options = gmail_auth_manager.credential_manager.get_credential_options()
            updated_html = create_auth_status_html(gmail_accounts, auth_status, credential_options)
            
            return status_msg, updated_html
        else:
            return f"Quick authentication failed: {message}", ""
            
    except Exception as e:
        return f"Error during quick authentication: {str(e)}", ""

def update_auth_status_display(gmail_accounts_data, credential_files):
    """Update the authentication status display"""
    if not credential_files:
        return "<p>⚠️ Please upload credential JSON files first.</p>"
    
    try:
        # Load credentials
        gmail_auth_manager.load_credentials(credential_files)
        
        # Get Gmail accounts and status
        gmail_accounts = gmail_auth_manager.get_gmail_accounts(gmail_accounts_data)
        if not gmail_accounts:
            return "<p>ℹ️ No Gmail accounts found in the uploaded accounts file.</p>"
        
        auth_status = gmail_auth_manager.get_authentication_status(gmail_accounts)
        credential_options = gmail_auth_manager.credential_manager.get_credential_options()
        
        return create_auth_status_html(gmail_accounts, auth_status, credential_options)
        
    except Exception as e:
        return f"<p>❌ Error updating authentication status: {str(e)}</p>"

def get_credential_summary(credential_files):
    """Get summary of uploaded credential files"""
    if not credential_files:
        return "<p>No credential files uploaded.</p>"
    
    try:
        gmail_auth_manager.credential_manager.load_credential_files(credential_files)
        credential_options = gmail_auth_manager.credential_manager.get_credential_options()
        
        if not credential_options:
            return "<p>⚠️ No valid credential files found.</p>"
        
        html = "<div style='margin: 10px 0;'><h4>📄 Uploaded Credential Files:</h4><ul>"
        for _, display_name in credential_options:
            html += f"<li>✅ {display_name}</li>"
        html += "</ul></div>"
        
        return html
        
    except Exception as e:
        return f"<p>❌ Error parsing credential files: {str(e)}</p>"

def create_gmail_auth_interface():
    """Create the Gmail authentication interface components"""
    with gr.Group():
        gr.Markdown("### 🔐 Gmail API Authentication")
        
        # Credential files upload
        credential_files_input = gr.File(
            label="📄 Gmail OAuth2 Credential JSON Files",
            file_count="multiple",
            file_types=[".json"],
            interactive=True
        )
        
        # Credential summary
        credential_summary = gr.HTML(
            label="Credential Files Status",
            value="<p>Upload credential JSON files to get started.</p>"
        )
        
        # Quick Authentication Section - SIMPLIFIED!
        with gr.Group():
            gr.Markdown("#### ⚡ Gmail Authentication")
            gr.Markdown("**Simple 2-step process:** Upload credential files → Select one → Authenticate (email auto-discovered)")
            
            with gr.Row():
                quick_auth_credential = gr.Dropdown(
                    label="🗂️ Select Credential File to Authenticate",
                    choices=[],
                    value=None,
                    interactive=True,
                    info="Choose which credential file to use - your email will be discovered automatically"
                )
                quick_auth_button = gr.Button(
                    "🚀 Authenticate (Incognito)", 
                    variant="primary",
                    size="lg"
                )
            
            quick_auth_result = gr.HTML(
                label="Authentication Result",
                value="<p style='color: #666; font-style: italic;'>Upload credential files above, then select one and click Authenticate.</p>"
            )
        
        # Authentication status table
        auth_status_display = gr.HTML(
            label="Authentication Status",
            value="<p>Upload accounts file and credential files to see authentication status.</p>"
        )
        
        # Keep minimal hidden inputs for JavaScript interaction (backward compatibility)
        with gr.Row(visible=False):
            auth_account_email = gr.Textbox(label="Account to Authenticate")
            auth_credential_key = gr.Textbox(label="Credential Key")
            auth_trigger = gr.Button("Authenticate Account")
        
        # Placeholder for auth_result (backward compatibility)
        auth_result = gr.HTML(label="Legacy Auth Result", value="", visible=False)
        
        # Update credential dropdown when files change
        def update_credential_dropdown(files):
            if not files:
                return gr.update(choices=[], value=None), "<p>Upload credential JSON files to get started.</p>"
            
            gmail_auth_manager.credential_manager.load_credential_files(files)
            options = gmail_auth_manager.credential_manager.get_credential_options()
            
            # Format choices correctly for dropdown: (display_name, key) pairs
            choices = [(display_name, key) for key, display_name in options]
            summary = get_credential_summary(files)
            
            print(f"DEBUG: Loaded {len(choices)} credential options: {choices}")  # Debug log
            
            return gr.update(choices=choices, value=choices[0][1] if choices else None), summary
        
        # Update displays when credential files change
        credential_files_input.change(
            fn=update_credential_dropdown,
            inputs=[credential_files_input],
            outputs=[quick_auth_credential, credential_summary]
        )
        
        # Quick authentication trigger
        quick_auth_button.click(
            fn=authenticate_quick_auth,
            inputs=[quick_auth_credential, credential_files_input, gr.State()],
            outputs=[quick_auth_result, auth_status_display]
        )
        
        
        # JavaScript-triggered authentication (for table buttons)
        auth_trigger.click(
            fn=authenticate_single_account,
            inputs=[auth_account_email, auth_credential_key, gr.State(), credential_files_input],
            outputs=[auth_result, auth_status_display]
        )
        
        return {
            'credential_files': credential_files_input,
            'auth_status_display': auth_status_display,
            'auth_result': auth_result,
            'auth_account_email': auth_account_email,
            'auth_credential_key': auth_credential_key,
            'auth_trigger': auth_trigger,
            'quick_auth_result': quick_auth_result,
            'quick_auth_credential': quick_auth_credential,
            'quick_auth_button': quick_auth_button
        }

def update_auth_status_from_accounts(accounts_file, credential_files):
    """Update authentication status when accounts file changes"""
    if not accounts_file or not credential_files:
        return "<p>⚠️ Please upload both accounts file and credential files.</p>"
    
    try:
        # Read accounts file
        if hasattr(accounts_file, 'name'):
            with open(accounts_file.name, 'rb') as f:
                accounts_data = f.read()
        else:
            accounts_data = accounts_file
        
        return update_auth_status_display(accounts_data, credential_files)
        
    except Exception as e:
        return f"<p>❌ Error reading accounts file: {str(e)}</p>"