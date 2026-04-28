import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from decimal import Decimal
import json

from src.notification_manager import NotificationManager
from src.models.lead import Lead, LeadStatus
from src.models.customer import Customer
from src.models.notification import NotificationLog, NotificationType


@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    session = Mock()
    session.query.return_value = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.close = Mock()
    return session


@pytest.fixture
def mock_email_service():
    """Mock email service for testing."""
    email_service = Mock()
    email_service.send_email.return_value = {"status": "sent", "message_id": "123456"}
    return email_service


@pytest.fixture
def sample_customer():
    """Sample customer data for testing."""
    return Customer(
        id=1,
        first_name="John",
        last_name="Smith",
        email="john.smith@email.com",
        phone="555-123-4567",
        address="123 Main St",
        city="Anytown",
        state="CA",
        zip_code="12345",
        created_at=datetime.now(),
    )


@pytest.fixture
def qualified_lead_data():
    """Complete qualified lead data for testing."""
    return {
        "id": 1,
        "customer_id": 1,
        "service_type": "roof_repair",
        "description": "Residential roof repair needed after storm damage",
        "urgency": "high",
        "budget_min": Decimal("2000.00"),
        "budget_max": Decimal("5000.00"),
        "preferred_date": datetime(2024, 2, 15),
        "property_type": "residential",
        "square_footage": 2500,
        "materials_needed": ["shingles", "underlayment", "flashing"],
        "access_requirements": "Standard ladder access",
        "permits_required": True,
        "insurance_claim": True,
        "photos_provided": True,
        "created_at": datetime.now(),
        "status": LeadStatus.QUALIFIED,
    }


@pytest.fixture
def incomplete_lead_data():
    """Incomplete lead data for testing."""
    return {
        "id": 2,
        "customer_id": 2,
        "service_type": "plumbing",
        "description": "Need plumber",
        "urgency": None,
        "budget_min": None,
        "budget_max": None,
        "preferred_date": None,
        "property_type": None,
        "square_footage": None,
        "materials_needed": [],
        "access_requirements": None,
        "permits_required": None,
        "insurance_claim": None,
        "photos_provided": False,
        "created_at": datetime.now(),
        "status": LeadStatus.INCOMPLETE,
    }


@pytest.fixture
def notification_manager(mock_db_session, mock_email_service):
    """NotificationManager instance with mocked dependencies."""
    return NotificationManager(
        db_session=mock_db_session, email_service=mock_email_service
    )


class TestDetectQualifiedLead:
    """Test cases for lead qualification detection."""

    def test_detect_qualified_lead_complete_data(
        self, notification_manager, qualified_lead_data
    ):
        """Test detection of a fully qualified lead."""
        lead = Lead(**qualified_lead_data)
        result = notification_manager.detect_qualified_lead(lead)

        assert result is True

    def test_detect_qualified_lead_incomplete_data(
        self, notification_manager, incomplete_lead_data
    ):
        """Test detection of an incomplete lead."""
        lead = Lead(**incomplete_lead_data)
        result = notification_manager.detect_qualified_lead(lead)

        assert result is False

    def test_detect_qualified_lead_missing_budget(
        self, notification_manager, qualified_lead_data
    ):
        """Test detection fails when budget information is missing."""
        qualified_lead_data["budget_min"] = None
        qualified_lead_data["budget_max"] = None
        lead = Lead(**qualified_lead_data)

        result = notification_manager.detect_qualified_lead(lead)
        assert result is False

    def test_detect_qualified_lead_missing_urgency(
        self, notification_manager, qualified_lead_data
    ):
        """Test detection fails when urgency is missing."""
        qualified_lead_data["urgency"] = None
        lead = Lead(**qualified_lead_data)

        result = notification_manager.detect_qualified_lead(lead)
        assert result is False

    def test_detect_qualified_lead_missing_description(
        self, notification_manager, qualified_lead_data
    ):
        """Test detection fails when description is too brief."""
        qualified_lead_data["description"] = "Fix"
        lead = Lead(**qualified_lead_data)

        result = notification_manager.detect_qualified_lead(lead)
        assert result is False

    def test_detect_qualified_lead_edge_case_minimum_budget(
        self, notification_manager, qualified_lead_data
    ):
        """Test detection with minimum valid budget."""
        qualified_lead_data["budget_min"] = Decimal("100.00")
        qualified_lead_data["budget_max"] = Decimal("200.00")
        lead = Lead(**qualified_lead_data)

        result = notification_manager.detect_qualified_lead(lead)
        assert result is True


