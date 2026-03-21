import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.modules.qualified_lead_detector import (
    QualifiedLeadDetector,
    LeadQualificationResult,
    QualificationStatus,
    LeadScore,
    ConversationState,
    PhotoAnalysisResult
)
from app.database.models import Lead, User, ConversationHistory
from app.modules.exceptions import (
    QualificationError,
    DatabaseError,
    PhotoAnalysisError
)


class TestQualifiedLeadDetector:
    """Comprehensive tests for the qualified lead detector module."""
    
    @pytest.fixture
    def detector(self):
        """Create a QualifiedLeadDetector instance for testing."""
        return QualifiedLeadDetector()
    
    @pytest.fixture
    def sample_complete_lead_data(self):
        """Sample data for a fully qualified lead."""
        return {
            'user_id': 'user123',
            'name': 'John Smith',
            'email': 'john.smith@example.com',
            'phone': '+1234567890',
            'location': {
                'address': '123 Main St',
                'city': 'New York',
                'state': 'NY',
                'zip_code': '10001',
                'coordinates': {'lat': 40.7128, 'lng': -74.0060}
            },
            'project_details': {
                'project_type': 'kitchen_remodel',
                'budget_range': '$15000-$25000',
                'timeline': 'within_3_months',
                'description': 'Complete kitchen renovation including cabinets, countertops, and appliances',
                'square_footage': 200
            },
            'photos': [
                {'url': 'photo1.jpg', 'analysis_complete': True},
                {'url': 'photo2.jpg', 'analysis_complete': True}
            ],
            'conversation_history': [
                {'message': 'I need a kitchen remodel', 'timestamp': datetime.utcnow()},
                {'message': 'My budget is around $20k', 'timestamp': datetime.utcnow()}
            ],
            'engagement_score': 85,
            'response_time_avg': 15.5,
            'session_duration': 1200
        }
    
    @pytest.fixture
    def sample_incomplete_lead_data(self):
        """Sample data for an incomplete lead."""
        return {
            'user_id': 'user456',
            'name': 'Jane Doe',
            'location': {
                'city': 'Los Angeles',
                'state': 'CA'
            },
            'project_details': {
                'project_type': 'bathroom_remodel'
            },
            'engagement_score': 45
        }
    
    @pytest.fixture
    def mock_database(self):
        """Mock database connection."""
        with patch('app.modules.qualified_lead_detector.get_database') as mock_db:
            mock_db.return_value.leads.find_one = AsyncMock()
            mock_db.return_value.leads.update_one = AsyncMock()
            mock_db.return_value.conversation_history.find = AsyncMock()
            yield mock_db.return_value


class TestFullyQualifiedLeads:
    """Test detection of fully qualified leads with all required data."""
    
    def test_detect_fully_qualified_lead_success(self, detector, sample_complete_lead_data):
        """Test successful detection of a fully qualified lead."""
        result = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        assert result.status == QualificationStatus.QUALIFIED
        assert result.score.overall >= 80
        assert result.completeness_percentage >= 90
        assert len(result.missing_elements) == 0
        assert result.confidence_level == 'high'
        assert result.ready_for_handoff is True
    
    def test_qualified_lead_with_high_engagement(self, detector, sample_complete_lead_data):
        """Test qualified lead with high engagement metrics."""
        sample_complete_lead_data['engagement_score'] = 95
        sample_complete_lead_data['response_time_avg'] = 8.0
        sample_complete_lead_data['session_duration'] = 1800
        
        result = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        assert result.status == QualificationStatus.QUALIFIED
        assert result.score.engagement >= 90
        assert result.score.overall >= 85
        assert 'high_engagement' in result.qualification_tags
    
    def test_qualified_lead_with_premium_budget(self, detector, sample_complete_lead_data):
        """Test qualified lead with premium budget range."""
        sample_complete_lead_data['project_details']['budget_range'] = '$50000-$100000'
        
        result = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        assert result.status == QualificationStatus.QUALIFIED
        assert result.score.budget >= 85
        assert 'premium_budget' in result.qualification_tags
    
    def test_qualified_lead_with_urgent_timeline(self, detector, sample_complete_lead_data):
        """Test qualified lead with urgent timeline."""
        sample_complete_lead_data['project_details']['timeline'] = 'within_1_month'
        
        result = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        assert result.status == QualificationStatus.QUALIFIED
        assert result.score.timeline >= 90
        assert 'urgent_timeline' in result.qualification_tags
    
    def test_qualified_lead_scoring_breakdown(self, detector, sample_complete_lead_data):
        """Test detailed scoring breakdown for qualified leads."""
        result = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        assert isinstance(result.score, LeadScore)
        assert result.score.contact_info >= 80
        assert result.score.project_details >= 70
        assert result.score.engagement >= 60
        assert result.score.budget >= 70
        assert result.score.timeline >= 60
        assert result.score.location >= 80


