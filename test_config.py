import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import MagicMock

# Test Environment Variables
TEST_ENV_VARS = {
    'OPENAI_API_KEY': 'test-openai-key-12345',
    'GMAIL_CLIENT_ID': 'test-gmail-client-id.apps.googleusercontent.com',
    'GMAIL_CLIENT_SECRET': 'test-gmail-client-secret',
    'GMAIL_REFRESH_TOKEN': 'test-gmail-refresh-token',
    'GMAIL_ACCESS_TOKEN': 'test-gmail-access-token',
    'SENDER_EMAIL': 'test@clawcontractor.com',
    'SENDER_NAME': 'Test Claw Contractor',
    'DATABASE_URL': 'sqlite:///:memory:',
    'TESTING': 'true',
    'LOG_LEVEL': 'DEBUG',
    'MAX_RETRIES': '3',
    'RETRY_DELAY': '1',
    'EMAIL_BATCH_SIZE': '10',
    'RATE_LIMIT_PER_MINUTE': '60'
}

# Mock Lead Data with Various Scenarios
MOCK_LEAD_DATA = {
    'new_residential_kitchen': {
        'id': 'lead_001',
        'name': 'John Smith',
        'email': 'john.smith@email.com',
        'phone': '555-123-4567',
        'project_type': 'Kitchen Remodel',
        'property_type': 'Residential',
        'project_description': 'Complete kitchen renovation with new cabinets, countertops, and appliances',
        'budget_range': '$25,000 - $50,000',
        'timeline': '3-4 months',
        'address': '123 Main St, Springfield, IL 62701',
        'source': 'Google Ads',
        'created_at': datetime.now().isoformat(),
        'status': 'new',
        'priority': 'high',
        'contact_attempts': 0,
        'last_contact': None,
        'notes': '',
        'preferred_contact_method': 'email',
        'availability': 'weekdays after 5pm'
    },
    
    'returning_commercial_bathroom': {
        'id': 'lead_002',
        'name': 'Sarah Johnson',
        'email': 'sarah.johnson@businessemail.com',
        'phone': '555-987-6543',
        'project_type': 'Bathroom Renovation',
        'property_type': 'Commercial',
        'project_description': 'Office building bathroom upgrades for ADA compliance',
        'budget_range': '$75,000 - $100,000',
        'timeline': '2-3 months',
        'address': '456 Business Blvd, Springfield, IL 62702',
        'source': 'Referral',
        'created_at': (datetime.now() - timedelta(days=7)).isoformat(),
        'status': 'contacted',
        'priority': 'medium',
        'contact_attempts': 2,
        'last_contact': (datetime.now() - timedelta(days=3)).isoformat(),
        'notes': 'Previous customer from 2022 kitchen project. Very satisfied with work.',
        'preferred_contact_method': 'phone',
        'availability': 'business hours only',
        'is_returning_customer': True,
        'previous_projects': ['Kitchen Remodel - 2022']
    },
    
    'urgent_flooring_repair': {
        'id': 'lead_003',
        'name': 'Mike Wilson',
        'email': 'mike.wilson@gmail.com',
        'phone': '555-456-7890',
        'project_type': 'Flooring Installation',
        'property_type': 'Residential',
        'project_description': 'Water damage repair and hardwood floor replacement in living room',
        'budget_range': '$10,000 - $25,000',
        'timeline': 'ASAP - 2 weeks',
        'address': '789 Oak Ave, Springfield, IL 62703',
        'source': 'Facebook',
        'created_at': datetime.now().isoformat(),
        'status': 'new',
        'priority': 'urgent',
        'contact_attempts': 0,
        'last_contact': None,
        'notes': 'Insurance claim involved. Need quick response.',
        'preferred_contact_method': 'phone',
        'availability': 'anytime',
        'is_insurance_claim': True,
        'urgency_reason': 'water damage'
    },
    
    'large_addition_project': {
        'id': 'lead_004',
        'name': 'Robert Davis',
        'email': 'robert.davis@email.com',
        'phone': '555-321-9876',
        'project_type': 'Home Addition',
        'property_type': 'Residential',
        'project_description': 'Two-story addition with master suite and home office',
        'budget_range': '$150,000 - $200,000',
        'timeline': '6-8 months',
        'address': '321 Elm St, Springfield, IL 62704',
        'source': 'Website',
        'created_at': (datetime.now() - timedelta(days=2)).isoformat(),
        'status': 'new',
        'priority': 'high',
        'contact_attempts': 0,
        'last_contact': None,
        'notes': 'High-value project. Architect already selected.',
        'preferred_contact_method': 'email',
        'availability': 'weekends preferred',
        'has_architect': True,
        'permits_needed': True
    },
    
    'small_repair_job': {
        'id': 'lead_005',
        'name': 'Lisa Brown',
        'email': 'lisa.brown@yahoo.com',
        'phone': '555-654-3210',
        'project_type': 'General Repairs',
        'property_type': 'Residential',
        'project_description': 'Minor drywall repairs and interior painting',
        'budget_range': '$2,000 - $5,000',
        'timeline': '1-2 weeks',
        'address': '654 Pine St, Springfield, IL 62705',
        'source': 'Yelp',
        'created_at': (datetime.now() - timedelta(days=1)).isoformat(),
        'status': 'new',
        'priority': 'low',
        'contact_attempts': 0,
        'last_contact': None,
        'notes': 'Small job but could lead to larger projects',
        'preferred_contact_method': 'email',
        'availability': 'flexible'
    }
}

