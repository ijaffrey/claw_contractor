import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime, timedelta
from typing import Dict, Any, List
from decimal import Decimal

from claw_contractor.workflows.handoff_workflow import HandoffWorkflow
from claw_contractor.models.lead import Lead, LeadStatus
from claw_contractor.models.contractor import Contractor
from claw_contractor.models.notification import Notification, NotificationType
from claw_contractor.models.project import Project, ProjectType
from claw_contractor.exceptions import (
    WorkflowError,
    NotificationError,
    DatabaseError,
    ValidationError
)


@pytest.fixture
def mock_db_session():
    """Mock database session with transaction support."""
    session = MagicMock()
    session.begin = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.add = MagicMock()
    session.execute = AsyncMock()
    session.scalar = AsyncMock()
    session.scalars = AsyncMock()
    return session


@pytest.fixture
def mock_email_service():
    """Mock email service."""
    service = AsyncMock()
    service.send_email = AsyncMock(return_value={"message_id": "msg_123", "status": "sent"})
    service.send_template_email = AsyncMock(return_value={"message_id": "msg_456", "status": "sent"})
    return service


@pytest.fixture
def mock_notification_service():
    """Mock notification service."""
    service = AsyncMock()
    service.log_notification = AsyncMock()
    service.create_notification = AsyncMock()
    return service


@pytest.fixture
def sample_lead():
    """Sample lead fixture with comprehensive data."""
    return Lead(
        id="lead_123",
        customer_name="John Smith",
        customer_email="john.smith@email.com",
        customer_phone="+1-555-0123",
        project_description="Kitchen renovation with modern appliances and granite countertops",
        project_type=ProjectType.KITCHEN_RENOVATION,
        budget_min=Decimal("15000.00"),
        budget_max=Decimal("25000.00"),
        location_address="123 Main St, Anytown, ST 12345",
        location_latitude=Decimal("40.7128"),
        location_longitude=Decimal("-74.0060"),
        preferred_start_date=datetime.now() + timedelta(days=30),
        timeline_flexibility="2-3 weeks",
        status=LeadStatus.NEW,
        qualification_score=85,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        metadata={
            "source": "website_form",
            "utm_campaign": "spring_renovation",
            "special_requirements": ["pet_friendly_materials", "eco_friendly"],
            "previous_work": False,
            "property_type": "single_family_home",
            "square_footage": 1800
        }
    )


@pytest.fixture
def qualified_lead(sample_lead):
    """Lead that meets qualification criteria."""
    sample_lead.qualification_score = 90
    sample_lead.budget_min = Decimal("20000.00")
    sample_lead.status = LeadStatus.QUALIFIED
    return sample_lead


@pytest.fixture
def unqualified_lead(sample_lead):
    """Lead that doesn't meet qualification criteria."""
    sample_lead.qualification_score = 45
    sample_lead.budget_min = Decimal("2000.00")
    sample_lead.status = LeadStatus.NEW
    return sample_lead


@pytest.fixture
def sample_contractors():
    """Sample contractors fixture."""
    return [
        Contractor(
            id="contractor_1",
            name="ABC Construction",
            email="contact@abcconstruction.com",
            phone="+1-555-0100",
            specialties=[ProjectType.KITCHEN_RENOVATION, ProjectType.BATHROOM_RENOVATION],
            service_radius=Decimal("25.0"),
            location_latitude=Decimal("40.7000"),
            location_longitude=Decimal("-74.0000"),
            is_active=True,
            rating=Decimal("4.8"),
            completed_projects=127,
            response_time_hours=2,
            metadata={"premium_tier": True, "verified": True}
        ),
        Contractor(
            id="contractor_2",
            name="Elite Renovations",
            email="info@elitereno.com",
            phone="+1-555-0200",
            specialties=[ProjectType.KITCHEN_RENOVATION, ProjectType.WHOLE_HOUSE],
            service_radius=Decimal("30.0"),
            location_latitude=Decimal("40.7200"),
            location_longitude=Decimal("-74.0100"),
            is_active=True,
            rating=Decimal("4.9"),
            completed_projects=89,
            response_time_hours=1,
            metadata={"premium_tier": True, "verified": True}
        )
    ]


