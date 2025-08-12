#!/usr/bin/env python3
"""
Test script for GMass scraper functionality
Tests the scraper by opening GMass site and scraping available scores
"""

import time
from gmass_scraper import fetch_gmass_scores, format_gmass_results_table

def test_gmass_scraper():
    """Test GMass scraper with sample email addresses"""
    print("Testing GMass scraper functionality...")
    print("=" * 50)
    
    # Test with some sample email addresses that might have existing data on GMass
    test_emails = [
        "test@example.com",
        "demo@gmail.com", 
        "sample@outlook.com"
    ]
    
    print(f"Testing with emails: {', '.join(test_emails)}")
    print("Opening GMass site and scraping scores...")
    print("This may take a few seconds per email...")
    
    # Run the scraper
    start_time = time.time()
    results = fetch_gmass_scores(test_emails)
    end_time = time.time()
    
    print(f"Scraping completed in {end_time - start_time:.2f} seconds")
    print("\nResults:")
    print("=" * 50)
    
    # Display results
    for email, data in results.items():
        print(f"\nEmail: {email}")
        print(f"   Inbox: {data.get('inbox', 0)}")
        print(f"   Promotions: {data.get('promotions', 0)}")
        print(f"   Spam: {data.get('spam', 0)}")
        print(f"   Score: {data.get('score', 0)}")
        print(f"   Link: {data.get('link', 'N/A')}")
        print(f"   Timestamp: {data.get('ts', 'N/A')}")
        if data.get('error'):
            print(f"   Error: {data['error']}")
    
    # Test HTML table formatting
    print("\nTesting HTML table formatting...")
    html_table = format_gmass_results_table(results)
    print(f"HTML table generated ({len(html_table)} characters)")
    
    # Save HTML table to file for inspection
    with open("gmass_test_results.html", "w", encoding="utf-8") as f:
        f.write(f"""
<!DOCTYPE html>
<html>
<head>
    <title>GMass Test Results</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>GMass Scraper Test Results</h1>
    <p>Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
    {html_table}
</body>
</html>
        """)
    
    print("HTML results saved to: gmass_test_results.html")
    
    # Summary
    print("\nSummary:")
    print("=" * 50)
    total_tested = len(test_emails)
    successful_scrapes = sum(1 for data in results.values() if not data.get('error'))
    failed_scrapes = total_tested - successful_scrapes
    
    print(f"Total emails tested: {total_tested}")
    print(f"Successful scrapes: {successful_scrapes}")
    print(f"Failed scrapes: {failed_scrapes}")
    
    if successful_scrapes > 0:
        avg_score = sum(data.get('score', 0) for data in results.values() if not data.get('error')) / successful_scrapes
        print(f"Average score: {avg_score:.2f}")
    
    return results

if __name__ == "__main__":
    try:
        results = test_gmass_scraper()
        print("\nTest completed successfully!")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()