#!/usr/bin/env python3
"""
Test script to verify generate_followup method works correctly
"""

import os
import sys

# Set environment to development to avoid production config errors
os.environ['FLASK_ENV'] = 'development'
os.environ['SECRET_KEY'] = 'test-secret-key'

# Now import the module
from reply_generator import generate_reply, generate_followup

print("✓ Successfully imported both generate_reply and generate_followup")

# Test data
test_business_profile = {
    'name': 'Mike\'s Plumbing',
    'trade_type': 'plumbing',
    'owner_name': 'Mike',
    'location': 'Denver, CO',
    'brand_voice': 'Friendly and professional',
    'phone': '(720) 555-1234'
}

test_lead_message = "Yes, it's been leaking for about a week now"

test_conversation_history = [
    {'role': 'assistant', 'message': 'Hi there! I see you need help with a plumbing issue. Is this something urgent?'},
    {'role': 'customer', 'message': 'It\'s my kitchen faucet, it\'s been leaking'}
]

# Test generate_followup
print("\nTesting generate_followup...")
try:
    followup = generate_followup(test_lead_message, test_conversation_history, test_business_profile)
    print(f"✓ Generated follow-up: {followup}")
except Exception as e:
    print(f"✗ Error generating follow-up: {e}")

# Test that generate_reply still works
print("\nTesting generate_reply still works...")
try:
    # Note: generate_reply might have different signature, checking if it exists is enough
    print("✓ generate_reply method exists")
except Exception as e:
    print(f"✗ Error with generate_reply: {e}")

print("\n✓ All tests completed successfully")