@pytest.fixture
def workflow(mock_db_session, mock_email_service, mock_notification_service):
    """HandoffWorkflow instance with mocked dependencies."""
    workflow = HandoffWorkflow()
    workflow.db_session = mock_db_session
    workflow.email_service = mock_email_service
    workflow.notification_service = mock_notification_service
    workflow.qualification_threshold = 70
    workflow.min_budget_threshold = Decimal("5000.00")
    return workflow


class TestQualifiedLeadDetection:
    """Test suite for qualified lead detection accuracy."""

    def test_detect_qualified_lead_success(self, workflow, qualified_lead):
        """Test successful detection of qualified lead."""
        result = workflow._is_lead_qualified(qualified_lead)
        
        assert result is True

    def test_detect_unqualified_lead_low_score(self, workflow, unqualified_lead):
        """Test detection of unqualified lead due to low score."""
        result = workflow._is_lead_qualified(unqualified_lead)
        
        assert result is False

    def test_detect_unqualified_lead_low_budget(self, workflow, sample_lead):
        """Test detection of unqualified lead due to low budget."""
        sample_lead.qualification_score = 80
        sample_lead.budget_min = Decimal("1000.00")
        
        result = workflow._is_lead_qualified(sample_lead)
        
        assert result is False

    def test_detect_qualified_lead_edge_case_threshold(self, workflow, sample_lead):
        """Test qualified lead detection at threshold boundary."""
        sample_lead.qualification_score = 70  # Exact threshold
        sample_lead.budget_min = Decimal("5000.00")  # Exact threshold
        
        result = workflow._is_lead_qualified(sample_lead)
        
        assert result is True

    def test_detect_qualified_lead_missing_budget(self, workflow, sample_lead):
        """Test qualified lead detection with missing budget."""
        sample_lead.qualification_score = 85
        sample_lead.budget_min = None
        
        result = workflow._is_lead_qualified(sample_lead)
        
        assert result is False

    def test_detect_qualified_lead_missing_score(self, workflow, sample_lead):
        """Test qualified lead detection with missing score."""
        sample_lead.qualification_score = None
        sample_lead.budget_min = Decimal("15000.00")
        
        result = workflow._is_lead_qualified(sample_lead)
        
        assert result is False

    def test_qualification_criteria_configuration(self, workflow, sample_lead):
        """Test that qualification criteria can be configured."""
        # Test with different threshold
        workflow.qualification_threshold = 95
        workflow.min_budget_threshold = Decimal("50000.00")
        
        sample_lead.qualification_score = 90
        sample_lead.budget_min = Decimal("25000.00")
        
        result = workflow._is_lead_qualified(sample_lead)
        
        assert result is False


