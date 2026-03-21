import pytest
import asyncio
import os
import json
import tempfile
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

from claw_contractor.main import ClawContractor
from claw_contractor.gmail_client import GmailClient
from claw_contractor.lead_qualifier import LeadQualifier
from claw_contractor.photo_analyzer import PhotoAnalyzer
from claw_contractor.contractor_matcher import ContractorMatcher
from claw_contractor.notification_sender import NotificationSender


class TestE2EGmailIntegration:
    """End-to-end tests for Gmail integration"""
    
    @pytest.fixture
    def mock_gmail_service(self):
        service = Mock()
        service.users().messages().list().execute.return_value = {
            'messages': [
                {'id': 'msg_001', 'threadId': 'thread_001'},
                {'id': 'msg_002', 'threadId': 'thread_002'}
            ]
        }
        
        # Mock message details
        message_data = {
            'id': 'msg_001',
            'threadId': 'thread_001',
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'customer@example.com'},
                    {'name': 'Subject', 'value': 'Deck repair needed'},
                    {'name': 'Date', 'value': 'Wed, 15 Nov 2023 10:30:00 -0800'}
                ],
                'body': {
                    'data': base64.urlsafe_b64encode(
                        b"Hi, I need my deck repaired. It has some loose boards and the railing is wobbly."
                    ).decode()
                },
                'parts': [
                    {
                        'filename': 'deck_damage.jpg',
                        'body': {
                            'attachmentId': 'att_001'
                        },
                        'mimeType': 'image/jpeg'
                    }
                ]
            }
        }
        
        service.users().messages().get().execute.return_value = message_data
        service.users().messages().attachments().get().execute.return_value = {
            'data': base64.urlsafe_b64encode(b'fake_image_data').decode()
        }
        
        return service

    @pytest.fixture
    def gmail_client(self, mock_gmail_service):
        with patch('claw_contractor.gmail_client.build', return_value=mock_gmail_service):
            client = GmailClient()
            client.authenticate()
            return client

    @pytest.mark.asyncio
    async def test_full_gmail_message_processing(self, gmail_client, mock_gmail_service):
        """Test complete Gmail message retrieval and processing"""
        # Test message listing
        messages = await gmail_client.get_unread_messages()
        assert len(messages) == 2
        assert messages[0]['id'] == 'msg_001'
        
        # Test message details retrieval
        message_details = await gmail_client.get_message_details('msg_001')
        assert message_details['from'] == 'customer@example.com'
        assert message_details['subject'] == 'Deck repair needed'
        assert 'deck repaired' in message_details['body']
        
        # Test attachment processing
        attachments = await gmail_client.get_message_attachments('msg_001')
        assert len(attachments) == 1
        assert attachments[0]['filename'] == 'deck_damage.jpg'
        assert attachments[0]['data'] is not None

    @pytest.mark.asyncio
    async def test_gmail_error_handling(self, gmail_client):
        """Test Gmail API error scenarios"""
        with patch.object(gmail_client.service.users().messages(), 'list') as mock_list:
            # Test API timeout
            mock_list().execute.side_effect = TimeoutError("Request timed out")
            
            messages = await gmail_client.get_unread_messages()
            assert messages == []
            
            # Test API rate limiting
            from googleapiclient.errors import HttpError
            mock_list().execute.side_effect = HttpError(
                resp=Mock(status=429), 
                content=b'Rate limit exceeded'
            )
            
            messages = await gmail_client.get_unread_messages()
            assert messages == []


