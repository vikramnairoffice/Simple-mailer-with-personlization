import time
import os
import re
import tempfile
from datetime import datetime
import urllib.parse
from mailer import main_worker, parse_file_lines, validate_accounts_file

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    print("Playwright not available. Install with: pip install playwright")
    PLAYWRIGHT_AVAILABLE = False

# Global variable to store GMass results
gmass_results = {}
selected_accounts_for_real_send = []

def generate_gmass_urls(sender_emails):
    """Generate GMass URLs for sender emails without scraping"""
    if not sender_emails:
        return {}
    
    urls = {}
    for email in sender_emails:
        if '@' not in email:
            raise ValueError(f"Invalid email format: {email}")
        
        # Extract username part before @ for GMass URL
        username = email.split('@')[0]
        encoded_username = urllib.parse.quote(username)
        url = f"https://www.gmass.co/inbox?q={encoded_username}"
        urls[email] = url
    
    return urls

def format_gmass_urls_display(urls):
    """Format GMass URLs as clickable HTML display"""
    if not urls:
        return "<p>No URLs to display</p>"
    
    html = """
    <div style='background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;'>
        <h4>📊 GMass URLs Generated</h4>
        <p>Check deliverability manually or click 'Get Scores' to fetch automatically:</p>
        <table style='width:100%; border-collapse: collapse; font-family: monospace;'>
            <thead>
                <tr style='background: #e9ecef;'>
                    <th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>Sender Account</th>
                    <th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>GMass URL</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for email, url in urls.items():
        html += f"""
        <tr>
            <td style='border: 1px solid #ddd; padding: 8px;'>{email}</td>
            <td style='border: 1px solid #ddd; padding: 8px;'>
                <a href='{url}' target='_blank' style='color: #0066cc; text-decoration: none;'>{url}</a>
            </td>
        </tr>
        """
    
    html += """
            </tbody>
        </table>
        <p style='margin-top: 10px; color: #6c757d; font-size: 0.9em;'>
            💡 <strong>Options:</strong><br>
            • Check URLs manually by clicking the links above, OR<br>
            • Wait 2-3 minutes for emails to process, then click 'Get Scores' for automatic Playwright scraping<br>
            • Scraping is completely optional - you can proceed without it
        </p>
    </div>
    """
    
    return html

def fetch_gmass_scores(sender_emails):
    """Scrape GMass deliverability scores for multiple senders"""
    if not PLAYWRIGHT_AVAILABLE:
        return {email: {"error": "Playwright not available"} for email in sender_emails}
    
    results = {}
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            for email in sender_emails:
                try:
                    # Extract username part before @ for GMass URL
                    username = email.split('@')[0]
                    encoded_username = urllib.parse.quote(username)
                    url = f"https://www.gmass.co/inbox?q={encoded_username}"
                    
                    page.goto(url, wait_until='domcontentloaded', timeout=15000)
                    time.sleep(2)  # Wait for dynamic content
                    
                    # Try to find actual deliverability data using proper selectors
                    inbox_count = promotions_count = spam_count = 0
                    
                    try:
                        # Wait for potential data to load
                        page.wait_for_timeout(3000)
                        
                        # Look for specific deliverability data containers/elements
                        # These selectors need to be updated based on actual GMass page structure
                        deliverability_elements = page.query_selector_all('[data-placement], .placement-result, .inbox-count, .promotions-count, .spam-count')
                        
                        if deliverability_elements:
                            # Found structured deliverability data
                            for element in deliverability_elements:
                                text = element.text_content().lower() if element.text_content() else ""
                                if 'inbox' in text and any(c.isdigit() for c in text):
                                    numbers = re.findall(r'\d+', text)
                                    if numbers:
                                        inbox_count = int(numbers[0])
                                elif 'promotion' in text and any(c.isdigit() for c in text):
                                    numbers = re.findall(r'\d+', text)
                                    if numbers:
                                        promotions_count = int(numbers[0])
                                elif 'spam' in text and any(c.isdigit() for c in text):
                                    numbers = re.findall(r'\d+', text)
                                    if numbers:
                                        spam_count = int(numbers[0])
                        else:
                            # Fallback: Check if page shows "no results" or similar  
                            page_text = page.content().lower()
                            if any(phrase in page_text for phrase in ['no results', 'no data', 'not found', '0 results']):
                                # Legitimate case of no deliverability data
                                inbox_count = promotions_count = spam_count = 0
                            else:
                                # Page loaded but no recognizable deliverability data structure
                                # This suggests either page structure changed or no real data
                                raise Exception("No deliverability data structure found on page")
                                
                    except Exception as selector_error:
                        # If structured approach fails, return zero scores with error info
                        inbox_count = promotions_count = spam_count = 0
                        print(f"Warning: Could not extract deliverability data for {email}: {selector_error}")
                    
                    # Calculate simple score
                    score = inbox_count + (0.6 * promotions_count)
                    
                    results[email] = {
                        "sender": email,
                        "inbox": inbox_count,
                        "promotions": promotions_count,
                        "spam": spam_count,
                        "score": round(score, 1),
                        "link": url,
                        "ts": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    
                except Exception as e:
                    results[email] = {
                        "sender": email,
                        "inbox": 0,
                        "promotions": 0,
                        "spam": 0,
                        "score": 0,
                        "link": f"https://www.gmass.co/inbox?q={urllib.parse.quote(email.split('@')[0])}",
                        "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "error": str(e)
                    }
            
            browser.close()
    
    except Exception as e:
        for email in sender_emails:
            results[email] = {
                "sender": email,
                "inbox": 0,
                "promotions": 0, 
                "spam": 0,
                "score": 0,
                "link": f"https://www.gmass.co/inbox?q={urllib.parse.quote(email.split('@')[0])}",
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "error": f"Browser error: {e}"
            }
    
    return results

def format_gmass_results_table(results):
    """Format GMass results as HTML table with checkboxes"""
    if not results:
        return "<p>No results to display</p>"
    
    html = """
    <table style='width:100%; border-collapse: collapse; font-family: monospace;'>
        <thead>
            <tr style='background: #f0f0f0;'>
                <th style='border: 1px solid #ddd; padding: 8px;'>Select</th>
                <th style='border: 1px solid #ddd; padding: 8px;'>Sender</th>
                <th style='border: 1px solid #ddd; padding: 8px;'>Inbox</th>
                <th style='border: 1px solid #ddd; padding: 8px;'>Promotions</th>
                <th style='border: 1px solid #ddd; padding: 8px;'>Spam</th>
                <th style='border: 1px solid #ddd; padding: 8px;'>Score</th>
                <th style='border: 1px solid #ddd; padding: 8px;'>Last Updated</th>
                <th style='border: 1px solid #ddd; padding: 8px;'>GMass Link</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for email, data in results.items():
        # Pre-check if inbox >= 1
        checked = "checked" if data.get("inbox", 0) >= 1 else ""
        error_info = f" (Error: {data.get('error', '')})" if data.get('error') else ""
        
        html += f"""
        <tr>
            <td style='border: 1px solid #ddd; padding: 8px; text-align: center;'>
                <input type='checkbox' id='smtp_{email}' {checked}>
            </td>
            <td style='border: 1px solid #ddd; padding: 8px;'>{email}{error_info}</td>
            <td style='border: 1px solid #ddd; padding: 8px; text-align: center;'>{data.get('inbox', 0)}</td>
            <td style='border: 1px solid #ddd; padding: 8px; text-align: center;'>{data.get('promotions', 0)}</td>
            <td style='border: 1px solid #ddd; padding: 8px; text-align: center;'>{data.get('spam', 0)}</td>
            <td style='border: 1px solid #ddd; padding: 8px; text-align: center;'>{data.get('score', 0)}</td>
            <td style='border: 1px solid #ddd; padding: 8px;'>{data.get('ts', 'N/A')}</td>
            <td style='border: 1px solid #ddd; padding: 8px;'>
                <a href='{data.get('link', '#')}' target='_blank'>View</a>
            </td>
        </tr>
        """
    
    html += """
        </tbody>
    </table>
    <script>
        // Allow selecting/deselecting all
        function selectAllSmtps(checked) {
            document.querySelectorAll('input[id^="smtp_"]').forEach(cb => cb.checked = checked);
        }
    </script>
    <p style='margin-top: 10px;'>
        <button onclick='selectAllSmtps(true)'>Select All</button>
        <button onclick='selectAllSmtps(false)'>Deselect All</button>
    </p>
    """
    
    return html

