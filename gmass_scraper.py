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
                    encoded_email = urllib.parse.quote(email)
                    url = f"https://www.gmass.co/inbox?q={encoded_email}"
                    
                    page.goto(url, wait_until='domcontentloaded', timeout=15000)
                    time.sleep(2)  # Wait for dynamic content
                    
                    # Try multiple selectors to find placement badges
                    inbox_count = promotions_count = spam_count = 0
                    
                    # Look for text content containing placement info
                    page_content = page.content().lower()
                    
                    # Simple text parsing approach
                    if 'inbox' in page_content:
                        inbox_matches = re.findall(r'inbox.*?(\d+)', page_content)
                        if inbox_matches:
                            inbox_count = int(inbox_matches[0])
                    
                    if 'promotions' in page_content:
                        promo_matches = re.findall(r'promotions.*?(\d+)', page_content)
                        if promo_matches:
                            promotions_count = int(promo_matches[0])
                    
                    if 'spam' in page_content:
                        spam_matches = re.findall(r'spam.*?(\d+)', page_content)
                        if spam_matches:
                            spam_count = int(spam_matches[0])
                    
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
                        "link": f"https://www.gmass.co/inbox?q={urllib.parse.quote(email)}",
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
                "link": f"https://www.gmass.co/inbox?q={urllib.parse.quote(email)}",
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

def run_gmass_test_and_fetch_scores(accounts_file, mode, subjects_text, bodies_text, gmass_recipients_text, 
                                   include_pdfs, include_images, support_number, attachment_format, 
                                   use_gmail_api, gmail_credentials_files, sender_name_type="business"):
    """Run GMass test and fetch deliverability scores"""
    global gmass_results
    
    if mode != "gmass":
        return "❌ Please set mode to 'gmass' for deliverability testing", ""
    
    if not accounts_file:
        return "❌ Please upload accounts file first", ""
    
    # Parse accounts
    accounts_lines = parse_file_lines(accounts_file)
    acc_valid, acc_msg, valid_accounts = validate_accounts_file(accounts_lines)
    
    if not acc_valid:
        return f"❌ Accounts file error: {acc_msg}", ""
    
    # Run the GMass test (existing logic)
    try:
        # Use existing main_worker but limit to small test
        results_generator = main_worker(
            accounts_file, None, 15, len(valid_accounts), "gmass", 
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
        
        # Wait a bit for emails to be processed by GMass
        time.sleep(10)
        
        # Fetch GMass scores
        sender_emails = [acc['email'] for acc in valid_accounts]
        gmass_results = fetch_gmass_scores(sender_emails)
        
        # Format results table
        results_table = format_gmass_results_table(gmass_results)
        
        return f"✅ GMass test completed. Deliverability scores fetched.\n{final_log}", results_table
        
    except Exception as e:
        return f"❌ Error during GMass test: {e}", ""

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