class TestE2ELeadQualificationWorkflow:
    """End-to-end tests for complete lead qualification workflow"""
    
    @pytest.fixture
    def sample_lead_data(self):
        return {
            'email': 'john.doe@example.com',
            'subject': 'Deck replacement needed',
            'body': 'Hi, I need my old deck completely replaced. It\'s about 20x15 feet and I\'d like composite materials.',
            'attachments': [
                {
                    'filename': 'current_deck.jpg',
                    'data': b'fake_image_data',
                    'mime_type': 'image/jpeg'
                }
            ],
            'timestamp': datetime.now()
        }

    @pytest.fixture
    def lead_qualifier(self):
        return LeadQualifier()

    @pytest.fixture  
    def photo_analyzer(self):
        return PhotoAnalyzer()

    @pytest.fixture
    def contractor_matcher(self):
        return ContractorMatcher()

    @pytest.fixture
    def notification_sender(self):
        return NotificationSender()

    @pytest.mark.asyncio
    async def test_complete_qualification_workflow(self, sample_lead_data, lead_qualifier, 
                                                  photo_analyzer, contractor_matcher, notification_sender):
        """Test full 6-step lead qualification process"""
        
        # Step 1: Initial contact classification
        classification = await lead_qualifier.classify_inquiry(sample_lead_data['body'])
        assert classification['service_type'] == 'deck_repair'
        assert classification['urgency'] == 'medium'
        assert classification['confidence'] > 0.8
        
        # Step 2: Photo analysis
        with patch.object(photo_analyzer, 'analyze_image') as mock_analyze:
            mock_analyze.return_value = {
                'damage_type': 'structural_replacement_needed',
                'severity': 'high',
                'estimated_scope': 'full_replacement',
                'materials_visible': ['wood', 'deteriorated_boards'],
                'confidence': 0.9
            }
            
            photo_analysis = await photo_analyzer.process_attachments(sample_lead_data['attachments'])
            assert photo_analysis[0]['damage_type'] == 'structural_replacement_needed'
            assert photo_analysis[0]['severity'] == 'high'
        
        # Step 3: Budget estimation
        budget_estimate = await lead_qualifier.estimate_project_budget(
            classification, photo_analysis
        )
        assert budget_estimate['min_cost'] > 0
        assert budget_estimate['max_cost'] > budget_estimate['min_cost']
        assert budget_estimate['materials_cost'] > 0
        
        # Step 4: Timeline assessment
        timeline = await lead_qualifier.assess_project_timeline(
            classification, photo_analysis, budget_estimate
        )
        assert timeline['estimated_duration_days'] > 0
        assert timeline['seasonal_factors'] is not None
        
        # Step 5: Contractor matching
        with patch.object(contractor_matcher, 'find_qualified_contractors') as mock_match:
            mock_contractors = [
                {
                    'id': 'contractor_001',
                    'name': 'Premium Deck Builders',
                    'rating': 4.8,
                    'specialties': ['deck_construction', 'composite_materials'],
                    'availability': 'within_2_weeks',
                    'location_match': 0.95
                }
            ]
            mock_match.return_value = mock_contractors
            
            contractors = await contractor_matcher.match_to_project(
                sample_lead_data, classification, budget_estimate
            )
            assert len(contractors) > 0
            assert contractors[0]['rating'] > 4.5
        
        # Step 6: Final handoff preparation
        handoff_package = await lead_qualifier.prepare_handoff_package(
            sample_lead_data, classification, photo_analysis, 
            budget_estimate, timeline, contractors
        )
        
        assert handoff_package['lead_score'] > 0.7
        assert handoff_package['recommended_contractors'] == contractors
        assert 'project_summary' in handoff_package
        assert 'next_steps' in handoff_package

    @pytest.mark.asyncio
    async def test_qualification_edge_cases(self, lead_qualifier):
        """Test edge cases in lead qualification"""
        
        # Test with minimal information
        minimal_lead = {
            'body': 'need help',
            'attachments': []
        }
        
        classification = await lead_qualifier.classify_inquiry(minimal_lead['body'])
        assert classification['confidence'] < 0.5
        assert classification['service_type'] == 'unknown'
        
        # Test with ambiguous request
        ambiguous_lead = {
            'body': 'Something is broken outside, can you fix it?',
            'attachments': []
        }
        
        classification = await lead_qualifier.classify_inquiry(ambiguous_lead['body'])
        assert classification['requires_clarification'] is True
        
        # Test with multiple service types
        complex_lead = {
            'body': 'I need my deck repaired and also some roofing work done',
            'attachments': []
        }
        
        classification = await lead_qualifier.classify_inquiry(complex_lead['body'])
        assert len(classification['service_types']) > 1