class TestGenerateContractorNotificationEmail:
    """Test cases for contractor notification email generation."""

    def test_generate_contractor_notification_email_complete(
        self, notification_manager, qualified_lead_data, sample_customer
    ):
        """Test generation of complete contractor notification email."""
        lead = Lead(**qualified_lead_data)
        contractor_email = "contractor@example.com"

        result = notification_manager.generate_contractor_notification_email(
            lead, sample_customer, contractor_email
        )

        assert result["to"] == contractor_email
        assert result["subject"] == "New Qualified Lead: Roof Repair - John Smith"
        assert "John Smith" in result["body"]
        assert "john.smith@email.com" in result["body"]
        assert "555-123-4567" in result["body"]
        assert "$2,000 - $5,000" in result["body"]
        assert "high" in result["body"].lower()
        assert "roof repair" in result["body"].lower()

    def test_generate_contractor_notification_email_html_format(
        self, notification_manager, qualified_lead_data, sample_customer
    ):
        """Test HTML format of contractor notification email."""
        lead = Lead(**qualified_lead_data)
        contractor_email = "contractor@example.com"

        result = notification_manager.generate_contractor_notification_email(
            lead, sample_customer, contractor_email, format_type="html"
        )

        assert "<html>" in result["body"]
        assert "<h2>" in result["body"]
        assert "<strong>" in result["body"]
        assert "<ul>" in result["body"]
        assert "</html>" in result["body"]

    def test_generate_contractor_notification_email_with_materials(
        self, notification_manager, qualified_lead_data, sample_customer
    ):
        """Test contractor email includes materials list."""
        lead = Lead(**qualified_lead_data)
        contractor_email = "contractor@example.com"

        result = notification_manager.generate_contractor_notification_email(
            lead, sample_customer, contractor_email
        )

        assert "shingles" in result["body"]
        assert "underlayment" in result["body"]
        assert "flashing" in result["body"]

    def test_generate_contractor_notification_email_insurance_claim(
        self, notification_manager, qualified_lead_data, sample_customer
    ):
        """Test contractor email mentions insurance claim."""
        lead = Lead(**qualified_lead_data)
        contractor_email = "contractor@example.com"

        result = notification_manager.generate_contractor_notification_email(
            lead, sample_customer, contractor_email
        )

        assert "insurance" in result["body"].lower()


class TestGenerateCustomerHandoffMessage:
    """Test cases for customer handoff message generation."""

    def test_generate_customer_handoff_message_basic(
        self, notification_manager, sample_customer
    ):
        """Test basic customer handoff message generation."""
        contractor_name = "ABC Roofing Company"
        contractor_phone = "555-999-8888"
        estimated_contact_time = "within 2 hours"

        result = notification_manager.generate_customer_handoff_message(
            sample_customer, contractor_name, contractor_phone, estimated_contact_time
        )

        assert "John" in result
        assert "ABC Roofing Company" in result
        assert "555-999-8888" in result
        assert "within 2 hours" in result

    def test_generate_customer_handoff_message_formatting(
        self, notification_manager, sample_customer
    ):
        """Test proper formatting of customer handoff message."""
        contractor_name = "Best Contractors LLC"
        contractor_phone = "555-777-6666"
        estimated_contact_time = "tomorrow morning"

        result = notification_manager.generate_customer_handoff_message(
            sample_customer, contractor_name, contractor_phone, estimated_contact_time
        )

        # Check for proper greeting and professional tone
        assert result.startswith("Hi John,")
        assert "we've connected you with" in result.lower()
        assert "thank you for choosing" in result.lower()

    def test_generate_customer_handoff_message_with_reference_number(
        self, notification_manager, sample_customer
    ):
        """Test customer handoff message includes reference number."""
        contractor_name = "Pro Services Inc"
        contractor_phone = "555-444-3333"
        estimated_contact_time = "this afternoon"
        reference_number = "REF-12345"

        result = notification_manager.generate_customer_handoff_message(
            sample_customer,
            contractor_name,
            contractor_phone,
            estimated_contact_time,
            reference_number,
        )

        assert "REF-12345" in result


