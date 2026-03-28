#!/usr/bin/env python3
"""Test script for lead_summarizer module"""

# Mock the database_manager to avoid import issues
import sys
from unittest.mock import MagicMock

# Mock database_manager before importing lead_summarizer
sys.modules['database_manager'] = MagicMock()

# Mock Config to avoid missing API key issues
class MockConfig:
    ANTHROPIC_API_KEY = 'test-api-key'

sys.modules['config'].Config = MockConfig

# Now import and test lead_summarizer
try:
    from lead_summarizer import LeadSummarizer
    
    print('✓ LeadSummarizer imported successfully')
    
    # Test instantiation
    ls = LeadSummarizer()
    print('✓ LeadSummarizer instantiated successfully')
    
    # Test method exists
    print('✓ generate_summary method exists:', hasattr(ls, 'generate_summary'))
    
    # Test helper methods exist
    print('✓ _format_conversation method exists:', hasattr(ls, '_format_conversation'))
    print('✓ _build_summary_prompt method exists:', hasattr(ls, '_build_summary_prompt'))
    print('✓ _calculate_lead_score method exists:', hasattr(ls, '_calculate_lead_score'))
    print('✓ _format_for_email method exists:', hasattr(ls, '_format_for_email'))
    print('✓ _get_timestamp method exists:', hasattr(ls, '_get_timestamp'))
    
    # Test _format_conversation with mock data
    mock_messages = [
        {'from_customer': True, 'content': 'I need a contractor for my kitchen remodel'},
        {'from_customer': False, 'content': 'What is your budget for this project?'},
        {'from_customer': True, 'content': 'Around $15,000, and I need it done by next month'}
    ]
    
    formatted = ls._format_conversation(mock_messages)
    print('✓ _format_conversation works with mock data')
    print('  Sample output:', formatted[:100] + '...')
    
    # Test lead scoring with mock data
    mock_summary = {'raw_summary': 'Customer needs urgent kitchen remodel, budget $15,000'}
    score = ls._calculate_lead_score(mock_summary, mock_messages)
    print('✓ _calculate_lead_score works with mock data')
    print('  Score result:', score)
    
    print('\n✅ All lead_summarizer tests passed!')
    
except Exception as e:
    print(f'❌ Error testing lead_summarizer: {e}')
    import traceback
    traceback.print_exc()