class TestE2EPhotoAnalysis:
    """End-to-end tests for photo analysis and attachment processing"""
    
    @pytest.fixture
    def sample_images(self):
        """Generate sample image data for testing"""
        # Create simple test images
        images = {}
        
        # Simulate different image types
        for image_type in ['deck_damage', 'roof_issue', 'foundation_crack']:
            # In real implementation, this would be actual image data
            images[image_type] = {
                'filename': f'{image_type}.jpg',
                'data': f'fake_{image_type}_data'.encode(),
                'mime_type': 'image/jpeg'
            }
        
        return images

    @pytest.fixture
    def photo_analyzer(self):
        return PhotoAnalyzer()

    @pytest.mark.asyncio
    async def test_image_analysis_workflow(self, photo_analyzer, sample_images):
        """Test complete image analysis workflow"""
        
        # Mock computer vision API responses
        mock_responses = {
            'deck_damage': {
                'damage_type': 'wood_rot',
                'severity': 'moderate', 
                'location': 'support_beams',
                'materials_detected': ['pressure_treated_lumber', 'composite_decking'],
                'safety_concerns': ['structural_integrity'],
                'confidence': 0.85
            },
            'roof_issue': {
                'damage_type': 'missing_shingles',
                'severity': 'high',
                'location': 'southwest_section', 
                'materials_detected': ['asphalt_shingles', 'flashing'],
                'safety_concerns': ['water_damage_risk'],
                'confidence': 0.92
            }
        }
        
        with patch.object(photo_analyzer, 'analyze_image') as mock_analyze:
            def side_effect(image_data, filename):
                if 'deck_damage' in filename:
                    return mock_responses['deck_damage']
                elif 'roof_issue' in filename:
                    return mock_responses['roof_issue']
                else:
                    return {'damage_type': 'unknown', 'confidence': 0.3}
            
            mock_analyze.side_effect = side_effect
            
            # Test batch processing
            attachments = list(sample_images.values())[:2]  # Test first two images
            results = await photo_analyzer.process_attachments(attachments)
            
            assert len(results) == 2
            assert results[0]['confidence'] > 0.8
            assert results[1]['confidence'] > 0.8
            assert 'damage_type' in results[0]
            assert 'safety_concerns' in results[1]

    @pytest.mark.asyncio
    async def test_image_processing_error_handling(self, photo_analyzer):
        """Test error scenarios in image processing"""
        
        # Test corrupted image data
        corrupted_image = {
            'filename': 'corrupted.jpg',
            'data': b'invalid_image_data',
            'mime_type': 'image/jpeg'
        }
        
        with patch.object(photo_analyzer, 'analyze_image') as mock_analyze:
            mock_analyze.side_effect = ValueError("Invalid image format")
            
            results = await photo_analyzer.process_attachments([corrupted_image])
            assert len(results) == 1
            assert results[0]['error'] is not None
            assert results[0]['confidence'] == 0.0
        
        # Test API timeout
        timeout_image = {
            'filename': 'timeout.jpg', 
            'data': b'valid_image_data',
            'mime_type': 'image/jpeg'
        }
        
        with patch.object(photo_analyzer, 'analyze_image') as mock_analyze:
            mock_analyze.side_effect = asyncio.TimeoutError("Analysis timed out")
            
            results = await photo_analyzer.process_attachments([timeout_image])
            assert results[0]['error'] == 'timeout'

    @pytest.mark.asyncio
    async def test_multi_format_image_support(self, photo_analyzer):
        """Test support for different image formats"""
        
        image_formats = [
            {'filename': 'test.jpg', 'mime_type': 'image/jpeg'},
            {'filename': 'test.png', 'mime_type': 'image/png'},
            {'filename': 'test.webp', 'mime_type': 'image/webp'},
            {'filename': 'test.gif', 'mime_type': 'image/gif'},
            {'filename': 'test.bmp', 'mime_type': 'image/bmp'}
        ]
        
        with patch.object(photo_analyzer, 'analyze_image') as mock_analyze:
            mock_analyze.return_value = {'damage_type': 'test', 'confidence': 0.9}
            
            for img_format in image_formats:
                img_format['data'] = b'test_data'
                results = await photo_analyzer.process_attachments([img_format])
                
                if img_format['mime_type'] in photo_analyzer.SUPPORTED_FORMATS:
                    assert results[0]['confidence'] > 0
                else:
                    assert 'unsupported_format' in results[0].get('error', '')


