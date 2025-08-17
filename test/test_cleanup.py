"""
Test script to verify the cleaned mailer.py code works correctly
"""
# Use ASCII characters instead of Unicode to avoid encoding issues

def test_imports():
    """Test all critical imports"""
    try:
        from mailer import (
            SmtpMailer, AccountErrorTracker, ProgressTracker, 
            _ensure_service_for_sender, _gmail_api_send,
            main_worker, parse_file_lines, validate_accounts_file
        )
        print("+ All mailer imports successful")
        return True
    except ImportError as e:
        print(f"- Import error: {e}")
        return False

def test_smtp_mailer():
    """Test SMTP mailer initialization"""
    try:
        from mailer import SmtpMailer
        mailer = SmtpMailer()
        
        # Check if expected providers are configured
        expected_providers = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com']
        for provider in expected_providers:
            if provider not in mailer.smtp_configs:
                print(f"- Missing provider: {provider}")
                return False
        
        print("+ SMTP mailer initialized correctly")
        return True
    except Exception as e:
        print(f"- SMTP mailer error: {e}")
        return False

def test_gmail_auth_function():
    """Test Gmail authentication function"""
    try:
        from mailer import _ensure_service_for_sender
        
        # Test with no credentials (should return None gracefully)
        result = _ensure_service_for_sender(None, None, None)
        if result is not None:
            print("- Expected None for no credentials")
            return False
            
        print("+ Gmail auth function handles no credentials correctly")
        return True
    except Exception as e:
        print(f"- Gmail auth function error: {e}")
        return False

def test_error_tracker():
    """Test error tracking system"""
    try:
        from mailer import AccountErrorTracker
        tracker = AccountErrorTracker()
        
        # Add test error
        tracker.add_error("test@gmail.com", "AUTH_FAILED", "Test error message")
        
        # Check error was added
        if "test@gmail.com" not in tracker.account_errors:
            print("- Error not tracked properly")
            return False
            
        # Test HTML report generation
        html_report = tracker.get_html_report()
        if not html_report or "test@gmail.com" not in html_report:
            print("- HTML report generation failed")
            return False
            
        print("+ Error tracker works correctly")
        return True
    except Exception as e:
        print(f"- Error tracker error: {e}")
        return False

def test_progress_tracker():
    """Test progress tracking system"""
    try:
        from mailer import ProgressTracker
        tracker = ProgressTracker(2)
        
        # Update progress for test account
        tracker.update_progress("test@gmail.com", 5, 10, "sending")
        
        # Check progress was recorded
        if "test@gmail.com" not in tracker.account_progress:
            print("- Progress not tracked properly")
            return False
            
        progress = tracker.account_progress["test@gmail.com"]
        if progress['sent'] != 5 or progress['total'] != 10:
            print("- Progress values incorrect")
            return False
            
        # Test HTML report
        html_report = tracker.get_html_report()
        if not html_report or "test@gmail.com" not in html_report:
            print("- Progress HTML report failed")
            return False
            
        print("+ Progress tracker works correctly")
        return True
    except Exception as e:
        print(f"- Progress tracker error: {e}")
        return False

def test_file_validation():
    """Test file validation functions"""
    try:
        from mailer import validate_accounts_file, validate_leads_file
        
        # Test valid accounts format
        valid_accounts = ["test1@gmail.com,password1", "test2@yahoo.com,password2"]
        valid, msg, accounts = validate_accounts_file(valid_accounts)
        if not valid or len(accounts) != 2:
            print(f"- Account validation failed: {msg}")
            return False
            
        # Test valid leads format
        valid_leads = ["lead1@gmail.com", "lead2@yahoo.com"]
        valid, msg, leads = validate_leads_file(valid_leads)
        if not valid or len(leads) != 2:
            print(f"- Leads validation failed: {msg}")
            return False
            
        print("+ File validation works correctly")
        return True
    except Exception as e:
        print(f"- File validation error: {e}")
        return False

def test_ui_integration():
    """Test UI integration"""
    try:
        from ui import gradio_ui
        
        # Create UI instance (don't launch)
        demo = gradio_ui()
        if demo is None:
            print("- UI creation failed")
            return False
            
        print("+ UI integration works correctly")
        return True
    except Exception as e:
        print(f"- UI integration error: {e}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    tests = [
        ("Import Tests", test_imports),
        ("SMTP Mailer", test_smtp_mailer),
        ("Gmail Auth Function", test_gmail_auth_function),
        ("Error Tracker", test_error_tracker),
        ("Progress Tracker", test_progress_tracker),
        ("File Validation", test_file_validation),
        ("UI Integration", test_ui_integration),
    ]
    
    print("Running cleanup verification tests...\n")
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        if test_func():
            passed += 1
        print()
    
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nSUCCESS: All tests passed! Code cleanup successful.")
        return True
    else:
        print(f"\nFAILED: {total - passed} tests failed. Code may have issues.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)