class TestIncompleteLeads:
    """Test detection of incomplete leads missing various qualification elements."""
    
    def test_lead_missing_contact_info(self, detector, sample_complete_lead_data):
        """Test lead missing essential contact information."""
        del sample_complete_lead_data['email']
        del sample_complete_lead_data['phone']
        
        result = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        assert result.status == QualificationStatus.NEEDS_NURTURING
        assert 'email' in result.missing_elements
        assert 'phone' in result.missing_elements
        assert result.score.contact_info < 60
        assert result.ready_for_handoff is False
    
    def test_lead_missing_project_details(self, detector, sample_incomplete_lead_data):
        """Test lead missing critical project details."""
        result = detector.analyze_lead_qualification(sample_incomplete_lead_data)
        
        assert result.status in [QualificationStatus.NEEDS_NURTURING, QualificationStatus.UNQUALIFIED]
        assert 'budget_range' in result.missing_elements
        assert 'timeline' in result.missing_elements
        assert 'project_description' in result.missing_elements
        assert result.score.project_details < 50
    
    def test_lead_missing_location_data(self, detector, sample_complete_lead_data):
        """Test lead missing location information."""
        sample_complete_lead_data['location'] = {'city': 'Unknown'}
        
        result = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        assert 'complete_address' in result.missing_elements
        assert result.score.location < 70
        assert result.completeness_percentage < 90
    
    def test_lead_with_low_engagement(self, detector, sample_complete_lead_data):
        """Test lead with low engagement metrics."""
        sample_complete_lead_data['engagement_score'] = 25
        sample_complete_lead_data['response_time_avg'] = 300.0
        sample_complete_lead_data['session_duration'] = 30
        
        result = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        assert result.status == QualificationStatus.NEEDS_NURTURING
        assert result.score.engagement < 40
        assert 'low_engagement' in result.qualification_tags
    
    def test_lead_with_no_budget_info(self, detector, sample_complete_lead_data):
        """Test lead missing budget information."""
        del sample_complete_lead_data['project_details']['budget_range']
        
        result = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        assert 'budget_range' in result.missing_elements
        assert result.score.budget < 50
        assert result.status == QualificationStatus.NEEDS_NURTURING
    
    def test_lead_with_vague_timeline(self, detector, sample_complete_lead_data):
        """Test lead with vague or missing timeline."""
        sample_complete_lead_data['project_details']['timeline'] = 'someday'
        
        result = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        assert result.score.timeline < 40
        assert 'vague_timeline' in result.qualification_tags


class TestPhotoAnalysisEdgeCases:
    """Test edge cases with partial photo analysis."""
    
    def test_lead_with_pending_photo_analysis(self, detector, sample_complete_lead_data):
        """Test lead with photos still being analyzed."""
        sample_complete_lead_data['photos'] = [
            {'url': 'photo1.jpg', 'analysis_complete': True},
            {'url': 'photo2.jpg', 'analysis_complete': False, 'analysis_status': 'in_progress'}
        ]
        
        result = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        assert result.status == QualificationStatus.PENDING_ANALYSIS
        assert 'photo_analysis_incomplete' in result.missing_elements
        assert result.ready_for_handoff is False
    
    def test_lead_with_failed_photo_analysis(self, detector, sample_complete_lead_data):
        """Test lead with failed photo analysis."""
        sample_complete_lead_data['photos'] = [
            {'url': 'photo1.jpg', 'analysis_complete': True},
            {'url': 'photo2.jpg', 'analysis_complete': False, 'analysis_status': 'failed'}
        ]
        
        result = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        assert 'photo_analysis_failed' in result.qualification_tags
        assert result.confidence_level in ['medium', 'low']
    
    def test_lead_with_no_photos(self, detector, sample_complete_lead_data):
        """Test lead with no photos provided."""
        del sample_complete_lead_data['photos']
        
        result = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        assert 'photos' in result.missing_elements
        assert result.score.project_details < 80
        assert 'no_photos' in result.qualification_tags
    
    @patch('app.modules.qualified_lead_detector.PhotoAnalysisService')
    def test_photo_analysis_service_error(self, mock_photo_service, detector, sample_complete_lead_data):
        """Test handling of photo analysis service errors."""
        mock_photo_service.analyze_photos.side_effect = PhotoAnalysisError("Service unavailable")
        
        result = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        assert result.status == QualificationStatus.PENDING_ANALYSIS
        assert 'photo_analysis_error' in result.qualification_tags
    
    def test_partial_photo_analysis_results(self, detector, sample_complete_lead_data):
        """Test lead with partial photo analysis results."""
        sample_complete_lead_data['photos'] = [
            {
                'url': 'photo1.jpg',
                'analysis_complete': True,
                'analysis_results': {
                    'room_type': 'kitchen',
                    'condition': 'needs_renovation',
                    'features_detected': ['cabinets', 'countertops']
                }
            },
            {
                'url': 'photo2.jpg',
                'analysis_complete': True,
                'analysis_results': {
                    'room_type': 'unknown',
                    'condition': 'unclear'
                }
            }
        ]
        
        result = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        assert result.status == QualificationStatus.QUALIFIED
        assert result.score.project_details >= 70