# Sample Email Templates for Testing
SAMPLE_EMAIL_TEMPLATES = {
    'initial_response_residential': {
        'subject': 'Thank you for your interest in Claw Contractor - {project_type}',
        'template': '''Dear {name},

Thank you for reaching out to Claw Contractor regarding your {project_type} project. We're excited about the opportunity to work with you!

Based on your description of {project_description}, we believe we can help bring your vision to life. Our team has extensive experience with {property_type} projects in the {budget_range} range.

Here's what happens next:
1. We'll schedule a free consultation to discuss your project in detail
2. Provide you with a detailed estimate within 48 hours
3. Answer any questions you may have about the timeline and process

We understand your timeline of {timeline} and will work to accommodate your schedule.

Best regards,
The Claw Contractor Team
Phone: (555) 123-CLAW
Email: info@clawcontractor.com'''
    },
    
    'urgent_response': {
        'subject': 'URGENT: Immediate Response for {project_type} - Claw Contractor',
        'template': '''Dear {name},

We understand the urgency of your {project_type} situation and want to help immediately.

For urgent projects like {project_description}, we prioritize quick response and can often begin work within 24-48 hours of approval.

I'm personally reaching out to schedule an emergency consultation at your earliest convenience. Please call me directly at (555) 123-CLAW or reply to this email with your availability today.

We're here to help resolve your situation quickly and professionally.

Emergency Response Team
Claw Contractor
Available 24/7 for urgent repairs'''
    },
    
    'returning_customer': {
        'subject': 'Welcome back! Your new {project_type} project - Claw Contractor',
        'template': '''Dear {name},

It's wonderful to hear from you again! We're thrilled that you're considering Claw Contractor for your new {project_type} project.

We remember the excellent work we did on your {previous_projects} and look forward to exceeding your expectations once again. As a returning customer, you'll receive:

• Priority scheduling
• 10% discount on labor costs
• Expedited project timeline
• Direct access to your previous project manager

Your new project involving {project_description} sounds exciting, and we're confident we can deliver the same high-quality results you experienced before.

Looking forward to working with you again!

Best regards,
The Claw Contractor Team'''
    },
    
    'commercial_proposal': {
        'subject': 'Commercial {project_type} Proposal - Claw Contractor',
        'template': '''Dear {name},

Thank you for considering Claw Contractor for your commercial {project_type} project.

We specialize in {property_type} projects and understand the unique requirements, including:
• Compliance with commercial building codes
• Minimal disruption to business operations
• Flexible scheduling around your business hours
• Comprehensive project management

For your {project_description} with a budget of {budget_range}, we can provide a detailed proposal that includes timeline, materials, and cost breakdown.

We'd like to schedule a site visit to better understand your specific needs and provide an accurate estimate.

Professional regards,
Commercial Division
Claw Contractor'''
    },
    
    'follow_up_template': {
        'subject': 'Following up on your {project_type} inquiry - Claw Contractor',
        'template': '''Dear {name},

I wanted to follow up on the {project_type} inquiry you submitted {days_ago} days ago.

We're still very interested in helping you with your {project_description} and want to ensure we haven't missed connecting with you.

If you're still moving forward with this project, I'd love to schedule a brief call to discuss:
• Your current timeline
• Any changes to your project scope
• Next steps for moving forward

If now isn't the right time, we completely understand and will keep your information on file for future reference.

Thank you for considering Claw Contractor.

Best regards,
Follow-up Team
Claw Contractor'''
    }
}

