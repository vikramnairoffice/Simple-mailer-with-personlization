#!/usr/bin/env python3

def test_lead_distribution():
    """Test the new equal distribution algorithm"""
    
    def distribute_leads(all_leads, num_accounts, leads_per_account):
        """Simulate the new distribution logic"""
        total_leads = len(all_leads)
        
        # Calculate base leads per account and remainder
        base_leads_per_account = total_leads // num_accounts
        remainder = total_leads % num_accounts
        
        # Apply cap: each account gets min(calculated_leads, leads_per_account)
        leads_distribution = []
        start_idx = 0
        
        for i in range(num_accounts):
            # First 'remainder' accounts get +1 extra lead
            account_lead_count = base_leads_per_account + (1 if i < remainder else 0)
            # Apply the cap
            account_lead_count = min(account_lead_count, leads_per_account)
            
            end_idx = start_idx + account_lead_count
            account_leads = all_leads[start_idx:end_idx]
            leads_distribution.append(account_leads)
            start_idx = end_idx
            
        return leads_distribution

    # Test cases
    test_cases = [
        # (total_leads, num_accounts, leads_per_account, description)
        (12, 12, 10, "Your case: 12 leads, 12 accounts, cap 10"),
        (15, 12, 10, "15 leads, 12 accounts, cap 10"),
        (100, 5, 300, "100 leads, 5 accounts, cap 300"),
        (1000, 5, 15, "1000 leads, 5 accounts, cap 15"),
        (7, 3, 10, "7 leads, 3 accounts, cap 10"),
    ]
    
    for total_leads, num_accounts, leads_per_account, description in test_cases:
        print(f"\n=== {description} ===")
        all_leads = [f"lead{i}@test.com" for i in range(total_leads)]
        
        distribution = distribute_leads(all_leads, num_accounts, leads_per_account)
        
        for i, account_leads in enumerate(distribution):
            print(f"Account {i}: {len(account_leads)} leads - {account_leads[:3]}{'...' if len(account_leads) > 3 else ''}")
        
        total_distributed = sum(len(account_leads) for account_leads in distribution)
        print(f"Total distributed: {total_distributed}/{total_leads}")

if __name__ == "__main__":
    test_lead_distribution()