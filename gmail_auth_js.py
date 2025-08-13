"""
JavaScript integration for Gmail authentication UI
Handles interactive buttons and dynamic authentication triggers
"""

import gradio as gr

def create_auth_javascript():
    """Create JavaScript for interactive authentication buttons"""
    js_code = """
    function() {
        // Add event listeners for authentication buttons
        const authButtons = document.querySelectorAll('.auth-button');
        const reauthButtons = document.querySelectorAll('.reauth-button');
        
        // Function to trigger authentication
        function triggerAuth(email, credKey) {
            // Find hidden Gradio components
            const emailInput = document.querySelector('input[data-testid*="auth_account_email"]') || 
                              document.querySelector('#component-* input[placeholder*="Account"]') ||
                              gradio_app.querySelector('[data-label="Account to Authenticate"] input');
            const credInput = document.querySelector('input[data-testid*="auth_credential_key"]') ||
                             document.querySelector('#component-* input[placeholder*="Credential"]') ||
                             gradio_app.querySelector('[data-label="Credential Key"] input');
            const triggerBtn = document.querySelector('button[data-testid*="auth_trigger"]') ||
                              document.querySelector('#component-* button') ||
                              gradio_app.querySelector('[data-label*="Authenticate Account"]');
            
            console.log('Triggering auth for:', email, credKey);
            console.log('Found inputs:', !!emailInput, !!credInput, !!triggerBtn);
            
            if (emailInput && credInput && triggerBtn) {
                // Set values
                emailInput.value = email;
                credInput.value = credKey;
                
                // Trigger change events
                emailInput.dispatchEvent(new Event('input', { bubbles: true }));
                credInput.dispatchEvent(new Event('input', { bubbles: true }));
                
                // Click trigger button
                setTimeout(() => {
                    triggerBtn.click();
                }, 100);
            } else {
                alert('Authentication system not ready. Please try manual authentication below.');
            }
        }
        
        // Set up button click handlers
        authButtons.forEach(button => {
            if (!button.hasAttribute('data-auth-setup')) {
                button.setAttribute('data-auth-setup', 'true');
                button.addEventListener('click', function(e) {
                    e.preventDefault();
                    const onclick = this.getAttribute('onclick');
                    if (onclick) {
                        // Extract email and credential from onclick attribute
                        const matches = onclick.match(/auth_account\\('([^']*)',\\s*'([^']*)'\\)/);
                        if (matches) {
                            triggerAuth(matches[1], matches[2]);
                        }
                    }
                });
            }
        });
        
        reauthButtons.forEach(button => {
            if (!button.hasAttribute('data-reauth-setup')) {
                button.setAttribute('data-reauth-setup', 'true');
                button.addEventListener('click', function(e) {
                    e.preventDefault();
                    const onclick = this.getAttribute('onclick');
                    if (onclick) {
                        // Extract email and credential from onclick attribute
                        const matches = onclick.match(/reauth_account\\('([^']*)',\\s*'([^']*)'\\)/);
                        if (matches) {
                            triggerAuth(matches[1], matches[2]);
                        }
                    }
                });
            }
        });
        
        // Also set up credential selector change handlers
        const credSelects = document.querySelectorAll('.credential-select');
        credSelects.forEach(select => {
            if (!select.hasAttribute('data-cred-setup')) {
                select.setAttribute('data-cred-setup', 'true');
                select.addEventListener('change', function() {
                    // This would trigger a refresh of the auth status table
                    // For now, just log the change
                    console.log('Credential changed for:', this.id, 'to:', this.value);
                });
            }
        });
        
        console.log('Gmail auth JavaScript setup complete');
        return 'JavaScript initialized';
    }
    """
    return js_code

def create_auth_refresh_component():
    """Create a component to refresh authentication JavaScript bindings"""
    with gr.Row(visible=False):
        js_trigger = gr.Button("Refresh JS", elem_id="auth_js_trigger")
        js_output = gr.Textbox(label="JS Status", elem_id="auth_js_status")
        
        js_trigger.click(
            fn=None,
            inputs=[],
            outputs=[js_output],
            js=create_auth_javascript()
        )
        
        return js_trigger, js_output

def add_auth_javascript_to_interface():
    """Add JavaScript integration to the Gradio interface"""
    # This function can be called to add JS functionality
    # The actual integration happens through the HTML components
    return {
        'js_code': create_auth_javascript(),
        'refresh_component': create_auth_refresh_component
    }