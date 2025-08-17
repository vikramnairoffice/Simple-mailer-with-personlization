#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sender_names import generate_sender_name

def test_sender_names():
    """Test the Faker-based sender name generation"""
    print("Testing Business Names:")
    for i in range(5):
        business_name = generate_sender_name("business")
        print(f"{i+1}. {business_name}")
    
    print("\nTesting Personal Names:")
    for i in range(5):
        personal_name = generate_sender_name("personal")
        print(f"{i+1}. {personal_name}")
    
    print("\nTesting Default (Business) Names:")
    for i in range(3):
        default_name = generate_sender_name()
        print(f"{i+1}. {default_name}")

if __name__ == "__main__":
    test_sender_names()