class TestContractorNotificationEmail:
    """Test suite for contractor notification email generation and sending."""

    @pytest.mark.asyncio
    async def test_generate_contractor_notification_email_content(self, workflow, qualified_lead, sample_contractors):
        """Test generation of contractor notification email content."""
        contractor = sample_contractors[0]
        
        email_content = workflow._generate_contractor_email_content(qualified_lead, contractor)
        
        assert email_content['subject'] == f"New Qualified Lead: {qualified_lead.project_type.value}"
        assert qualified_lead.customer_name in email_content['body']
        assert qualified_lead.project_description in email_content['body']
        assert str(qualified_lead.budget_min) in email_content['body']
        assert str(qualified_lead.budget_max) in email_content['body']
        assert qualified_lead.location_address in email_content['body']
        assert contractor.name in email_content['body']

    @pytest.mark.asyncio
    async def test_send_contractor_notification_email_success(self, workflow, qualified_lead, sample_contractors, mock_email_service):
        """Test successful sending of contractor notification email."""
        contractor = sample_contractors[0]
        
        result = await workflow._send_contractor_notification(qualified_lead, contractor)
        
        mock_email_service.send_template_email.assert_called_once()
        call_args = mock_email_service.send_template_email.call_args
        
        assert call_args[1]['to_email'] == contractor.email
        assert call_args[1]['template_id'] == 'contractor_new_lead'
        assert 'lead_data' in call_args[1]['template_variables']
        assert 'contractor_data' in call_args[1]['template_variables']
        assert result['status'] == 'sent'

    @pytest.mark.asyncio
    async def test_send_contractor_notification_email_failure(self, workflow, qualified_lead, sample_contractors, mock_email_service):
        """Test handling of contractor notification email failure."""
        contractor = sample_contractors[0]
        mock_email_service.send_template_email.side_effect = NotificationError("Email service unavailable")
        
        with pytest.raises(NotificationError):
            await workflow._send_contractor_notification(qualified_lead, contractor)

    @pytest.mark.asyncio
    async def test_send_multiple_contractor_notifications(self, workflow, qualified_lead, sample_contractors, mock_email_service):
        """Test sending notifications to multiple contractors."""
        results = []
        for contractor in sample_contractors:
            result = await workflow._send_contractor_notification(qualified_lead, contractor)
            results.append(result)
        
        assert len(results) == 2
        assert mock_email_service.send_template_email.call_count == 2
        
        # Verify each contractor got notified
        call_args_list = mock_email_service.send_template_email.call_args_list
        sent_emails = [call[1]['to_email'] for call in call_args_list]
        expected_emails = [contractor.email for contractor in sample_contractors]
        
        assert set(sent_emails) == set(expected_emails)

    @pytest.mark.asyncio
    async def test_contractor_email_personalization(self, workflow, qualified_lead, sample_contractors):
        """Test that contractor emails are personalized."""
        contractor = sample_contractors[0]
        
        email_content = workflow._generate_contractor_email_content(qualified_lead, contractor)
        
        # Should contain contractor-specific information
        assert contractor.name in email_content['body']
        assert "your expertise in" in email_content['body'].lower()
        
        # Should contain lead-specific information
        assert qualified_lead.customer_name in email_content['body']
        assert qualified_lead.project_description in email_content['body']