def run_gmass_test_with_urls_only(accounts_file, mode, subjects_text, bodies_text, gmass_recipients_text, 
                                include_pdfs, include_images, support_number, attachment_format, 
                                use_gmail_api, gmail_credentials_files, sender_name_type="business"):
    """Stage 1: Send GMass test emails and return URLs only (no Playwright scraping)"""
    if mode != "gmass":
        return "❌ Please set mode to 'gmass' for deliverability testing", ""
    
    if not accounts_file:
        return "❌ Please upload accounts file first", ""
    
    # Parse accounts
    accounts_lines = parse_file_lines(accounts_file)
    acc_valid, acc_msg, valid_accounts = validate_accounts_file(accounts_lines)
    
    if not acc_valid:
        return f"❌ Accounts file error: {acc_msg}", ""
    
    # Run the GMass test (sending emails)
    try:
        # Get sender emails for URL generation
        sender_emails = [acc['email'] for acc in valid_accounts]
        
        # Use existing main_worker - ensure each SMTP sends to ALL GMass recipients
        results_generator = main_worker(
            accounts_file, None, len(gmass_recipients_text.strip().split('\n')), len(valid_accounts), "gmass", 
            subjects_text, bodies_text, gmass_recipients_text,
            include_pdfs, include_images, support_number, attachment_format,
            use_gmail_api, gmail_credentials_files, sender_name_type
        )
        
        # Wait for completion
        final_log = ""
        for log_html, progress_html, errors_html, summary_html in results_generator:
            final_log = log_html
            if "All tasks complete" in log_html:
                break
        
        # Generate URLs immediately (no Playwright scraping)
        gmass_urls = generate_gmass_urls(sender_emails)
        urls_display = format_gmass_urls_display(gmass_urls)
        
        status_message = f"✅ GMass test emails sent successfully! URLs generated for {len(sender_emails)} accounts."
        
        return status_message, urls_display
        
    except Exception as e:
        return f"❌ Error during GMass test: {e}", ""

