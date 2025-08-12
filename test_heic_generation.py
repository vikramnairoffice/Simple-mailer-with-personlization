#!/usr/bin/env python3
"""
Test script for HEIC invoice generation functionality
"""

import os
import sys
from invoice import InvoiceGenerator

def test_heic_generation():
    """Test HEIC invoice generation"""
    print("Testing HEIC invoice generation...")
    
    # Create invoice generator instance
    generator = InvoiceGenerator()
    
    # Test parameters
    test_email = "test@example.com"
    test_phone = "(555) 123-4567"
    
    try:
        # Test PDF generation (should work)
        print("1. Testing PDF generation...")
        pdf_path = generator.generate_for_recipient(test_email, test_phone, "pdf")
        if os.path.exists(pdf_path):
            print(f"[OK] PDF generated successfully: {pdf_path}")
        else:
            print("[FAIL] PDF generation failed")
            return False
            
        # Test PNG generation (should work)
        print("2. Testing PNG generation...")
        png_path = generator.generate_for_recipient(test_email, test_phone, "image")
        if os.path.exists(png_path):
            print(f"[OK] PNG generated successfully: {png_path}")
        else:
            print("[FAIL] PNG generation failed")
            return False
            
        # Test HEIC generation (new functionality)
        print("3. Testing HEIC generation...")
        heic_path = generator.generate_for_recipient(test_email, test_phone, "heic")
        if os.path.exists(heic_path):
            print(f"[OK] HEIC generated successfully: {heic_path}")
            
            # Check file size (should be non-zero)
            file_size = os.path.getsize(heic_path)
            print(f"   HEIC file size: {file_size} bytes")
            
            if file_size > 0:
                print("[OK] HEIC file appears to be valid (non-zero size)")
            else:
                print("[FAIL] HEIC file is empty")
                return False
        else:
            print("[FAIL] HEIC generation failed")
            return False
            
        print("\n[SUCCESS] All tests passed! HEIC generation is working correctly.")
        return True
        
    except Exception as e:
        print(f"[ERROR] Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_heic_generation()
    sys.exit(0 if success else 1)