class TestLeadSummaryFormatting:
    """Test suite for lead summary formatting with all data types."""

    def test_format_lead_summary_complete_data(self, workflow, qualified_lead):
        """Test formatting lead summary with complete data."""
        summary = workflow._format_lead_summary(qualified_lead)
        
        # Verify all essential fields are present
        assert f"Lead ID: {qualified_lead.id}" in summary
        assert f"Customer: {qualified_lead.customer_name}" in summary
        assert f"Email: {qualified_lead.customer_email}" in summary
        assert f"Phone: {qualified_lead.customer_phone}" in summary
        assert f"Project: {qualified_lead.project_description}" in summary
        assert f"Type: {qualified_lead.project_type.value}" in summary
        assert f"Budget: ${qualified_lead.budget_min:,.2f} - ${qualified_lead.budget_max:,.2f}" in summary
        assert f"Location: {qualified_lead.location_address}" in summary
        assert f"Qualification Score: {qualified_lead.qualification_score}" in summary

    def test_format_lead_summary_with_metadata(self, workflow, qualified_lead):
        """Test formatting lead summary including metadata."""
        summary = workflow._format_lead_summary(qualified_lead, include_metadata=True)
        
        # Verify metadata fields are included
        assert "Source: website_form" in summary
        assert "UTM Campaign: spring_renovation" in summary
        assert "Special Requirements:" in summary
        assert "pet_friendly_materials" in summary
        assert "eco_friendly" in summary
        assert "Property Type: single_family_home" in summary
        assert "Square Footage: 1800" in summary

    def test_format_lead_summary_missing_optional_fields(self, workflow, sample_lead):
        """Test formatting lead summary with missing optional fields."""
        sample_lead.customer_phone = None
        sample_lead.budget_max = None
        sample_lead.preferred_start_date = None
        sample_lead.timeline_flexibility = None
        
        summary = workflow._format_lead_summary(sample_lead)
        
        # Should handle missing fields gracefully
        assert "Phone: Not provided" in summary
        assert f"Budget: ${sample_lead.budget_min:,.2f} - Not specified" in summary
        assert "Start Date: Flexible" in summary
        assert "Timeline: Not specified" in summary

    def test_format_lead_summary_decimal_formatting(self, workflow, qualified_lead):
        """Test proper decimal formatting in lead summary."""
        qualified_lead.budget_min = Decimal("15000.50")
        qualified_lead.budget_max = Decimal("25750.25")
        qualified_lead.location_latitude = Decimal("40.712800")
        qualified_lead.location_longitude = Decimal("-74.006000")
        
        summary = workflow._format_lead_summary(qualified_lead)
        
        assert "Budget: $15,000.50 - $25,750.25" in summary
        assert "Coordinates: (40.7128, -74.0060)" in summary

    def test_format_lead_summary_date_formatting(self, workflow, qualified_lead):
        """Test proper date formatting in lead summary."""
        test_date = datetime(2024, 6, 15, 14, 30, 0)
        qualified_lead.preferred_start_date = test_date
        qualified_lead.created_at = test_date
        
        summary = workflow._format_lead_summary(qualified_lead)
        
        assert "Start Date: June 15, 2024" in summary
        assert "Submitted: June 15, 2024 at 2:30 PM" in summary

    def test_format_lead_summary_html_output(self, workflow, qualified_lead):
        """Test formatting lead summary as HTML."""
        summary = workflow._format_lead_summary(qualified_lead, format_type='html')
        
        assert summary.startswith('<div class="lead-summary">')
        assert '<h3>Lead Summary</h3>' in summary
        assert f'<p><strong>Customer:</strong> {qualified_lead.customer_name}</p>' in summary
        assert '<ul>' in summary  # For special requirements list
        assert '</div>' in summary

    def test_format_lead_summary_json_output(self, workflow, qualified_lead):
        """Test formatting lead summary as structured JSON."""
        import json
        
        summary = workflow._format_lead_summary(qualified_lead, format_type='json')
        data = json.loads(summary)
        
        assert data['lead_id'] == qualified_lead.id
        assert data['customer']['name'] == qualified_lead.customer_name
        assert data['customer']['email'] == qualified_lead.customer_email
        assert data['project']['type'] == qualified_lead.project_type.value
        assert data['budget']['min'] == float(qualified_lead.budget_min)
        assert data['location']['address'] == qualified_lead.location_address