class TestFormatLeadSummary:
    """Test cases for lead summary formatting."""

    def test_format_lead_summary_complete_data(
        self, notification_manager, qualified_lead_data, sample_customer
    ):
        """Test formatting of complete lead summary."""
        lead = Lead(**qualified_lead_data)

        result = notification_manager.format_lead_summary(lead, sample_customer)

        assert "Lead ID: 1" in result
        assert "Customer: John Smith" in result
        assert "Service: roof_repair" in result
        assert "Budget: $2,000.00 - $5,000.00" in result
        assert "Urgency: high" in result
        assert "Property: residential, 2500 sq ft" in result
        assert "Contact: john.smith@email.com, 555-123-4567" in result

    def test_format_lead_summary_with_address(
        self, notification_manager, qualified_lead_data, sample_customer
    ):
        """Test lead summary includes customer address."""
        lead = Lead(**qualified_lead_data)

        result = notification_manager.format_lead_summary(lead, sample_customer)

        assert "Address: 123 Main St, Anytown, CA 12345" in result

    def test_format_lead_summary_missing_optional_fields(
        self, notification_manager, incomplete_lead_data
    ):
        """Test formatting handles missing optional fields gracefully."""
        customer = Customer(
            id=2,
            first_name="Jane",
            last_name="Doe",
            email="jane@email.com",
            phone="555-000-1111",
        )
        lead = Lead(**incomplete_lead_data)

        result = notification_manager.format_lead_summary(lead, customer)

        assert "Lead ID: 2" in result
        assert "Customer: Jane Doe" in result
        assert "Budget: Not specified" in result
        assert "Urgency: Not specified" in result


class TestLogNotification:
    """Test cases for notification logging."""

    def test_log_notification_success(self, notification_manager, mock_db_session):
        """Test successful notification logging."""
        notification_data = {
            "lead_id": 1,
            "notification_type": NotificationType.CONTRACTOR_NOTIFICATION,
            "recipient": "contractor@example.com",
            "message": "Test notification message",
            "status": "sent",
            "metadata": {"email_id": "123456"},
        }

        result = notification_manager.log_notification(**notification_data)

        assert result is True
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_log_notification_database_error(
        self, notification_manager, mock_db_session
    ):
        """Test notification logging handles database errors."""
        mock_db_session.commit.side_effect = Exception("Database error")

        notification_data = {
            "lead_id": 1,
            "notification_type": NotificationType.CUSTOMER_HANDOFF,
            "recipient": "customer@example.com",
            "message": "Test message",
            "status": "failed",
        }

        result = notification_manager.log_notification(**notification_data)

        assert result is False
        mock_db_session.rollback.assert_called_once()

    def test_log_notification_with_metadata(
        self, notification_manager, mock_db_session
    ):
        """Test notification logging includes metadata."""
        metadata = {
            "email_provider": "SendGrid",
            "template_id": "template_123",
            "campaign_id": "camp_456",
        }

        notification_data = {
            "lead_id": 1,
            "notification_type": NotificationType.CONTRACTOR_NOTIFICATION,
            "recipient": "test@example.com",
            "message": "Test with metadata",
            "status": "sent",
            "metadata": metadata,
        }

        notification_manager.log_notification(**notification_data)

        # Verify the logged notification contains metadata
        call_args = mock_db_session.add.call_args[0][0]
        assert isinstance(call_args, NotificationLog)
        assert call_args.metadata == json.dumps(metadata)


class TestUpdateLeadStatus:
    """Test cases for lead status updates."""

    def test_update_lead_status_success(self, notification_manager, mock_db_session):
        """Test successful lead status update."""
        lead_id = 1
        new_status = LeadStatus.ASSIGNED
        notes = "Lead assigned to contractor"

        # Mock the query result
        mock_lead = Mock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_lead
        )

        result = notification_manager.update_lead_status(lead_id, new_status, notes)

        assert result is True
        assert mock_lead.status == new_status
        assert mock_lead.status_notes == notes
        assert mock_lead.updated_at is not None
        mock_db_session.commit.assert_called_once()

    def test_update_lead_status_lead_not_found(
        self, notification_manager, mock_db_session
    ):
        """Test lead status update when lead doesn't exist."""
        lead_id = 999
        new_status = LeadStatus.ASSIGNED

        # Mock query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        result = notification_manager.update_lead_status(lead_id, new_status)

        assert result is False
        mock_db_session.commit.assert_not_called()

    def test_update_lead_status_database_error(
        self, notification_manager, mock_db_session
    ):
        """Test lead status update handles database errors."""
        lead_id = 1
        new_status = LeadStatus.COMPLETED

        mock_lead = Mock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_lead
        )
        mock_db_session.commit.side_effect = Exception("Database error")

        result = notification_manager.update_lead_status(lead_id, new_status)

        assert result is False
        mock_db_session.rollback.assert_called_once()

    def test_update_lead_status_with_history_tracking(
        self, notification_manager, mock_db_session
    ):
        """Test lead status update creates history record."""
        lead_id = 1
        new_status = LeadStatus.IN_PROGRESS
        notes = "Work started"

        mock_lead = Mock()
        mock_lead.status = LeadStatus.ASSIGNED  # Previous status
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_lead
        )

        result = notification_manager.update_lead_status(
            lead_id, new_status, notes, track_history=True
        )

        assert result is True
        # Verify history record creation
        assert mock_db_session.add.call_count == 2  # Lead update + history record