# Mock OpenAI API Responses
MOCK_OPENAI_RESPONSES = {
    'email_generation_success': {
        'id': 'chatcmpl-test123',
        'object': 'chat.completion',
        'created': 1677858242,
        'model': 'gpt-3.5-turbo',
        'usage': {
            'prompt_tokens': 150,
            'completion_tokens': 200,
            'total_tokens': 350
        },
        'choices': [
            {
                'message': {
                    'role': 'assistant',
                    'content': 'Dear John,\n\nThank you for your interest in our kitchen remodeling services. We would love to discuss your project...'
                },
                'finish_reason': 'stop',
                'index': 0
            }
        ]
    },
    
    'email_generation_error': {
        'error': {
            'message': 'Rate limit exceeded',
            'type': 'rate_limit_error',
            'param': None,
            'code': 'rate_limit_exceeded'
        }
    },
    
    'lead_scoring_response': {
        'id': 'chatcmpl-score456',
        'object': 'chat.completion',
        'created': 1677858242,
        'model': 'gpt-3.5-turbo',
        'choices': [
            {
                'message': {
                    'role': 'assistant',
                    'content': '{"score": 85, "priority": "high", "reasoning": "Large budget, clear project scope, immediate timeline"}'
                },
                'finish_reason': 'stop',
                'index': 0
            }
        ]
    },
    
    'template_selection_response': {
        'id': 'chatcmpl-template789',
        'object': 'chat.completion',
        'created': 1677858242,
        'model': 'gpt-3.5-turbo',
        'choices': [
            {
                'message': {
                    'role': 'assistant',
                    'content': 'initial_response_residential'
                },
                'finish_reason': 'stop',
                'index': 0
            }
        ]
    }
}

# Mock Gmail API Responses
MOCK_GMAIL_RESPONSES = {
    'send_success': {
        'id': '18b2c3d4e5f6g7h8',
        'threadId': '18b2c3d4e5f6g7h8',
        'labelIds': ['SENT']
    },
    
    'send_error': {
        'error': {
            'code': 403,
            'message': 'Daily sending quota exceeded',
            'status': 'PERMISSION_DENIED'
        }
    },
    
    'auth_success': {
        'access_token': 'ya29.test-access-token',
        'expires_in': 3600,
        'refresh_token': 'test-refresh-token',
        'scope': 'https://www.googleapis.com/auth/gmail.send',
        'token_type': 'Bearer'
    },
    
    'auth_error': {
        'error': 'invalid_grant',
        'error_description': 'Token has been expired or revoked.'
    }
}

# Test Database Configuration
TEST_DATABASE_CONFIG = {
    'url': 'sqlite:///:memory:',
    'echo': False,
    'pool_pre_ping': True,
    'connect_args': {
        'check_same_thread': False
    }
}

# Test Settings
TEST_SETTINGS = {
    'email': {
        'max_retries': 3,
        'retry_delay': 1,
        'batch_size': 10,
        'rate_limit_per_minute': 60,
        'timeout': 30
    },
    'openai': {
        'model': 'gpt-3.5-turbo',
        'max_tokens': 500,
        'temperature': 0.7,
        'timeout': 30,
        'max_retries': 3
    },
    'lead_processing': {
        'min_score_threshold': 50,
        'high_priority_score': 80,
        'urgent_keywords': ['asap', 'urgent', 'emergency', 'immediate'],
        'commercial_indicators': ['office', 'business', 'commercial', 'retail']
    },
    'logging': {
        'level': 'DEBUG',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': '/tmp/test_claw_contractor.log'
    }
}

