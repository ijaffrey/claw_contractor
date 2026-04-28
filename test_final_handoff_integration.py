import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.models import Base, Lead, Contractor, Notification, ContractorProfile
from app.services.lead_qualification import LeadQualificationService
from app.services.contractor_matching import ContractorMatchingService
from app.services.notification_service import NotificationService
from app.services.handoff_orchestrator import HandoffOrchestratorService
from app.core.exceptions import HandoffError, NotificationError
from app.schemas.leads import LeadStatus, ServiceType
from app.schemas.contractors import ContractorStatus


class TestFinalHandoffIntegration:
    """End-to-end integration tests for the complete handoff workflow."""

    @pytest.fixture
    def test_db(self):
        """Create an in-memory test database."""
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=engine
        )
        return TestingSessionLocal()

    @pytest.fixture
    def sample_lead_data(self):
        """Sample lead data for testing."""
        return {
            "id": 1,
            "customer_name": "John Doe",
            "customer_email": "john.doe@example.com",
            "customer_phone": "+1234567890",
            "service_type": ServiceType.PLUMBING,
            "description": "Kitchen faucet repair needed urgently",
            "location": "Downtown Seattle, WA",
            "budget_range": "200-500",
            "urgency": "high",
            "status": LeadStatus.QUALIFIED,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

    @pytest.fixture
    def sample_contractor_data(self):
        """Sample contractor data for testing."""
        return {
            "id": 1,
            "name": "Mike's Plumbing",
            "email": "mike@mikesplumbing.com",
            "phone": "+1987654321",
            "status": ContractorStatus.ACTIVE,
            "profile": {
                "service_types": [ServiceType.PLUMBING],
                "service_areas": ["Downtown Seattle", "Capitol Hill", "Ballard"],
                "rating": 4.8,
                "completion_rate": 0.95,
                "response_time_hours": 2,
            },
        }

    @pytest.fixture
    def mock_services(self):
        """Mock all external services."""
        return {
            "lead_qualification": AsyncMock(spec=LeadQualificationService),
            "contractor_matching": AsyncMock(spec=ContractorMatchingService),
            "notification": AsyncMock(spec=NotificationService),
        }

    @pytest.fixture
    def orchestrator(self, test_db, mock_services):
        """Create handoff orchestrator with mocked dependencies."""
        return HandoffOrchestratorService(
            db=test_db,
            lead_qualification_service=mock_services["lead_qualification"],
            contractor_matching_service=mock_services["contractor_matching"],
            notification_service=mock_services["notification"],
        )

    def setup_test_data(self, db, lead_data, contractor_data):
        """Set up test data in the database."""
        # Create contractor profile
        contractor_profile = ContractorProfile(
            contractor_id=contractor_data["id"],
            service_types=contractor_data["profile"]["service_types"],
            service_areas=contractor_data["profile"]["service_areas"],
            rating=contractor_data["profile"]["rating"],
            completion_rate=contractor_data["profile"]["completion_rate"],
            response_time_hours=contractor_data["profile"]["response_time_hours"],
        )

        # Create contractor
        contractor = Contractor(
            id=contractor_data["id"],
            name=contractor_data["name"],
            email=contractor_data["email"],
            phone=contractor_data["phone"],
            status=contractor_data["status"],
            profile=contractor_profile,
        )

        # Create lead
        lead = Lead(
            id=lead_data["id"],
            customer_name=lead_data["customer_name"],
            customer_email=lead_data["customer_email"],
            customer_phone=lead_data["customer_phone"],
            service_type=lead_data["service_type"],
            description=lead_data["description"],
            location=lead_data["location"],
            budget_range=lead_data["budget_range"],
            urgency=lead_data["urgency"],
            status=lead_data["status"],
            created_at=lead_data["created_at"],
            updated_at=lead_data["updated_at"],
        )

        db.add(contractor)
        db.add(lead)
        db.commit()
        db.refresh(contractor)
        db.refresh(lead)

        return lead, contractor

    @pytest.mark.asyncio
    async def test_complete_handoff_workflow_success(
        self,
        orchestrator,
        test_db,
        mock_services,
        sample_lead_data,
        sample_contractor_data,
    ):
        """Test the complete successful handoff workflow from start to finish."""
        # Setup test data
        lead, contractor = self.setup_test_data(
            test_db, sample_lead_data, sample_contractor_data
        )

        # Mock service responses
        mock_services["lead_qualification"].is_qualified.return_value = True
        mock_services["contractor_matching"].find_best_match.return_value = contractor
        mock_services["notification"].notify_contractor.return_value = {
            "notification_id": "notif_123",
            "status": "sent",
            "timestamp": datetime.utcnow(),
        }
        mock_services["notification"].notify_customer.return_value = {
            "notification_id": "notif_456",
            "status": "sent",
            "timestamp": datetime.utcnow(),
        }

        # Execute handoff workflow
        result = await orchestrator.execute_complete_handoff(lead.id)

        # Verify result
        assert result["success"] is True
        assert result["lead_id"] == lead.id
        assert result["contractor_id"] == contractor.id
        assert "handoff_id" in result

        # Verify lead status updated to completed
        test_db.refresh(lead)
        assert lead.status == LeadStatus.COMPLETED
        assert lead.assigned_contractor_id == contractor.id
        assert lead.handoff_completed_at is not None

        # Verify notifications were sent
        mock_services["notification"].notify_contractor.assert_called_once()
        mock_services["notification"].notify_customer.assert_called_once()

        # Verify notification records in database
        notifications = test_db.query(Notification).filter_by(lead_id=lead.id).all()
        assert len(notifications) == 2

        contractor_notification = next(
            (n for n in notifications if n.recipient_type == "contractor"), None
        )
        customer_notification = next(
            (n for n in notifications if n.recipient_type == "customer"), None
        )

        assert contractor_notification is not None
        assert contractor_notification.recipient_id == str(contractor.id)
        assert contractor_notification.status == "sent"

        assert customer_notification is not None
        assert customer_notification.recipient_id == lead.customer_email
        assert customer_notification.status == "sent"

    @pytest.mark.asyncio
    async def test_handoff_with_lead_qualification_failure(
        self,
        orchestrator,
        test_db,
        mock_services,
        sample_lead_data,
        sample_contractor_data,
    ):
        """Test handoff workflow when lead qualification fails."""
        # Setup test data with unqualified lead
        sample_lead_data["status"] = LeadStatus.NEW
        lead, contractor = self.setup_test_data(
            test_db, sample_lead_data, sample_contractor_data
        )

        # Mock lead qualification to fail
        mock_services["lead_qualification"].is_qualified.return_value = False

        # Execute handoff workflow
        with pytest.raises(HandoffError) as exc_info:
            await orchestrator.execute_complete_handoff(lead.id)

        assert "Lead not qualified for handoff" in str(exc_info.value)

        # Verify lead status remains unchanged
        test_db.refresh(lead)
        assert lead.status == LeadStatus.NEW
        assert lead.assigned_contractor_id is None

        # Verify no notifications were sent
        mock_services["notification"].notify_contractor.assert_not_called()
        mock_services["notification"].notify_customer.assert_not_called()

    @pytest.mark.asyncio
    async def test_handoff_with_no_available_contractors(
        self,
        orchestrator,
        test_db,
        mock_services,
        sample_lead_data,
        sample_contractor_data,
    ):
        """Test handoff workflow when no contractors are available."""
        # Setup test data
        lead, contractor = self.setup_test_data(
            test_db, sample_lead_data, sample_contractor_data
        )

        # Mock services
        mock_services["lead_qualification"].is_qualified.return_value = True
        mock_services["contractor_matching"].find_best_match.return_value = None

        # Execute handoff workflow
        with pytest.raises(HandoffError) as exc_info:
            await orchestrator.execute_complete_handoff(lead.id)

        assert "No available contractors found" in str(exc_info.value)

        # Verify lead status updated to reflect no contractor available
        test_db.refresh(lead)
        assert lead.status == LeadStatus.NO_CONTRACTOR_AVAILABLE
        assert lead.assigned_contractor_id is None

    @pytest.mark.asyncio
    async def test_handoff_with_contractor_notification_failure(
        self,
        orchestrator,
        test_db,
        mock_services,
        sample_lead_data,
        sample_contractor_data,
    ):
        """Test handoff workflow when contractor notification fails."""
        # Setup test data
        lead, contractor = self.setup_test_data(
            test_db, sample_lead_data, sample_contractor_data
        )

        # Mock services
        mock_services["lead_qualification"].is_qualified.return_value = True
        mock_services["contractor_matching"].find_best_match.return_value = contractor
        mock_services["notification"].notify_contractor.side_effect = NotificationError(
            "Failed to send contractor notification"
        )

        # Execute handoff workflow
        with pytest.raises(HandoffError) as exc_info:
            await orchestrator.execute_complete_handoff(lead.id)

        assert "Failed to notify contractor" in str(exc_info.value)

        # Verify lead status updated to reflect notification failure
        test_db.refresh(lead)
        assert lead.status == LeadStatus.NOTIFICATION_FAILED
        assert lead.assigned_contractor_id == contractor.id

        # Verify failed notification logged
        failed_notification = (
            test_db.query(Notification)
            .filter_by(lead_id=lead.id, recipient_type="contractor", status="failed")
            .first()
        )
        assert failed_notification is not None

    @pytest.mark.asyncio
    async def test_handoff_with_customer_notification_failure(
        self,
        orchestrator,
        test_db,
        mock_services,
        sample_lead_data,
        sample_contractor_data,
    ):
        """Test handoff workflow when customer notification fails."""
        # Setup test data
        lead, contractor = self.setup_test_data(
            test_db, sample_lead_data, sample_contractor_data
        )

        # Mock services
        mock_services["lead_qualification"].is_qualified.return_value = True
        mock_services["contractor_matching"].find_best_match.return_value = contractor
        mock_services["notification"].notify_contractor.return_value = {
            "notification_id": "notif_123",
            "status": "sent",
            "timestamp": datetime.utcnow(),
        }
        mock_services["notification"].notify_customer.side_effect = NotificationError(
            "Failed to send customer notification"
        )

        # Execute handoff workflow
        result = await orchestrator.execute_complete_handoff(lead.id)

        # Verify partial success - contractor notified but customer notification failed
        assert result["success"] is False
        assert result["contractor_notified"] is True
        assert result["customer_notified"] is False

        # Verify lead status shows partial completion
        test_db.refresh(lead)
        assert lead.status == LeadStatus.PARTIALLY_COMPLETED
        assert lead.assigned_contractor_id == contractor.id

        # Verify notifications in database
        notifications = test_db.query(Notification).filter_by(lead_id=lead.id).all()
        contractor_notification = next(
            (n for n in notifications if n.recipient_type == "contractor"), None
        )
        customer_notification = next(
            (n for n in notifications if n.recipient_type == "customer"), None
        )

        assert contractor_notification.status == "sent"
        assert customer_notification.status == "failed"

    @pytest.mark.asyncio
    async def test_notification_logging_throughout_process(
        self,
        orchestrator,
        test_db,
        mock_services,
        sample_lead_data,
        sample_contractor_data,
    ):
        """Test that all notifications are properly logged throughout the process."""
        # Setup test data
        lead, contractor = self.setup_test_data(
            test_db, sample_lead_data, sample_contractor_data
        )

        # Mock services
        mock_services["lead_qualification"].is_qualified.return_value = True
        mock_services["contractor_matching"].find_best_match.return_value = contractor

        contractor_notification_time = datetime.utcnow()
        customer_notification_time = contractor_notification_time + timedelta(seconds=1)

        mock_services["notification"].notify_contractor.return_value = {
            "notification_id": "notif_contractor_123",
            "status": "sent",
            "timestamp": contractor_notification_time,
        }
        mock_services["notification"].notify_customer.return_value = {
            "notification_id": "notif_customer_456",
            "status": "sent",
            "timestamp": customer_notification_time,
        }

        # Execute handoff workflow
        await orchestrator.execute_complete_handoff(lead.id)

        # Verify all notification logs
        notifications = (
            test_db.query(Notification)
            .filter_by(lead_id=lead.id)
            .order_by(Notification.created_at)
            .all()
        )

        assert len(notifications) == 2

        # Verify contractor notification log
        contractor_notif = notifications[0]
        assert contractor_notif.notification_type == "lead_assignment"
        assert contractor_notif.recipient_type == "contractor"
        assert contractor_notif.recipient_id == str(contractor.id)
        assert contractor_notif.external_notification_id == "notif_contractor_123"
        assert contractor_notif.status == "sent"
        assert contractor_notif.sent_at == contractor_notification_time

        # Verify customer notification log
        customer_notif = notifications[1]
        assert customer_notif.notification_type == "contractor_assigned"
        assert customer_notif.recipient_type == "customer"
        assert customer_notif.recipient_id == lead.customer_email
        assert customer_notif.external_notification_id == "notif_customer_456"
        assert customer_notif.status == "sent"
        assert customer_notif.sent_at == customer_notification_time

    @pytest.mark.asyncio
    async def test_database_state_validation_after_successful_handoff(
        self,
        orchestrator,
        test_db,
        mock_services,
        sample_lead_data,
        sample_contractor_data,
    ):
        """Test complete database state validation after successful handoff."""
        # Setup test data
        lead, contractor = self.setup_test_data(
            test_db, sample_lead_data, sample_contractor_data
        )
        original_lead_count = test_db.query(Lead).count()
        original_contractor_count = test_db.query(Contractor).count()

        # Mock services
        mock_services["lead_qualification"].is_qualified.return_value = True
        mock_services["contractor_matching"].find_best_match.return_value = contractor
        mock_services["notification"].notify_contractor.return_value = {
            "notification_id": "notif_123",
            "status": "sent",
            "timestamp": datetime.utcnow(),
        }
        mock_services["notification"].notify_customer.return_value = {
            "notification_id": "notif_456",
            "status": "sent",
            "timestamp": datetime.utcnow(),
        }

        # Execute handoff workflow
        result = await orchestrator.execute_complete_handoff(lead.id)

        # Validate lead state
        test_db.refresh(lead)
        assert lead.status == LeadStatus.COMPLETED
        assert lead.assigned_contractor_id == contractor.id
        assert lead.handoff_completed_at is not None
        assert lead.updated_at > lead.created_at

        # Validate contractor state (should remain unchanged)
        test_db.refresh(contractor)
        assert contractor.status == ContractorStatus.ACTIVE

        # Validate notification records
        notifications = test_db.query(Notification).filter_by(lead_id=lead.id).all()
        assert len(notifications) == 2

        for notification in notifications:
            assert notification.lead_id == lead.id
            assert notification.status == "sent"
            assert notification.created_at is not None
            assert notification.sent_at is not None
            assert notification.external_notification_id is not None

        # Validate no records were deleted
        assert test_db.query(Lead).count() == original_lead_count
        assert test_db.query(Contractor).count() == original_contractor_count

        # Validate handoff record creation
        from app.database.models import Handoff

        handoffs = test_db.query(Handoff).filter_by(lead_id=lead.id).all()
        assert len(handoffs) == 1

        handoff = handoffs[0]
        assert handoff.lead_id == lead.id
        assert handoff.contractor_id == contractor.id
        assert handoff.status == "completed"
        assert handoff.completed_at is not None

    @pytest.mark.asyncio
    async def test_concurrent_handoff_requests_for_same_lead(
        self,
        orchestrator,
        test_db,
        mock_services,
        sample_lead_data,
        sample_contractor_data,
    ):
        """Test handling of concurrent handoff requests for the same lead."""
        # Setup test data
        lead, contractor = self.setup_test_data(
            test_db, sample_lead_data, sample_contractor_data
        )

        # Mock services
        mock_services["lead_qualification"].is_qualified.return_value = True
        mock_services["contractor_matching"].find_best_match.return_value = contractor
        mock_services["notification"].notify_contractor.return_value = {
            "notification_id": "notif_123",
            "status": "sent",
            "timestamp": datetime.utcnow(),
        }
        mock_services["notification"].notify_customer.return_value = {
            "notification_id": "notif_456",
            "status": "sent",
            "timestamp": datetime.utcnow(),
        }

        # Execute concurrent handoff requests
        tasks = [
            orchestrator.execute_complete_handoff(lead.id),
            orchestrator.execute_complete_handoff(lead.id),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify one succeeds and one fails
        successful_results = [
            r for r in results if isinstance(r, dict) and r.get("success")
        ]
        failed_results = [r for r in results if isinstance(r, Exception)]

        assert len(successful_results) == 1
        assert len(failed_results) == 1
        assert isinstance(failed_results[0], HandoffError)
        assert "already in progress" in str(
            failed_results[0]
        ) or "already completed" in str(failed_results[0])

        # Verify final state is consistent
        test_db.refresh(lead)
        assert lead.status == LeadStatus.COMPLETED
        assert lead.assigned_contractor_id == contractor.id

        # Verify only one set of notifications was sent
        notifications = test_db.query(Notification).filter_by(lead_id=lead.id).all()
        assert len(notifications) == 2

    @pytest.mark.asyncio
    async def test_handoff_rollback_on_partial_failure(
        self,
        orchestrator,
        test_db,
        mock_services,
        sample_lead_data,
        sample_contractor_data,
    ):
        """Test proper rollback when handoff partially fails."""
        # Setup test data
        lead, contractor = self.setup_test_data(
            test_db, sample_lead_data, sample_contractor_data
        )

        # Mock services to simulate partial failure
        mock_services["lead_qualification"].is_qualified.return_value = True
        mock_services["contractor_matching"].find_best_match.return_value = contractor
        mock_services["notification"].notify_contractor.return_value = {
            "notification_id": "notif_123",
            "status": "sent",
            "timestamp": datetime.utcnow(),
        }
        # Customer notification fails after contractor notification succeeds
        mock_services["notification"].notify_customer.side_effect = NotificationError(
            "Customer notification service unavailable"
        )

        # Execute handoff workflow
        result = await orchestrator.execute_complete_handoff(lead.id)

        # Verify partial completion state
        assert result["success"] is False
        assert result["contractor_notified"] is True
        assert result["customer_notified"] is False

        # Verify lead state reflects partial completion
        test_db.refresh(lead)
        assert lead.status == LeadStatus.PARTIALLY_COMPLETED
        assert lead.assigned_contractor_id == contractor.id

        # Verify notification logs reflect the partial state
        notifications = test_db.query(Notification).filter_by(lead_id=lead.id).all()
        assert len(notifications) == 2

        contractor_notification = next(
            n for n in notifications if n.recipient_type == "contractor"
        )
        customer_notification = next(
            n for n in notifications if n.recipient_type == "customer"
        )

        assert contractor_notification.status == "sent"
        assert customer_notification.status == "failed"
        assert (
            customer_notification.error_message
            == "Customer notification service unavailable"
        )
