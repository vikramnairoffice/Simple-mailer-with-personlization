import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from gmass_scraper import run_gmass_test_with_urls_only, fetch_gmass_scores_only, generate_gmass_urls
from content import DEFAULT_GMASS_RECIPIENTS

class TestGmass2Stage(unittest.TestCase):
    """Test 2-stage GMass workflow: Stage 1 (Send + URLs), Stage 2 (Get Scores)"""
    
    def setUp(self):
        """Set up test data"""
        self.test_accounts = [
            {"email": "test1@gmail.com", "password": "pass1"},
            {"email": "test2@yahoo.com", "password": "pass2"}
        ]
        self.gmass_recipients = DEFAULT_GMASS_RECIPIENTS[:3]
        
    def create_temp_accounts_file(self):
        """Create temporary accounts file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            for acc in self.test_accounts:
                f.write(f"{acc['email']},{acc['password']}\n")
            return f.name
    
    def test_stage1_sends_emails_and_returns_urls_only(self):
        """Test Stage 1: Send emails and return URLs without Playwright scraping"""
        accounts_file_path = self.create_temp_accounts_file()
        
        try:
            # Mock the sending function to avoid actual email sending
            with patch('gmass_scraper.main_worker') as mock_worker:
                # Mock successful sending
                mock_worker.return_value = iter([
                    ("✅ Sending started", "", "", ""),
                    ("📧 All tasks complete", "", "", "")
                ])
                
                class MockFile:
                    def __init__(self, path):
                        self.name = path
                
                accounts_file = MockFile(accounts_file_path)
                
                # Run Stage 1
                status_msg, urls_html = run_gmass_test_with_urls_only(
                    accounts_file=accounts_file,
                    mode="gmass",
                    subjects_text="Test Subject",
                    bodies_text="Test Body",
                    gmass_recipients_text="\n".join(self.gmass_recipients),
                    include_pdfs=False,
                    include_images=False,
                    support_number="",
                    attachment_format="pdf",
                    use_gmail_api=False,
                    gmail_credentials_files=None,
                    sender_name_type="business"
                )
                
                # Should return success message
                self.assertIn("✅", status_msg)
                self.assertIn("URLs generated", status_msg)
                
                # Should return URLs HTML without scores
                self.assertIn("https://www.gmass.co/inbox?q=test1", urls_html)
                self.assertIn("https://www.gmass.co/inbox?q=test2", urls_html)
                
                # Should NOT contain score data (Stage 1 only generates URLs)
                self.assertNotIn("Score:", urls_html)
                self.assertNotIn("Inbox:", urls_html)
                
        finally:
            if os.path.exists(accounts_file_path):
                os.unlink(accounts_file_path)
    
    def test_stage2_fetches_scores_with_playwright(self):
        """Test Stage 2: Fetch scores using Playwright without sending"""
        accounts_file_path = self.create_temp_accounts_file()
        
        try:
            # Mock Playwright results
            mock_results = {
                "test1@gmail.com": {
                    "sender": "test1@gmail.com",
                    "inbox": 2,
                    "promotions": 1,
                    "spam": 0,
                    "score": 2.6,
                    "link": "https://www.gmass.co/inbox?q=test1",
                    "ts": "2024-01-01 12:00"
                },
                "test2@yahoo.com": {
                    "sender": "test2@yahoo.com", 
                    "inbox": 1,
                    "promotions": 0,
                    "spam": 2,
                    "score": 1.0,
                    "link": "https://www.gmass.co/inbox?q=test2",
                    "ts": "2024-01-01 12:00"
                }
            }
            
            with patch('gmass_scraper.fetch_gmass_scores', return_value=mock_results):
                class MockFile:
                    def __init__(self, path):
                        self.name = path
                
                accounts_file = MockFile(accounts_file_path)
                
                # Run Stage 2
                status_msg, results_table = fetch_gmass_scores_only(accounts_file)
                
                # Should return success message
                self.assertIn("✅", status_msg)
                self.assertIn("scores fetched", status_msg)
                
                # Should return table with scores
                self.assertIn("test1@gmail.com", results_table)
                self.assertIn("test2@yahoo.com", results_table)
                self.assertIn("2.6", results_table)  # Score for test1
                self.assertIn("1.0", results_table)  # Score for test2
                
                # Should contain table headers
                self.assertIn("Inbox", results_table)
                self.assertIn("Promotions", results_table)
                self.assertIn("Score", results_table)
                
        finally:
            if os.path.exists(accounts_file_path):
                os.unlink(accounts_file_path)
    
    def test_url_generation_function(self):
        """Test the generate_gmass_urls function directly"""
        emails = ["user1@gmail.com", "user2@yahoo.com"]
        
        urls = generate_gmass_urls(emails)
        
        self.assertEqual(len(urls), 2)
        self.assertEqual(urls["user1@gmail.com"], "https://www.gmass.co/inbox?q=user1")
        self.assertEqual(urls["user2@yahoo.com"], "https://www.gmass.co/inbox?q=user2")
    
    def test_stage2_without_stage1_fails_gracefully(self):
        """Test Stage 2 fails gracefully if no accounts file provided"""
        status_msg, results_table = fetch_gmass_scores_only(None)
        
        self.assertIn("❌", status_msg)
        self.assertIn("upload accounts file", status_msg)
    
    def test_complete_2stage_workflow(self):
        """Test complete workflow: Stage 1 → Stage 2"""
        accounts_file_path = self.create_temp_accounts_file()
        
        try:
            class MockFile:
                def __init__(self, path):
                    self.name = path
            
            accounts_file = MockFile(accounts_file_path)
            
            # Stage 1: Send and get URLs
            with patch('gmass_scraper.main_worker') as mock_worker:
                mock_worker.return_value = iter([("✅ Complete", "", "", "")])
                
                status1, urls1 = run_gmass_test_with_urls_only(
                    accounts_file=accounts_file,
                    mode="gmass",
                    subjects_text="Test",
                    bodies_text="Test",
                    gmass_recipients_text="\n".join(self.gmass_recipients),
                    include_pdfs=False,
                    include_images=False,
                    support_number="",
                    attachment_format="pdf",
                    use_gmail_api=False,
                    gmail_credentials_files=None,
                    sender_name_type="business"
                )
                
                self.assertIn("✅", status1)
                self.assertIn("https://www.gmass.co/inbox", urls1)
            
            # Stage 2: Get scores
            mock_scores = {
                "test1@gmail.com": {"inbox": 1, "promotions": 0, "spam": 0, "score": 1.0, "link": "https://www.gmass.co/inbox?q=test1", "ts": "2024-01-01 12:00", "sender": "test1@gmail.com"},
                "test2@yahoo.com": {"inbox": 0, "promotions": 1, "spam": 0, "score": 0.6, "link": "https://www.gmass.co/inbox?q=test2", "ts": "2024-01-01 12:00", "sender": "test2@yahoo.com"}
            }
            
            with patch('gmass_scraper.fetch_gmass_scores', return_value=mock_scores):
                status2, table2 = fetch_gmass_scores_only(accounts_file)
                
                self.assertIn("✅", status2)
                self.assertIn("1.0", table2)  # Score data present
                self.assertIn("0.6", table2)  # Score data present
                
        finally:
            if os.path.exists(accounts_file_path):
                os.unlink(accounts_file_path)

if __name__ == "__main__":
    unittest.main()