# Helper Functions for Test Setup and Teardown
class TestHelper:
    """Helper class for test setup and teardown operations"""
    
    @staticmethod
    def setup_environment_variables():
        """Set up test environment variables"""
        for key, value in TEST_ENV_VARS.items():
            os.environ[key] = value
    
    @staticmethod
    def cleanup_environment_variables():
        """Clean up test environment variables"""
        for key in TEST_ENV_VARS.keys():
            os.environ.pop(key, None)
    
    @staticmethod
    def create_mock_openai_client(response_type: str = 'email_generation_success'):
        """Create a mock OpenAI client with predefined responses"""
        mock_client = MagicMock()
        
        if response_type in MOCK_OPENAI_RESPONSES:
            if 'error' in MOCK_OPENAI_RESPONSES[response_type]:
                mock_client.chat.completions.create.side_effect = Exception(
                    MOCK_OPENAI_RESPONSES[response_type]['error']['message']
                )
            else:
                mock_response = MagicMock()
                mock_response.model_dump.return_value = MOCK_OPENAI_RESPONSES[response_type]
                mock_response.choices[0].message.content = MOCK_OPENAI_RESPONSES[response_type]['choices'][0]['message']['content']
                mock_client.chat.completions.create.return_value = mock_response
        
        return mock_client
    
    @staticmethod
    def create_mock_gmail_service(response_type: str = 'send_success'):
        """Create a mock Gmail service with predefined responses"""
        mock_service = MagicMock()
        
        if response_type == 'send_success':
            mock_service.users().messages().send().execute.return_value = MOCK_GMAIL_RESPONSES['send_success']
        elif response_type == 'send_error':
            mock_service.users().messages().send().execute.side_effect = Exception(
                MOCK_GMAIL_RESPONSES['send_error']['error']['message']
            )
        
        return mock_service
    
    @staticmethod
    def get_mock_lead_data(scenario: str) -> Dict[str, Any]:
        """Get mock lead data for a specific scenario"""
        if scenario not in MOCK_LEAD_DATA:
            raise ValueError(f"Unknown scenario: {scenario}")
        return MOCK_LEAD_DATA[scenario].copy()
    
    @staticmethod
    def get_sample_email_template(template_type: str) -> Dict[str, str]:
        """Get a sample email template"""
        if template_type not in SAMPLE_EMAIL_TEMPLATES:
            raise ValueError(f"Unknown template type: {template_type}")
        return SAMPLE_EMAIL_TEMPLATES[template_type].copy()
    
    @staticmethod
    def create_test_database_session():
        """Create an in-memory database session for testing"""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        engine = create_engine(TEST_DATABASE_CONFIG['url'], **{
            k: v for k, v in TEST_DATABASE_CONFIG.items() if k != 'url'
        })
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return SessionLocal()
    
    @staticmethod
    def setup_test_logging():
        """Set up logging for tests"""
        import logging
        
        logging.basicConfig(
            level=getattr(logging, TEST_SETTINGS['logging']['level']),
            format=TEST_SETTINGS['logging']['format']
        )
        
        # Create a test-specific logger
        logger = logging.getLogger('test_claw_contractor')
        logger.setLevel(logging.DEBUG)
        
        return logger
    
    @staticmethod
    def cleanup_test_files():
        """Clean up any test files created during testing"""
        import glob
        
        test_files = [
            '/tmp/test_claw_contractor.log',
            '/tmp/test_*.db',
            '/tmp/claw_test_*'
        ]
        
        for pattern in test_files:
            for file_path in glob.glob(pattern):
                try:
                    os.remove(file_path)
                except OSError:
                    pass
    
    @staticmethod
    def validate_email_content(content: str, lead_data: Dict[str, Any]) -> bool:
        """Validate that email content contains expected lead information"""
        required_fields = ['name', 'project_type', 'project_description']
        
        for field in required_fields:
            if field in lead_data and str(lead_data[field]) not in content:
                return False
        
        return True
    
    @staticmethod
    def create_test_lead_batch(count: int = 5) -> List[Dict[str, Any]]:
        """Create a batch of test leads for bulk operations"""
        scenarios = list(MOCK_LEAD_DATA.keys())
        leads = []
        
        for i in range(count):
            scenario = scenarios[i % len(scenarios)]
            lead = MOCK_LEAD_DATA[scenario].copy()
            lead['id'] = f"test_lead_{i+1:03d}"
            lead['email'] = f"testlead{i+1}@example.com"
            leads.append(lead)
        
        return leads
    
    @staticmethod
    def assert_email_format(email_data: Dict[str, Any]) -> bool:
        """Assert that email data has proper format"""
        required_keys = ['to', 'subject', 'body']
        return all(key in email_data for key in required_keys)

# Test Data Validation Functions
def validate_lead_data(lead_data: Dict[str, Any]) -> bool:
    """Validate that lead data contains required fields"""
    required_fields = [
        'id', 'name', 'email', 'project_type', 'property_type',
        'project_description', 'budget_range', 'timeline', 'status'
    ]
    
    return all(field in lead_data for field in required_fields)

def validate_email_template(template: Dict[str, str]) -> bool:
    """Validate that email template has required structure"""
    required_keys = ['subject', 'template']
    return all(key in template for key in required_keys)

# Test Fixtures Factory
class TestFixtures:
    """Factory class for creating test fixtures"""
    
    @classmethod
    def create_lead_with_custom_data(cls, **kwargs) -> Dict[str, Any]:
        """Create a lead with custom data merged with base data"""
        base_lead = MOCK_LEAD_DATA['new_residential_kitchen'].copy()
        base_lead.update(kwargs)
        return base_lead
    
    @classmethod
    def create_email_template_with_custom_data(cls, base_template: str, **kwargs) -> Dict[str, str]:
        """Create an email template with custom data"""
        template = SAMPLE_EMAIL_TEMPLATES[base_template].copy()
        template.update(kwargs)
        return template

# Export all test configuration for easy importing
__all__ = [
    'TEST_ENV_VARS',
    'MOCK_LEAD_DATA',
    'SAMPLE_EMAIL_TEMPLATES',
    'MOCK_OPENAI_RESPONSES',
    'MOCK_GMAIL_RESPONSES',
    'TEST_DATABASE_CONFIG',
    'TEST_SETTINGS',
    'TestHelper',
    'validate_lead_data',
    'validate_email_template',
    'TestFixtures'
]