import unittest
import urllib.parse
from gmass_scraper import generate_gmass_urls

class TestGmassUrlGeneration(unittest.TestCase):
    """Test GMass URL generation functionality"""
    
    def test_single_email_url_generation(self):
        """Test URL generation for a single email account"""
        email = "niao78@gmail.com"
        expected_url = "https://www.gmass.co/inbox?q=niao78"
        
        urls = generate_gmass_urls([email])
        
        self.assertIn(email, urls)
        self.assertEqual(urls[email], expected_url)
    
    def test_multiple_emails_url_generation(self):
        """Test URL generation for multiple email accounts"""
        emails = ["amitr78@gmail.com", "test@yahoo.com", "user@hotmail.com"]
        expected_urls = {
            "amitr78@gmail.com": "https://www.gmass.co/inbox?q=amitr78",
            "test@yahoo.com": "https://www.gmass.co/inbox?q=test", 
            "user@hotmail.com": "https://www.gmass.co/inbox?q=user"
        }
        
        urls = generate_gmass_urls(emails)
        
        self.assertEqual(len(urls), 3)
        for email in emails:
            self.assertIn(email, urls)
            self.assertEqual(urls[email], expected_urls[email])
    
    def test_special_characters_in_email(self):
        """Test URL generation with special characters in username"""
        email = "user.name+tag@gmail.com"
        expected_username = "user.name+tag"
        expected_url = f"https://www.gmass.co/inbox?q={urllib.parse.quote(expected_username)}"
        
        urls = generate_gmass_urls([email])
        
        self.assertIn(email, urls)
        self.assertEqual(urls[email], expected_url)
    
    def test_empty_email_list(self):
        """Test URL generation with empty email list"""
        urls = generate_gmass_urls([])
        
        self.assertEqual(urls, {})
    
    def test_invalid_email_format(self):
        """Test URL generation with invalid email format"""
        email = "invalid-email"
        
        with self.assertRaises(ValueError):
            generate_gmass_urls([email])

if __name__ == "__main__":
    unittest.main()