class TestE2EErrorRecoveryScenarios:
    """End-to-end tests for error recovery and resilience"""
    
    @pytest.fixture
    def claw_contractor(self):
        return ClawContractor()

    @pytest.mark.asyncio
    async def test_api_failure_recovery(self, claw_contractor):
        """Test recovery from various API failures"""
        
        # Test Gmail API failure
        with patch.object(claw_contractor.gmail_client, 'get_unread_messages') as mock_gmail:
            mock_gmail.side_effect = Exception("Gmail API unavailable")
            
            # Should continue processing with empty message list
            result = await claw_contractor.process_new_leads()
            assert result['processed_count'] == 0
            assert result['errors']['gmail_failures'] == 1
        
        # Test OpenAI API failure
        with patch.object(claw_contractor.lead_qualifier, 'classify_inquiry') as mock_classify:
            mock_classify.side_effect = Exception("OpenAI API rate limited")
            
            sample_lead = {
                'email': 'test@example.com',
                'body': 'Need deck repair',
                'attachments': []
            }
            
            # Should fallback to basic classification
            result = await claw_contractor.process_lead(sample_lead)
            assert result['status'] == 'partial_processing'
            assert 'classification_fallback' in result

    @pytest.mark.asyncio
    async def test_network_timeout_handling(self, claw_contractor):
        """Test handling of network timeouts"""
        
        # Mock network timeout scenarios
        timeout_scenarios = [
            ('gmail_timeout', asyncio.TimeoutError("Gmail request timed out")),
            ('openai_timeout', asyncio.TimeoutError("OpenAI request timed out")),
            ('vision_timeout', asyncio.TimeoutError("Vision API timed out"))
        ]
        
        for scenario_name, exception in timeout_scenarios:
            if 'gmail' in scenario_name:
                with patch.object(claw_contractor.gmail_client, 'get_unread_messages', 
                                side_effect=exception):
                    result = await claw_contractor.process_new_leads()
                    assert 'timeout' in result['errors']
            
            elif 'openai' in scenario_name:
                with patch.object(claw_contractor.lead_qualifier, 'classify_inquiry',
                                side_effect=exception):
                    sample_lead = {'body': 'test', 'attachments': []}
                    result = await claw_contractor.process_lead(sample_lead)
                    assert result['status'] == 'timeout_retry_needed'

    @pytest.mark.asyncio
    async def test_invalid_response_handling(self, claw_contractor):
        """Test handling of invalid API responses"""
        
        # Test malformed Gmail response
        with patch.object(claw_contractor.gmail_client, 'get_message_details') as mock_details:
            mock_details.return_value = {'invalid': 'response_format'}
            
            result = await claw_contractor.process_message('msg_001')
            assert result['status'] == 'parsing_error'
            assert 'invalid_response' in result['errors']
        
        # Test malformed OpenAI response
        with patch.object(claw_contractor.lead_qualifier, 'classify_inquiry') as mock_classify:
            mock_classify.return_value = "not_a_dict_response"
            
            sample_lead = {'body': 'test inquiry', 'attachments': []}
            result = await claw_contractor.process_lead(sample_lead)
            assert 'response_parsing_error' in result['errors']

    @pytest.mark.asyncio
    async def test_partial_failure_recovery(self, claw_contractor):
        """Test recovery from partial system failures"""
        
        # Simulate scenario where some components work, others fail
        sample_lead = {
            'email': 'customer@example.com',
            'body': 'Need urgent deck repair',
            'attachments': [{'filename': 'damage.jpg', 'data': b'image_data'}]
        }
        
        # Gmail works, classification fails, photo analysis works
        with patch.object(claw_contractor.lead_qualifier, 'classify_inquiry', 
                         side_effect=Exception("Classification failed")), \
             patch.object(claw_contractor.photo_analyzer, 'process_attachments',
                         return_value=[{'damage_type': 'severe', 'confidence': 0.9}]):
            
            result = await claw_contractor.process_lead(sample_lead)
            
            # Should complete with partial results
            assert result['status'] == 'partially_processed'
            assert result['photo_analysis_completed'] is True
            assert result['classification_completed'] is False
            assert 'fallback_actions_taken' in result