def fetch_gmass_scores_only(accounts_file):
    """Fetch GMass scores only (separate from sending)"""
    global gmass_results
    
    if not accounts_file:
        return "❌ Please upload accounts file first", ""
    
    # Parse accounts
    accounts_lines = parse_file_lines(accounts_file)
    acc_valid, acc_msg, valid_accounts = validate_accounts_file(accounts_lines)
    
    if not acc_valid:
        return f"❌ Accounts file error: {acc_msg}", ""
    
    try:
        # Fetch GMass scores
        sender_emails = [acc['email'] for acc in valid_accounts]
        gmass_results = fetch_gmass_scores(sender_emails)
        
        # Format results table
        results_table = format_gmass_results_table(gmass_results)
        
        return "✅ GMass scores fetched successfully.", results_table
        
    except Exception as e:
        return f"❌ Error fetching GMass scores: {e}", ""

def start_real_send_with_selected_smtps(accounts_file, leads_file, leads_per_account, 
                                      subjects_text, bodies_text, include_pdfs, include_images, 
                                      support_number, attachment_format, use_gmail_api, gmail_credentials_files, sender_name_type="business"):
    """Start real send with only selected SMTPs from GMass results"""
    global gmass_results, selected_accounts_for_real_send
    
    if not gmass_results:
        return "❌ Please run GMass test first", "", "", ""
    
    if not accounts_file or not leads_file:
        return "❌ Please upload both accounts and leads files", "", "", ""
    
    # Parse accounts and filter by selected checkboxes
    accounts_lines = parse_file_lines(accounts_file)
    acc_valid, acc_msg, valid_accounts = validate_accounts_file(accounts_lines)
    
    if not acc_valid:
        return f"❌ Accounts file error: {acc_msg}", "", "", ""
    
    # Filter accounts based on GMass results (simulate checkbox selection by using inbox >= 1)
    selected_accounts_for_real_send = [
        acc for acc in valid_accounts 
        if acc['email'] in gmass_results and gmass_results[acc['email']].get('inbox', 0) >= 1
    ]
    
    if not selected_accounts_for_real_send:
        return "❌ No SMTPs selected or no SMTPs with good deliverability", "", "", ""
    
    # Create a temporary accounts file with only selected accounts
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
        for acc in selected_accounts_for_real_send:
            temp_file.write(f"{acc['email']},{acc['password']}\n")
        temp_accounts_path = temp_file.name
    
    # Use existing main_worker with filtered accounts
    try:
        # Create a mock file object for the filtered accounts
        class MockFile:
            def __init__(self, path):
                self.name = path
        
        filtered_accounts_file = MockFile(temp_accounts_path)
        
        results_generator = main_worker(
            filtered_accounts_file, leads_file, leads_per_account, len(selected_accounts_for_real_send), 
            "leads", subjects_text, bodies_text, "", include_pdfs, include_images, 
            support_number, attachment_format, use_gmail_api, gmail_credentials_files, sender_name_type
        )
        
        # Return the generator for real-time updates
        for result in results_generator:
            yield result
            
    except Exception as e:
        yield f"❌ Error during real send: {e}", "", "", ""
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_accounts_path)
        except:
            pass