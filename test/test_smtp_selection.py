"""
Test suite for SMTP Account Selection System
Tests the functionality for displaying validated accounts and selecting which ones to use
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from unittest.mock import Mock, patch, MagicMock


class TestAccountSelectionManager(unittest.TestCase):
    """Test the AccountSelectionManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        from ui_token_helpers import AccountSelectionManager
        self.manager = AccountSelectionManager()
        
        self.sample_validated_accounts = [
            {"email": "test1@gmail.com", "status": "Working"},
            {"email": "test2@yahoo.com", "status": "Working"}, 
            {"email": "test3@hotmail.com", "status": "Working"},
            {"email": "test4@gmail.com", "status": "Working"},
            {"email": "test5@aol.com", "status": "Working"}
        ]
    
    def test_initial_state_empty(self):
        """Test manager starts with empty state"""
        self.assertEqual(len(self.manager.get_all_accounts()), 0)
        self.assertEqual(len(self.manager.get_selected_accounts()), 0)
    
    def test_load_validated_accounts(self):
        """Test loading validated accounts into manager"""
        self.manager.load_validated_accounts(self.sample_validated_accounts)
        
        all_accounts = self.manager.get_all_accounts()
        self.assertEqual(len(all_accounts), 5)
        
        # All accounts should be selected by default
        selected = self.manager.get_selected_accounts()
        self.assertEqual(len(selected), 5)
    
    def test_select_specific_accounts(self):
        """Test selecting specific accounts by email"""
        self.manager.load_validated_accounts(self.sample_validated_accounts)
        
        # Unselect 2 accounts
        self.manager.set_account_selection("test2@yahoo.com", False)
        self.manager.set_account_selection("test4@gmail.com", False)
        
        selected = self.manager.get_selected_accounts()
        self.assertEqual(len(selected), 3)
        
        selected_emails = [acc["email"] for acc in selected]
        self.assertIn("test1@gmail.com", selected_emails)
        self.assertIn("test3@hotmail.com", selected_emails) 
        self.assertIn("test5@aol.com", selected_emails)
        self.assertNotIn("test2@yahoo.com", selected_emails)
        self.assertNotIn("test4@gmail.com", selected_emails)
    
    def test_get_selection_table_data(self):
        """Test generating table data for UI display"""
        self.manager.load_validated_accounts(self.sample_validated_accounts)
        
        # Unselect one account
        self.manager.set_account_selection("test3@hotmail.com", False)
        
        table_data = self.manager.get_selection_table_data()
        
        self.assertEqual(len(table_data), 5)
        
        # Check table structure: [email, status, checkbox]
        for row in table_data:
            self.assertEqual(len(row), 3)
            self.assertIn("@", row[0])  # Email format
            self.assertEqual(row[1], "Working")  # Status
            self.assertIn(row[2], [True, False])  # Checkbox boolean
        
        # Check specific unselected account
        hotmail_row = next(row for row in table_data if "test3@hotmail.com" in row[0])
        self.assertFalse(hotmail_row[2])  # Should be unchecked


class TestUITableGeneration(unittest.TestCase):
    """Test UI table generation from validation results"""
    
    def test_create_selection_table_from_validation_results(self):
        """Test creating selection table from SMTP validation results"""
        validation_results = {
            "working": [
                {"email": "user1@gmail.com", "provider": "Gmail"},
                {"email": "user2@yahoo.com", "provider": "Yahoo"},
                {"email": "user3@hotmail.com", "provider": "Hotmail"}
            ],
            "failed": [
                {"email": "broken@gmail.com", "error": "Auth failed"}
            ]
        }
        
        from ui_token_helpers import create_selection_table_from_validation
        
        table_data = create_selection_table_from_validation(validation_results)
        
        # Should only show working accounts
        self.assertEqual(len(table_data), 3)
        
        # Check table format
        for row in table_data:
            self.assertEqual(len(row), 3)
            self.assertTrue(row[2])  # All should be selected by default
    
    def test_empty_validation_results(self):
        """Test handling empty validation results"""
        validation_results = {"working": [], "failed": []}
        
        from ui_token_helpers import create_selection_table_from_validation
        
        table_data = create_selection_table_from_validation(validation_results)
        
        # Should return message row when no working accounts
        self.assertEqual(len(table_data), 1)
        self.assertIn("No working", table_data[0][0])