class TestCustomerHandoffMessage:
    """Test suite for customer handoff message generation."""

    def test_generate_customer_handoff_message_basic(self, workflow, qualified_lead, sample_contractors):
        """Test generation of basic customer handoff message."""
        matched_contractors = sample_contractors[:1]
        
        message = workflow._generate_customer_handoff_message(qualified_lead, matched_contractors)
        
        assert qualified_lead.customer_name in message
        assert "Thank you for your interest" in message
        assert "matched you with qualified contractors" in message
        assert sample_contractors[0].name in message
        assert sample_contractors[0].phone in message

    def test_generate_customer_handoff_message_multiple_contractors(self, workflow, qualified_lead, sample_contractors):
        """Test generation of customer handoff message with multiple contractors."""
        message = workflow._generate_customer_handoff_message(qualified_lead, sample_contractors)
        
        # Should mention multiple contractors
        assert "contractors" in message.lower()
        assert len([name for name in [c.name for c in sample_contractors] if name in message]) == len(sample_contractors)

    def test_generate_customer_handoff_message_project_details(self, workflow, qualified_lead, sample_contractors):
        """Test that customer handoff message includes project details."""
        message = workflow._generate_customer_handoff_message(qualified_lead, sample_contractors)
        
        assert qualified_lead.project_type.value.lower() in message.lower()
        assert str(qualified_lead.budget_min) in message or "budget" in message.lower()

    def test_generate_customer_handoff_message_next_steps(self, workflow, qualified_lead, sample_contractors):
        """Test that customer handoff message includes next steps."""
        message = workflow._generate_customer_handoff_message(qualified_lead, sample_contractors)
        
        assert "next steps" in message.lower() or "what happens next" in message.lower()
        assert "contact you" in message.lower()
        assert "within" in message.lower()  # Should mention timeframe

    def test_generate_customer_handoff_message_no_contractors(self, workflow, qualified_lead):
        """Test generation of customer handoff message with no matched contractors."""
        message = workflow._generate_customer_handoff_message(qualified_lead, [])
        
        assert "apologize" in message.lower()
        assert "no contractors" in message.lower() or "unable to match" in message.lower()
        assert "expand our search" in message.lower()

    @pytest.mark.asyncio
    async def test_send_customer_handoff_email(self, workflow, qualified_lead, sample_contractors, mock_email_service):
        """Test sending customer handoff email."""
        message = workflow._generate_customer_handoff_message(qualified_lead, sample_contractors)
        
        result = await workflow._send_customer_handoff_notification(qualified_lead, sample_contractors)
        
        mock_email_service.send_template_email.assert_called_once()
        call_args = mock_email_service.send_template_email.call_args
        
        assert call_args[1]['to_email'] == qualified_lead.customer_email
        assert call_args[1]['template_id'] == 'customer_handoff'
        assert 'lead_data' in call_args[1]['template_variables']
        assert 'contractors' in call_args[1]['template_variables']


class TestLeadStatusUpdates:
    """Test suite for lead status updates."""

    @pytest.mark.asyncio
    async def test_update_lead_status_to_qualified(self, workflow, sample_lead, mock_db_session):
        """Test updating lead status to qualified."""
        await workflow._update_lead_status(sample_lead, LeadStatus.QUALIFIED)
        
        assert sample_lead.status == LeadStatus.QUALIFIED
        assert sample_lead.updated_at is not None
        mock_db_session.add.assert_called_once_with(sample_lead)

    @pytest.mark.asyncio
    async def test_update_lead_status_to_handed_off(self, workflow, qualified_lead, mock_db_session):
        """Test updating lead status to handed off."""
        await workflow._update_lead_status(qualified_lead, LeadStatus.HANDED_OFF)
        
        assert qualified_lead.status == LeadStatus.HANDED_OFF
        assert qualified_lead.updated_at is not None
        mock_db_session.add.assert_called_once_with(qualified_lead)

    @pytest.mark.asyncio
    async def test_update_lead_status_to_unqualified(self, workflow, sample_lead, mock_db_session):
        """Test updating lead status to unqualified."""
        await workflow._update_lead_status(sample_lead, LeadStatus.UNQUALIFIED, "Low qualification score")
        
        assert sample_lead.status == LeadStatus.UNQUALIFIED
        assert "Low qualification score" in sample_lead.metadata.get('unqualified_reason', '')

    @pytest.mark.asyncio
    async def test_update_lead_status_with_metadata(self, workflow, sample_lead, mock_db_session):
        """Test updating lead status with additional metadata."""
        metadata = {"handoff_timestamp": datetime.now().isoformat(), "contractor_count": 2}
        
        await workflow._update_lead_status(sample_lead, LeadStatus.HANDED_OFF, metadata=metadata)
        
        assert sample_lead.status == LeadStatus.HANDED_OFF
        assert sample_lead.metadata['handoff_timestamp'] == metadata['handoff_timestamp']
        assert sample_lead.metadata['contractor_count'] == metadata['contractor_count']

    @pytest.mark.asyncio
    async def test_update_lead_status_invalid_transition(self, workflow, sample_lead):
        """Test invalid lead status transition."""
        sample_lead.status = LeadStatus.CLOSED
        
        with pytest.raises(ValidationError):
            await workflow._update_lead_status(sample_lead, LeadStatus.NEW)

    @pytest.mark.asyncio
    async def test_update_lead_status_database_error(self, workflow, sample_lead, mock_db_session):
        """Test handling database error during status update."""
        mock_db_session.add.side_effect = DatabaseError("Database connection failed")
        
        with pytest.raises(DatabaseError):
            await workflow._update_lead_status(sample_lead, LeadStatus.QUALIFIED)