class TestE2EMockLeadData:
    """End-to-end tests using comprehensive mock lead data"""
    
    @pytest.fixture
    def mock_lead_scenarios(self):
        """Comprehensive mock lead data covering various scenarios"""
        return {
            'high_value_deck_replacement': {
                'email': 'wealthy.homeowner@mansion.com',
                'subject': 'Premium deck replacement - budget $50k+',
                'body': '''Hi, I need to replace my existing deck with high-end materials. 
                          The current deck is 30x20 feet with a lower level. I'm interested in 
                          composite materials with built-in lighting and a pergola. 
                          Timeline is flexible, budget is $50,000-$75,000.''',
                'attachments': [
                    {'filename': 'current_deck_1.jpg', 'data': b'deck_overview_data'},
                    {'filename': 'current_deck_2.jpg', 'data': b'deck_detail_data'},
                    {'filename': 'inspiration.jpg', 'data': b'desired_design_data'}
                ],
                'expected_classification': {
                    'service_type': 'deck_replacement',
                    'urgency': 'low',
                    'budget_range': 'high',
                    'lead_quality': 'premium'
                }
            },
            
            'urgent_safety_repair': {
                'email': 'concerned.parent@family.com', 
                'subject': 'URGENT: Deck safety issue with kids',
                'body': '''URGENT - My deck railing just broke and I have small children. 
                          One of the support posts is loose and the whole railing section 
                          is wobbly. Need someone ASAP to make it safe. Insurance may cover.''',
                'attachments': [
                    {'filename': 'broken_railing.jpg', 'data': b'safety_hazard_data'}
                ],
                'expected_classification': {
                    'service_type': 'deck_repair',
                    'urgency': 'emergency',
                    'safety_concern': True,
                    'lead_quality': 'high'
                }
            },
            
            'budget_conscious_repair': {
                'email': 'thrifty.homeowner@budget.com',
                'subject': 'Cheap deck repair options?',
                'body': '''Hi, my deck has some issues but I'm on a tight budget. 
                          Some boards are loose and there's some minor rot. 
                          What's the cheapest way to fix this? Can I do some myself?''',
                'attachments': [],
                'expected_classification': {
                    'service_type': 'deck_repair', 
                    'urgency': 'low',
                    'budget_range': 'low',
                    'lead_quality': 'medium'
                }
            },
            
            'commercial_project': {
                'email': 'facilities@bigcompany.com',
                'subject': 'Office building deck renovation - RFQ',
                'body': '''We need quotes for renovating the outdoor deck area at our 
                          office building. This is a commercial project requiring licensed 
                          contractors with commercial insurance. Deck is approximately 
                          1000 sq ft. Please provide formal quote with timeline.''',
                'attachments': [
                    {'filename': 'site_plans.pdf', 'data': b'architectural_plans'},
                    {'filename': 'current_condition.jpg', 'data': b'commercial_deck_photo'}
                ],
                'expected_classification': {
                    'service_type': 'deck_renovation',
                    'project_type': 'commercial',
                    'urgency': 'medium', 
                    'lead_quality': 'high'
                }
            },
            
            'unclear_request': {
                'email': 'confused.customer@unclear.com',
                'subject': 'Outside thing broken',
                'body': 'Something outside is broken. Can you fix?',
                'attachments': [],
                'expected_classification': {
                    'service_type': 'unknown',
                    'urgency': 'unknown',
                    'requires_clarification': True,
                    'lead_quality': 'low'
                }
            }
        }

    @pytest.mark.asyncio
    async def test_mock_lead_processing(self, mock_lead_scenarios):
        """Test processing of various mock lead scenarios"""
        
        claw_contractor = ClawContractor()
        
        for scenario_name, lead_data in mock_lead_scenarios.items():
            print(f"Testing scenario: {scenario_name}")
            
            # Mock the various service responses based on scenario
            with patch.object(claw_contractor.lead_qualifier, 'classify_inquiry') as mock_classify, \
                 patch.object(claw_contractor.photo_analyzer, 'process_attachments') as mock_photos, \
                 patch.object(claw_contractor.contractor_matcher, 'match_to_project') as mock_match:
                
                # Set up expected responses
                mock_classify.return_value = lead_data['expected_classification']
                
                if lead_data['attachments']:
                    mock_photos.return_value = [
                        {'damage_type': 'varies', 'confidence': 0.8, 'filename': att['filename']}
                        for att in lead_data['attachments']
                    ]
                else:
                    mock_photos.return_value = []
                
                # Mock contractor matching based on lead quality
                if lead_data['expected_classification']['lead_quality'] == 'premium':
                    mock_match.return_value = [
                        {'id': 'premium_contractor', 'rating': 4.9, 'specialties': ['luxury_builds']}
                    ]
                elif lead_data['expected_classification']['lead_quality'] == 'high':
                    mock_match.return_value = [
                        {'id': 'quality_contractor', 'rating': 4.7, 'specialties': ['safety_repairs']}
                    ]
                else:
                    mock_match.return_value = [
                        {'id': 'standard_contractor', 'rating': 4.2, 'specialties': ['basic_repairs']}
                    ]
                
                # Process the lead
                result = await claw_contractor.process_lead(lead_data)
                
                # Verify results match expectations
                assert result['classification']['service_type'] == lead_data['expected_classification']['service_type']
                assert result['classification']['urgency'] == lead_data['expected_classification']['urgency']
                
                if lead_data['expected_classification'].get('requires_clarification'):
                    assert result['status'] == 'needs_clarification'
                else:
                    assert result['status'] in ['completed', 'partially_processed']

    @pytest.mark.asyncio
    async def test_lead_scoring_accuracy(self, mock_lead_scenarios):
        """Test accuracy of lead scoring across different scenarios"""
        
        lead_qualifier = LeadQualifier()
        
        for scenario_name, lead_data in mock_lead_scenarios.items():
            with patch.object(lead_qualifier, 'classify_inquiry') as mock_classify:
                mock_classify.return_value = lead_data['expected_classification']
                
                score = await lead_qualifier.calculate_lead_score(
                    lead_data, lead_data['expected_classification']
                )
                
                # Verify scoring aligns with expectations
                if lead_data['expected_classification']['lead_quality'] == 'premium':
                    assert score > 0.9
                elif lead_data['expected_classification']['lead_quality'] == 'high':
                    assert 0.7 <= score <= 0.9
                elif lead_data['expected_classification']['lead_quality'] == 'medium':
                    assert 0.5 <= score <= 0.7
                else:  # low quality
                    assert score < 0.5