class TestConversationStateValidation:
    """Test conversation state validation functionality."""
    
    def test_active_conversation_state(self, detector, sample_complete_lead_data):
        """Test lead with active conversation state."""
        recent_timestamp = datetime.utcnow() - timedelta(minutes=10)
        sample_complete_lead_data['conversation_history'][-1]['timestamp'] = recent_timestamp
        sample_complete_lead_data['last_interaction'] = recent_timestamp
        
        result = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        assert result.conversation_state == ConversationState.ACTIVE
        assert 'active_conversation' in result.qualification_tags
        assert result.priority_level == 'high'
    
    def test_dormant_conversation_state(self, detector, sample_complete_lead_data):
        """Test lead with dormant conversation state."""
        old_timestamp = datetime.utcnow() - timedelta(days=7)
        sample_complete_lead_data['conversation_history'][-1]['timestamp'] = old_timestamp
        sample_complete_lead_data['last_interaction'] = old_timestamp
        
        result = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        assert result.conversation_state == ConversationState.DORMANT
        assert 'dormant_conversation' in result.qualification_tags
        assert result.priority_level == 'medium'
    
    def test_stale_conversation_state(self, detector, sample_complete_lead_data):
        """Test lead with stale conversation state."""
        very_old_timestamp = datetime.utcnow() - timedelta(days=30)
        sample_complete_lead_data['conversation_history'][-1]['timestamp'] = very_old_timestamp
        sample_complete_lead_data['last_interaction'] = very_old_timestamp
        
        result = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        assert result.conversation_state == ConversationState.STALE
        assert result.status == QualificationStatus.UNQUALIFIED
        assert result.priority_level == 'low'
    
    def test_conversation_quality_analysis(self, detector, sample_complete_lead_data):
        """Test conversation quality impact on qualification."""
        high_quality_conversation = [
            {'message': 'I need a complete kitchen renovation', 'timestamp': datetime.utcnow()},
            {'message': 'My budget is $25,000 and I want to start in 2 months', 'timestamp': datetime.utcnow()},
            {'message': 'I live at 123 Main St, New York', 'timestamp': datetime.utcnow()},
            {'message': 'Can you provide a quote?', 'timestamp': datetime.utcnow()}
        ]
        sample_complete_lead_data['conversation_history'] = high_quality_conversation
        
        result = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        assert result.score.engagement >= 80
        assert 'detailed_conversation' in result.qualification_tags
    
    def test_conversation_intent_detection(self, detector, sample_complete_lead_data):
        """Test conversation intent detection and scoring."""
        intent_keywords = [
            {'message': 'I want to hire a contractor immediately', 'timestamp': datetime.utcnow()},
            {'message': 'When can we schedule a consultation?', 'timestamp': datetime.utcnow()},
            {'message': 'I have cash ready for this project', 'timestamp': datetime.utcnow()}
        ]
        sample_complete_lead_data['conversation_history'] = intent_keywords
        
        result = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        assert 'high_purchase_intent' in result.qualification_tags
        assert result.score.engagement >= 85