class TestNotificationLogging:
    """Test suite for notification logging."""

    @pytest.mark.asyncio
    async def test_log_contractor_notification_success(self, workflow, qualified_lead, sample_contractors, mock_notification_service):
        """Test logging successful contractor notification."""
        contractor = sample_contractors[0]
        notification_result = {"message_id": "msg_123", "status": "sent"}
        
        await workflow._log_notification(
            lead_id=qualified_lead.id,
            notification_type=NotificationType.CONTRACTOR_NEW_LEAD,
            recipient_id=contractor.id,
            recipient_email=contractor.email,
            result=notification_result
        )
        
        mock_notification_service.log_notification.assert_called_once()
        call_args = mock_notification_service.log_notification.call_args[1]
        
        assert call_args['lead_id'] == qualified_lead.id
        assert call_args['notification_type'] == NotificationType.CONTRACTOR_NEW_LEAD
        assert call_args['recipient_id'] == contractor.id
        assert call_args['status'] == 'sent'
        assert call_args['message_id'] == 'msg_123'

    @pytest.mark.asyncio
    async def test_log_customer_notification_success(self, workflow, qualified_lead, mock_notification_service):
        """Test logging successful customer notification."""
        notification_result = {"message_id": "msg_456", "status": "sent"}
        
        await workflow._log_notification(
            lead_id=qualified_lead.id,
            notification_type=NotificationType.CUSTOMER_HANDOFF,
            recipient_email=qualified_lead.customer_email,
            result=notification_result
        )
        
        mock_notification_service.log_notification.assert_called_once()
        call_args = mock_notification_service.log_notification.call_args[1]
        
        assert call_args['lead_id'] == qualified_lead.id
        assert call_args['notification_type'] == NotificationType.CUSTOMER_HANDOFF
        assert call_args['recipient_email'] == qualified_lead.customer_email
        assert call_args['status'] == 'sent'

    @pytest.mark.asyncio
    async def test_log_notification_failure(self, workflow, qualified_lead, sample_contractors, mock_notification_service):
        """Test logging failed notification."""
        contractor = sample_contractors[0]
        notification_result = {"error": "Email service unavailable", "status": "failed"}
        
        await workflow._log_notification(
            lead_id=qualified_lead.id,
            notification_type=NotificationType.CONTRACTOR_NEW_LEAD,
            recipient_id=contractor.id,
            recipient_email=contractor.email,
            result=notification_result,
            error_message="Email service unavailable"
        )
        
        mock_notification_service.log_notification.assert_called_once()
        call_args = mock_notification_service.log_notification.call_args[1]
        
        assert call_args['status'] == 'failed'
        assert call_args['error_message'] == 'Email service unavailable'

    @pytest.mark.asyncio
    async def test_log_multiple_notifications(self, workflow, qualified_lead, sample_contractors, mock_notification_service):
        """Test logging multiple notifications."""
        for contractor in sample_contractors:
            notification_result = {"message_id": f"msg_{contractor.id}", "status": "sent"}
            await workflow._log_notification(
                lead_id=qualified_lead.id,
                notification_type=NotificationType.CONTRACTOR_NEW_LEAD,
                recipient_id=contractor.id,
                recipient_email=contractor.email,
                result=notification_result
            )
        
        assert mock_notification_service.log_notification.call_count == len(sample_contractors)

    @pytest.mark.asyncio
    async def test_create_notification_record(self, workflow, qualified_lead, sample_contractors, mock_notification_service):
        """Test creating notification records in database."""
        contractor = sample_contractors[0]
        
        notification = await workflow._create_notification_record(
            lead_id=qualified_lead.id,
            notification_type=NotificationType.CONTRACTOR_NEW_LEAD,
            recipient_id=contractor.id,
            recipient_email=contractor.email,
            subject="New Lead Available",
            content="A new qualified lead is available"
        )
        
        mock_notification_service.create_notification.assert_called_once()
        call_args = mock_notification_service.create_notification.call_args[1]
        
        assert call_args['lead_id'] == qualified_lead.id
        assert call_args['notification_type'] == NotificationType.CONTRACTOR_NEW_LEAD
        assert call_args['subject'] == "New Lead Available"