class TestE2EEmailFormattingAndNotification:
    """End-to-end tests for email formatting and contractor notifications"""
    
    @pytest.fixture
    def notification_sender(self):
        return NotificationSender()

    @pytest.fixture
    def sample_handoff_data(self):
        return {
            'lead_info': {
                'email': 'customer@example.com',
                'name': 'John Smith',
                'phone': '555-0123',
                'address': '123 Main St, Anytown USA'
            },
            'project_details': {
                'service_type': 'deck_replacement',
                'description': 'Full deck replacement with composite materials',
                'budget_range': '$40,000 - $60,000',
                'timeline': 'Within 3 months',
                'urgency': 'medium'
            },
            'analysis_results': {
                'photo_analysis': [
                    {
                        'damage_type': 'structural_deterioration',
                        'severity': 'high', 
                        'confidence': 0.92
                    }
                ],
                'lead_score': 0.85,
                'qualification_notes': 'High-value lead with clear project scope'
            },
            'contractor_info': {
                'id': 'contractor_001',
                'name': 'Premium Deck Builders',
                'email': 'contact@premiumdecks.com',
                'phone': '555-DECKS',
                'specialties': ['deck_construction', 'composite_materials']
            }
        }

    @pytest.mark.asyncio
    async def test_contractor_notification_formatting(self, notification_sender, sample_handoff_data):
        """Test proper formatting of contractor notification emails"""
        
        # Generate contractor notification
        notification = await notification_sender.format_contractor_notification(sample_handoff_data)
        
        # Verify email structure
        assert notification['to'] == sample_handoff_data['contractor_info']['email']
        assert 'New Qualified Lead' in notification['subject']
        assert sample_handoff_data['project_details']['service_type'] in notification['subject']
        
        # Verify email content includes all key information
        body = notification['body']
        assert sample_handoff_data['lead_info']['name'] in body
        assert sample_handoff_data['lead_info']['email'] in body
        assert sample_handoff_data['project_details']['budget_range'] in body
        assert sample_handoff_data['project_details']['description'] in body
        assert f"{sample_handoff_data['analysis_results']['lead_score']:.1%}" in body
        
        # Verify attachments are included
        assert 'attachments' in notification
        assert len(notification['attachments']) > 0
        
        # Verify professional formatting
        assert notification['format'] == 'html'
        assert '<html>' in body
        assert 'style=' in body  # CSS styling included

    @pytest.mark.asyncio
    async def test_customer_confirmation_email(self, notification_sender, sample_handoff_data):
        """Test customer confirmation email formatting"""
        
        confirmation = await notification_sender.format_customer_confirmation(sample_handoff_data)
        
        # Verify customer email structure
        assert confirmation['to'] == sample_handoff_data['lead_info']['email']
        assert 'received' in confirmation['subject'].lower()
        assert 'contractor' in confirmation['subject'].lower()
        
        body = confirmation['body']
        assert sample_handoff_data['lead_info']['name'] in body
        assert sample_handoff_data['contractor_info']['name'] in body
        assert sample_handoff_data['contractor_info']['phone