class TestWorkerFiltering(unittest.TestCase):
    """Test worker activation based on account selection"""
    
    def test_filter_accounts_for_workers(self):
        """Test filtering accounts for worker activation"""
        all_accounts = [
            {"email": "test1@gmail.com", "password": "pass1"},
            {"email": "test2@yahoo.com", "password": "pass2"},
            {"email": "test3@hotmail.com", "password": "pass3"},
            {"email": "test4@gmail.com", "password": "pass4"},
            {"email": "test5@aol.com", "password": "pass5"}
        ]
        
        selected_emails = ["test1@gmail.com", "test3@hotmail.com", "test5@aol.com"]
        
        from ui_token_helpers import filter_accounts_for_workers
        
        filtered_accounts = filter_accounts_for_workers(all_accounts, selected_emails)
        
        self.assertEqual(len(filtered_accounts), 3)
        
        filtered_emails = [acc["email"] for acc in filtered_accounts]
        self.assertEqual(set(filtered_emails), set(selected_emails))
    
    def test_filter_with_empty_selection(self):
        """Test filtering when no accounts are selected"""
        all_accounts = [
            {"email": "test1@gmail.com", "password": "pass1"},
            {"email": "test2@yahoo.com", "password": "pass2"}
        ]
        
        selected_emails = []
        
        from ui_token_helpers import filter_accounts_for_workers
        
        filtered_accounts = filter_accounts_for_workers(all_accounts, selected_emails)
        
        self.assertEqual(len(filtered_accounts), 0)
    
    def test_worker_count_matches_selection(self):
        """Test that worker count matches selected accounts"""
        # Mock the filtered accounts worker to capture the accounts parameter
        with patch('mailer.main_worker_with_filtered_accounts') as mock_worker:
            mock_worker.return_value = iter([("log", "progress", "errors", "summary")])
            
            from ui_token_helpers import unified_send_handler_with_selection
            
            # Mock accounts file content
            accounts_content = [
                "test1@gmail.com,pass1",
                "test2@yahoo.com,pass2", 
                "test3@hotmail.com,pass3",
                "test4@gmail.com,pass4",
                "test5@aol.com,pass5"
            ]
            
            # Mock file object
            mock_file = Mock()
            mock_file.name = "test_accounts.txt"
            
            with patch('mailer.parse_file_lines', return_value=accounts_content):
                with patch('mailer.validate_accounts_file', return_value=(True, "Valid", [
                    {"email": "test1@gmail.com", "password": "pass1"},
                    {"email": "test2@yahoo.com", "password": "pass2"},
                    {"email": "test3@hotmail.com", "password": "pass3"},
                    {"email": "test4@gmail.com", "password": "pass4"},
                    {"email": "test5@aol.com", "password": "pass5"}
                ])):
                    with patch('mailer.convert_mode_to_attachment_flags', return_value=(True, False)):
                        
                        # Selected accounts (3 out of 5)
                        selected_emails = ["test1@gmail.com", "test3@hotmail.com", "test5@aol.com"]
                        
                        result = unified_send_handler_with_selection(
                            mock_file, "App Password", None, 10, 3, "leads",
                            "Subject", "Body", "", "Attachment", "pdf", "pdf", "", "business",
                            selected_emails
                        )
                        
                        # Verify filtered worker was called
                        mock_worker.assert_called_once()
                        
                        # Get the arguments passed to main_worker_with_filtered_accounts
                        args, kwargs = mock_worker.call_args
                        
                        # First argument should be filtered_accounts (length 3)
                        filtered_accounts = args[0]
                        self.assertEqual(len(filtered_accounts), 3)
                        
                        # Check that only selected accounts are included
                        filtered_emails = [acc["email"] for acc in filtered_accounts]
                        self.assertEqual(set(filtered_emails), set(selected_emails))


class TestIntegrationFlow(unittest.TestCase):
    """Test the complete integration flow"""
    
    def test_complete_selection_workflow(self):
        """Test complete workflow: upload -> validate -> select -> send"""
        
        # Step 1: Upload and validate accounts
        with patch('mailer.parse_file_lines') as mock_parse:
            with patch('mailer.validate_accounts_file') as mock_validate:
                with patch('token_manager.token_manager') as mock_token_manager:
                    
                    # Mock account parsing and validation
                    mock_parse.return_value = [
                        "user1@gmail.com,pass1",
                        "user2@yahoo.com,pass2",
                        "user3@hotmail.com,pass3",
                        "user4@gmail.com,pass4",
                        "user5@aol.com,pass5"
                    ]
                    
                    mock_validate.return_value = (True, "Valid", [
                        {"email": "user1@gmail.com", "password": "pass1"},
                        {"email": "user2@yahoo.com", "password": "pass2"},
                        {"email": "user3@hotmail.com", "password": "pass3"},
                        {"email": "user4@gmail.com", "password": "pass4"},
                        {"email": "user5@aol.com", "password": "pass5"}
                    ])
                    
                    from ui_token_helpers import AccountSelectionManager
                    
                    # Step 2: Load into selection manager
                    manager = AccountSelectionManager()
                    validated_accounts = [
                        {"email": "user1@gmail.com", "status": "Working"},
                        {"email": "user2@yahoo.com", "status": "Working"},
                        {"email": "user3@hotmail.com", "status": "Working"},
                        {"email": "user4@gmail.com", "status": "Working"},
                        {"email": "user5@aol.com", "status": "Working"}
                    ]
                    
                    manager.load_validated_accounts(validated_accounts)
                    
                    # Step 3: User makes selection (uncheck 2 accounts)
                    manager.set_account_selection("user2@yahoo.com", False)
                    manager.set_account_selection("user4@gmail.com", False)
                    
                    # Step 4: Verify selection state
                    selected = manager.get_selected_accounts()
                    self.assertEqual(len(selected), 3)
                    
                    selected_emails = [acc["email"] for acc in selected]
                    expected_emails = ["user1@gmail.com", "user3@hotmail.com", "user5@aol.com"]
                    self.assertEqual(set(selected_emails), set(expected_emails))
                    
                    # Step 5: Verify table data for UI
                    table_data = manager.get_selection_table_data()
                    self.assertEqual(len(table_data), 5)
                    
                    # Count selected vs unselected
                    selected_count = sum(1 for row in table_data if row[2])
                    unselected_count = sum(1 for row in table_data if not row[2])
                    
                    self.assertEqual(selected_count, 3)
                    self.assertEqual(unselected_count, 2)


if __name__ == "__main__":
    unittest.main()