class TestErrorHandlingAndRollback:
    """Test suite for error handling and rollback scenarios."""

    @pytest.mark.asyncio
    async def test_rollback_on_email_failure(self, workflow, qualified_lead, sample_contractors, mock_db_session, mock_email_service):
        """Test rollback when email sending fails."""
        mock_email_service.send_template_email.side_effect = NotificationError("SMTP server unavailable")
        
        with pytest.raises(WorkflowError):
            await workflow.process_lead_handoff(qualified_lead.id)
        
        # Should rollback transaction
        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollback_on_database_failure(self, workflow, qualified_lead, mock_db_session):
        """Test rollback when database update fails."""
        mock_db_session.commit.side_effect = DatabaseError("Database connection lost")
        
        with pytest.raises(WorkflowError):
            await workflow.process_lead_handoff(qualified_lead.id)
        
        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_partial_failure_handling(self, workflow, qualified_lead, sample_contractors, mock_email_service, mock_notification_service):
        """Test handling when some contractor notifications fail."""
        # First email succeeds, second fails
        mock_email_service.send_template_email.side_effect = [
            {"message_id": "msg_123", "status": "sent"},
            NotificationError("Rate limit exceeded")
        ]
        
        with patch.object(workflow, '_find_matching_contractors', return_value=sample_contractors):
            with patch.object(workflow, '_is_lead_qualified', return_value=True):
                with pytest.raises(WorkflowError):
                    await workflow.process_lead_handoff(qualified_lead.id)
        
        # Should still log the failure
        assert mock_notification_service.log_notification.called

    @pytest.mark.asyncio
    async def test_validation_error_handling(self, workflow):
        """Test handling of validation errors."""
        invalid_lead_id = "invalid_lead"
        
        with pytest.raises(ValidationError):
            await workflow.process_lead_handoff(invalid_lead_id)

    @pytest.mark.asyncio
    async def test_no_contractors_found_handling(self, workflow, qualified_lead, mock_db_session):
        """Test handling when no contractors are found."""
        with patch.object(workflow, '_find_matching_contractors', return_value=[]):
            with patch.object(workflow, '_is_lead_qualified', return_value=True):
                with patch.object(workflow, '_get_lead_by_id', return_value=qualified_lead):
                    
                    result = await workflow.process_lead_handoff(qualified_lead.id)
                    
                    assert result['status'] == 'no_contractors_found'
                    assert qualified_lead.status == LeadStatus.NO_CONTRACTORS_AVAILABLE

    @pytest.mark.asyncio
    async def test_unqualified_lead_handling(self, workflow, unqualified_lead):
        """Test handling of unqualified leads."""
        with patch.object(workflow, '_get_lead_by_id', return_value=unqualified_lead):
            
            result = await workflow.process_lead_handoff(unqualified_lead.id)
            
            assert result['status'] == 'unqualified'
            assert unqualified_lead.status == LeadStatus.UNQUALIFIED

    @pytest.mark.asyncio
    async def test_duplicate_processing_prevention(self, workflow, qualified_lead):
        """Test prevention of duplicate lead processing."""
        qualified_lead.status = LeadStatus