class TestNotificationManagerIntegration:
    """Integration tests for notification manager."""

    @patch("src.notification_manager.EmailService")
    def test_full_notification_workflow(
        self,
        mock_email_class,
        notification_manager,
        qualified_lead_data,
        sample_customer,
    ):
        """Test complete notification workflow from lead detection to logging."""
        # Setup
        lead = Lead(**qualified_lead_data)
        contractor_email = "contractor@example.com"

        # Mock email service
        mock_email_instance = mock_email_class.return_value
        mock_email_instance.send_email.return_value = {
            "status": "sent",
            "message_id": "msg_123",
        }

        # Execute workflow
        is_qualified = notification_manager.detect_qualified_lead(lead)
        assert is_qualified is True

        email_content = notification_manager.generate_contractor_notification_email(
            lead, sample_customer, contractor_email
        )
        assert email_content["to"] == contractor_email

        # Update status
        update_success = notification_manager.update_lead_status(
            lead.id, LeadStatus.NOTIFIED, "Contractor notified"
        )
        assert update_success is True

    def test_notification_workflow_with_incomplete_lead(
        self, notification_manager, incomplete_lead_data
    ):
        """Test workflow correctly handles incomplete leads."""
        lead = Lead(**incomplete_lead_data)

        is_qualified = notification_manager.detect_qualified_lead(lead)
        assert is_qualified is False

        # Should not proceed with notification for incomplete lead
        update_success = notification_manager.update_lead_status(
            lead.id, LeadStatus.INCOMPLETE, "Missing required information"
        )
        assert update_success is True

    def test_error_handling_in_workflow(
        self, notification_manager, qualified_lead_data, sample_customer
    ):
        """Test error handling throughout the notification workflow."""
        lead = Lead(**qualified_lead_data)

        # Test with invalid email service
        notification_manager.email_service = None

        with pytest.raises(AttributeError):
            notification_manager.generate_contractor_notification_email(
                lead, sample_customer, "test@example.com"
            )

    @patch("src.notification_manager.datetime")
    def test_notification_timing_and_scheduling(
        self, mock_datetime, notification_manager, qualified_lead_data, sample_customer
    ):
        """Test notification timing and scheduling functionality."""
        # Mock current time
        mock_now = datetime(2024, 1, 15, 10, 30, 0)
        mock_datetime.now.return_value = mock_now

        lead = Lead(**qualified_lead_data)

        # Test immediate notification
        result = notification_manager.generate_contractor_notification_email(
            lead, sample_customer, "contractor@example.com"
        )

        assert "urgent" in result["body"].lower() or "high" in result["body"].lower()

    def test_bulk_notification_processing(self, notification_manager, mock_db_session):
        """Test processing multiple notifications in batch."""
        # Create multiple mock leads
        leads = []
        customers = []

        for i in range(3):
            lead_data = {
                "id": i + 1,
                "customer_id": i + 1,
                "service_type": "plumbing",
                "description": f"Service request {i + 1}",
                "urgency": "medium",
                "budget_min": Decimal("500.00"),
                "budget_max": Decimal("1000.00"),
                "status": LeadStatus.QUALIFIED,
            }
            leads.append(Lead(**lead_data))

            customer_data = {
                "id": i + 1,
                "first_name": f"Customer{i + 1}",
                "last_name": "Test",
                "email": f"customer{i + 1}@test.com",
                "phone": f"555-000-000{i + 1}",
            }
            customers.append(Customer(**customer_data))

        # Process notifications for all leads
        results = []
        for lead, customer in zip(leads, customers):
            if notification_manager.detect_qualified_lead(lead):
                email_content = (
                    notification_manager.generate_contractor_notification_email(
                        lead, customer, "contractor@example.com"
                    )
                )
                results.append(email_content)

        assert len(results) == 3
        for result in results:
            assert result["to"] == "contractor@example.com"
            assert "Service request" in result["body"]