class TestDatabaseIntegration:
    """Test integration with database lead records."""
    
    @pytest.mark.asyncio
    async def test_analyze_lead_from_database(self, detector, mock_database, sample_complete_lead_data):
        """Test analyzing lead qualification from database record."""
        mock_database.leads.find_one.return_value = sample_complete_lead_data
        
        result = await detector.analyze_lead_from_database('user123')
        
        assert result.status == QualificationStatus.QUALIFIED
        mock_database.leads.find_one.assert_called_once_with({'user_id': 'user123'})
    
    @pytest.mark.asyncio
    async def test_update_qualification_in_database(self, detector, mock_database):
        """Test updating qualification results in database."""
        qualification_result = LeadQualificationResult(
            status=QualificationStatus.QUALIFIED,
            score=LeadScore(overall=85, contact_info=90, project_details=80, engagement=85, budget=80, timeline=75, location=90),
            completeness_percentage=92,
            missing_elements=[],
            confidence_level='high',
            ready_for_handoff=True,
            conversation_state=ConversationState.ACTIVE,
            qualification_tags=['high_engagement', 'complete_info'],
            priority_level='high',
            analyzed_at=datetime.utcnow()
        )
        
        await detector.update_lead_qualification_in_database('user123', qualification_result)
        
        mock_database.leads.update_one.assert_called_once()
        update_call = mock_database.leads.update_one.call_args
        assert update_call[0][0] == {'user_id': 'user123'}
        assert 'qualification_result' in update_call[0][1]['$set']
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self, detector, mock_database):
        """Test handling of database connection errors."""
        mock_database.leads.find_one.side_effect = DatabaseError("Connection failed")
        
        with pytest.raises(DatabaseError):
            await detector.analyze_lead_from_database('user123')
    
    @pytest.mark.asyncio
    async def test_lead_not_found_in_database(self, detector, mock_database):
        """Test handling when lead is not found in database."""
        mock_database.leads.find_one.return_value = None
        
        result = await detector.analyze_lead_from_database('nonexistent_user')
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_batch_qualification_analysis(self, detector, mock_database):
        """Test batch analysis of multiple leads."""
        lead_ids = ['user1', 'user2', 'user3']
        mock_leads = [
            {'user_id': 'user1', 'name': 'User 1', 'email': 'user1@test.com'},
            {'user_id': 'user2', 'name': 'User 2', 'email': 'user2@test.com'},
            {'user_id': 'user3', 'name': 'User 3', 'email': 'user3@test.com'}
        ]
        
        mock_database.leads.find.return_value = mock_leads
        
        results = await detector.batch_analyze_leads(lead_ids)
        
        assert len(results) == 3
        assert all(isinstance(result, LeadQualificationResult) for result in results)
    
    @pytest.mark.asyncio
    async def test_qualification_history_tracking(self, detector, mock_database, sample_complete_lead_data):
        """Test tracking qualification history over time."""
        mock_database.leads.find_one.return_value = sample_complete_lead_data
        
        result = await detector.analyze_lead_from_database('user123')
        await detector.save_qualification_history('user123', result)
        
        # Verify history was saved
        expected_history_entry = {
            'user_id': 'user123',
            'qualification_status': result.status.value,
            'overall_score': result.score.overall,
            'analyzed_at': result.analyzed_at,
            'confidence_level': result.confidence_level
        }
        
        mock_database.qualification_history.insert_one.assert_called_once()


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling scenarios."""
    
    def test_empty_lead_data(self, detector):
        """Test handling of empty lead data."""
        result = detector.analyze_lead_qualification({})
        
        assert result.status == QualificationStatus.UNQUALIFIED
        assert result.score.overall == 0
        assert len(result.missing_elements) > 5
        assert result.ready_for_handoff is False
    
    def test_malformed_lead_data(self, detector):
        """Test handling of malformed lead data."""
        malformed_data = {
            'user_id': None,
            'name': '',
            'location': 'not_a_dict',
            'project_details': {'budget_range': 'invalid_range'}
        }
        
        result = detector.analyze_lead_qualification(malformed_data)
        
        assert result.status == QualificationStatus.UNQUALIFIED
        assert 'data_validation_errors' in result.qualification_tags
    
    def test_qualification_timeout_handling(self, detector, sample_complete_lead_data):
        """Test handling of qualification analysis timeout."""
        with patch('app.modules.qualified_lead_detector.time.time') as mock_time:
            mock_time.side_effect = [0, 0, 1000]  # Simulate timeout
            
            result = detector.analyze_lead_qualification(
                sample_complete_lead_data,
                timeout=30
            )
            
            assert 'analysis_timeout' in result.qualification_tags
    
    def test_concurrent_qualification_requests(self, detector, sample_complete_lead_data):
        """Test handling of concurrent qualification requests for same lead."""
        import asyncio
        import concurrent.futures
        
        def analyze_lead():
            return detector.analyze_lead_qualification(sample_complete_lead_data)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(analyze_lead) for _ in range(3)]
            results = [future.result() for future in futures]
        
        # All results should be consistent
        assert all(result.status == QualificationStatus.QUALIFIED for result in results)
        assert len(set(result.score.overall for result in results)) == 1
    
    def test_qualification_caching(self, detector, sample_complete_lead_data):
        """Test caching of qualification results."""
        user_id = sample_complete_lead_data['user_id']
        
        # First analysis
        result1 = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        # Second analysis should use cache if data hasn't changed
        result2 = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        assert result1.analyzed_at == result2.analyzed_at
        assert result1.score.overall == result2.score.overall
    
    def test_qualification_result_serialization(self, detector, sample_complete_lead_data):
        """Test serialization and deserialization of qualification results."""
        result = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        # Serialize to JSON
        serialized = result.to_json()
        assert isinstance(serialized, str)
        
        # Deserialize from JSON
        deserialized = LeadQualificationResult.from_json(serialized)
        
        assert deserialized.status == result.status
        assert deserialized.score.overall == result.score.overall
        assert deserialized.completeness_percentage == result.completeness_percentage


class TestQualificationMetrics:
    """Test qualification metrics and scoring algorithms."""
    
    def test_scoring_algorithm_consistency(self, detector):
        """Test that scoring algorithm produces consistent results."""
        test_data = {
            'user_id': 'test_user',
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '+1234567890',
            'location': {'city': 'Test City', 'state': 'TS'},
            'project_details': {
                'project_type': 'bathroom_remodel',
                'budget_range': '$10000-$20000',
                'timeline': 'within_6_months'
            },
            'engagement_score': 70
        }
        
        # Run analysis multiple times
        results = [detector.analyze_lead_qualification(test_data) for _ in range(5)]
        
        # Check consistency
        scores = [result.score.overall for result in results]
        assert len(set(scores)) == 1, "Scoring should be consistent"
    
    def test_weighted_scoring_components(self, detector, sample_complete_lead_data):
        """Test that scoring components are properly weighted."""
        result = detector.analyze_lead_qualification(sample_complete_lead_data)
        
        # Verify scoring components contribute appropriately to overall score
        component_scores = [
            result.score.contact_info * 0.20,
            result.score.project_details * 0.25,
            result.score.engagement * 0.20,
            result.score.budget * 0.15,
            result.score.timeline * 0.10,
            result.score.location * 0.10
        ]
        
        expected_overall = sum(component_scores)
        assert abs(result.score.overall - expected_overall) < 5  # Allow small variance
    
    def test_qualification_threshold_boundaries(self, detector):
        """Test qualification status at threshold boundaries."""
        # Test data at qualification threshold
        threshold_data = {
            'user_id': 'threshold_user',
            'name': 'Threshold User',
            'email': 'threshold@example.com',
            'engagement_score': 60  # At boundary
        }
        
        result = detector.analyze_lead_qualification(threshold_data)
        
        # Should handle boundary cases gracefully
        assert result.status in [QualificationStatus.QUALIFIED, QualificationStatus.NEEDS_NURTURING]
        assert result.confidence_level in ['medium', 'low']


class TestPerformanceAndScaling:
    """Test performance characteristics and scaling behavior."""
    
    def test_large_conversation_history_performance(self, detector, sample_complete_lead_data):
        """Test performance with large conversation history."""
        # Create large conversation history
        large_history = [
            {'message': f'Message {i}', 'timestamp': datetime.utcnow()}
            for i in range(1000)
        ]
        sample_complete_lead_data['conversation_history'] = large_history
        
        import time
        start_time = time.time()
        result = detector.analyze_lead_qualification(sample_complete_lead_data)
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 5.0
        assert result.status is not None
    
    def test_memory_usage_with_large_datasets(self, detector):
        """Test memory usage remains reasonable with large datasets."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Process many leads
        for i in range(100):
            test_data = {
                'user_id': f'user_{i}',
                'name': f'User {i}',
                'email': f'user{i}@example.com'
            }
            detector.analyze_lead_qualification(test_data)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024