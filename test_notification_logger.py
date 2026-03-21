import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from notification_logger import (
    NotificationLogger,
    NotificationEntry,
    NotificationStatus,
    NotificationType,
    ContractorNotification,
    CustomerHandoffMessage,
    DeliveryStatusUpdate
)
from database import get_async_session
from exceptions import DatabaseError, ValidationError


class TestNotificationLogger:
    @pytest.fixture
    def mock_session(self):
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def notification_logger(self, mock_session):
        logger = NotificationLogger()
        logger._session = mock_session
        return logger

    @pytest.fixture
    def sample_contractor_notification(self):
        return ContractorNotification(
            contractor_id="contractor_123",
            message="New delivery request available",
            delivery_id="delivery_456",
            urgency_level="high",
            location_data={"lat": 40.7128, "lng": -74.0060},
            metadata={"route_id": "route_789"}
        )

    @pytest.fixture
    def sample_customer_handoff(self):
        return CustomerHandoffMessage(
            customer_id="customer_123",
            delivery_id="delivery_456",
            message="Your package has been handed off to our delivery partner",
            tracking_number="TRK123456789",
            estimated_delivery=datetime.now(timezone.utc) + timedelta(hours=2),
            handoff_location="Distribution Center A"
        )

    @pytest.fixture
    def sample_status_update(self):
        return DeliveryStatusUpdate(
            delivery_id="delivery_456",
            old_status="in_transit",
            new_status="delivered",
            location={"lat": 40.7128, "lng": -74.0060},
            notes="Package delivered to front door",
            delivery_proof={"signature": "John Doe", "photo_url": "https://example.com/photo.jpg"}
        )

    @pytest.mark.asyncio
    async def test_log_contractor_notification_success(self, notification_logger, mock_session, sample_contractor_notification):
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        with patch('notification_logger.datetime') as mock_datetime:
            fixed_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = fixed_time
            
            result = await notification_logger.log_contractor_notification(sample_contractor_notification)
            
            assert result is not None
            assert result.notification_type == NotificationType.CONTRACTOR
            assert result.recipient_id == "contractor_123"
            assert result.message == "New delivery request available"
            assert result.delivery_id == "delivery_456"
            assert result.status == NotificationStatus.SENT
            assert result.created_at == fixed_time
            
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_contractor_notification_with_proper_timestamps(self, notification_logger, mock_session, sample_contractor_notification):
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        before_time = datetime.now(timezone.utc)
        
        result = await notification_logger.log_contractor_notification(sample_contractor_notification)
        
        after_time = datetime.now(timezone.utc)
        
        assert before_time <= result.created_at <= after_time
        assert result.created_at.tzinfo == timezone.utc

    @pytest.mark.asyncio
    async def test_log_contractor_notification_database_error(self, notification_logger, mock_session, sample_contractor_notification):
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock(side_effect=Exception("Database connection lost"))
        mock_session.rollback = AsyncMock()
        
        with pytest.raises(DatabaseError) as exc_info:
            await notification_logger.log_contractor_notification(sample_contractor_notification)
        
        assert "Failed to log contractor notification" in str(exc_info.value)
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_customer_handoff_message_success(self, notification_logger, mock_session, sample_customer_handoff):
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        result = await notification_logger.log_customer_handoff_message(sample_customer_handoff)
        
        assert result is not None
        assert result.notification_type == NotificationType.CUSTOMER_HANDOFF
        assert result.recipient_id == "customer_123"
        assert result.delivery_id == "delivery_456"
        assert result.message == "Your package has been handed off to our delivery partner"
        assert result.metadata["tracking_number"] == "TRK123456789"
        assert result.metadata["handoff_location"] == "Distribution Center A"
        assert "estimated_delivery" in result.metadata

    @pytest.mark.asyncio
    async def test_log_customer_handoff_message_validation_error(self, notification_logger, mock_session):
        invalid_handoff = CustomerHandoffMessage(
            customer_id="",  # Invalid empty customer_id
            delivery_id="delivery_456",
            message="Test message",
            tracking_number="TRK123456789",
            estimated_delivery=datetime.now(timezone.utc),
            handoff_location="Test Location"
        )
        
        with pytest.raises(ValidationError) as exc_info:
            await notification_logger.log_customer_handoff_message(invalid_handoff)
        
        assert "Invalid customer handoff data" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_log_delivery_status_update_success(self, notification_logger, mock_session, sample_status_update):
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        result = await notification_logger.log_delivery_status_update(sample_status_update)
        
        assert result is not None
        assert result.notification_type == NotificationType.STATUS_UPDATE
        assert result.delivery_id == "delivery_456"
        assert result.metadata["old_status"] == "in_transit"
        assert result.metadata["new_status"] == "delivered"
        assert result.metadata["location"] == {"lat": 40.7128, "lng": -74.0060}
        assert result.metadata["notes"] == "Package delivered to front door"

    @pytest.mark.asyncio
    async def test_log_delivery_status_update_with_proof(self, notification_logger, mock_session, sample_status_update):
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        result = await notification_logger.log_delivery_status_update(sample_status_update)
        
        assert result.metadata["delivery_proof"]["signature"] == "John Doe"
        assert result.metadata["delivery_proof"]["photo_url"] == "https://example.com/photo.jpg"

    @pytest.mark.asyncio
    async def test_query_notification_history_by_delivery_id(self, notification_logger, mock_session):
        # Mock query results
        mock_notifications = [
            NotificationEntry(
                id="notif_1",
                notification_type=NotificationType.CONTRACTOR,
                recipient_id="contractor_123",
                delivery_id="delivery_456",
                message="Test message 1",
                status=NotificationStatus.SENT,
                created_at=datetime.now(timezone.utc)
            ),
            NotificationEntry(
                id="notif_2",
                notification_type=NotificationType.STATUS_UPDATE,
                delivery_id="delivery_456",
                message="Status updated",
                status=NotificationStatus.DELIVERED,
                created_at=datetime.now(timezone.utc)
            )
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_notifications
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await notification_logger.query_notification_history(delivery_id="delivery_456")
        
        assert len(result) == 2
        assert all(notif.delivery_id == "delivery_456" for notif in result)
        assert result[0].notification_type == NotificationType.CONTRACTOR
        assert result[1].notification_type == NotificationType.STATUS_UPDATE

    @pytest.mark.asyncio
    async def test_query_notification_history_by_recipient_id(self, notification_logger, mock_session):
        mock_notifications = [
            NotificationEntry(
                id="notif_3",
                notification_type=NotificationType.CONTRACTOR,
                recipient_id="contractor_123",
                delivery_id="delivery_789",
                message="Test message",
                status=NotificationStatus.SENT,
                created_at=datetime.now(timezone.utc)
            )
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_notifications
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await notification_logger.query_notification_history(recipient_id="contractor_123")
        
        assert len(result) == 1
        assert result[0].recipient_id == "contractor_123"

    @pytest.mark.asyncio
    async def test_query_notification_history_with_date_range(self, notification_logger, mock_session):
        start_date = datetime.now(timezone.utc) - timedelta(days=7)
        end_date = datetime.now(timezone.utc)
        
        mock_notifications = []
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_notifications
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await notification_logger.query_notification_history(
            delivery_id="delivery_456",
            start_date=start_date,
            end_date=end_date
        )
        
        assert isinstance(result, list)
        # Verify that the query was called with date range filters
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args[0][0]
        assert "created_at" in str(call_args)

    @pytest.mark.asyncio
    async def test_query_notification_history_with_status_filter(self, notification_logger, mock_session):
        mock_notifications = [
            NotificationEntry(
                id="notif_4",
                notification_type=NotificationType.CONTRACTOR,
                recipient_id="contractor_123",
                delivery_id="delivery_456",
                message="Test message",
                status=NotificationStatus.DELIVERED,
                created_at=datetime.now(timezone.utc)
            )
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_notifications
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await notification_logger.query_notification_history(
            delivery_id="delivery_456",
            status=NotificationStatus.DELIVERED
        )
        
        assert len(result) == 1
        assert result[0].status == NotificationStatus.DELIVERED

    @pytest.mark.asyncio
    async def test_query_notification_history_empty_result(self, notification_logger, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await notification_logger.query_notification_history(delivery_id="nonexistent_delivery")
        
        assert result == []

    @pytest.mark.asyncio
    async def test_query_notification_history_database_error(self, notification_logger, mock_session):
        mock_session.execute = AsyncMock(side_effect=Exception("Database query failed"))
        
        with pytest.raises(DatabaseError) as exc_info:
            await notification_logger.query_notification_history(delivery_id="delivery_456")
        
        assert "Failed to query notification history" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_notification_status_success(self, notification_logger, mock_session):
        mock_notification = NotificationEntry(
            id="notif_1",
            notification_type=NotificationType.CONTRACTOR,
            recipient_id="contractor_123",
            delivery_id="delivery_456",
            message="Test message",
            status=NotificationStatus.SENT,
            created_at=datetime.now(timezone.utc)
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_notification
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        
        result = await notification_logger.update_notification_status("notif_1", NotificationStatus.DELIVERED)
        
        assert result is not None
        assert result.status == NotificationStatus.DELIVERED
        assert result.delivered_at is not None
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_notification_status_not_found(self, notification_logger, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await notification_logger.update_notification_status("nonexistent_id", NotificationStatus.DELIVERED)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_notification_stats_success(self, notification_logger, mock_session):
        # Mock aggregate query results
        mock_stats_result = MagicMock()
        mock_stats_result.fetchall.return_value = [
            (NotificationStatus.SENT, 10),
            (NotificationStatus.DELIVERED, 8),
            (NotificationStatus.FAILED, 2)
        ]
        mock_session.execute = AsyncMock(return_value=mock_stats_result)
        
        stats = await notification_logger.get_notification_stats(delivery_id="delivery_456")
        
        expected_stats = {
            "total_notifications": 20,
            "by_status": {
                NotificationStatus.SENT: 10,
                NotificationStatus.DELIVERED: 8,
                NotificationStatus.FAILED: 2
            },
            "delivery_rate": 0.4,  # 8/20
            "failure_rate": 0.1    # 2/20
        }
        
        assert stats == expected_stats

    @pytest.mark.asyncio
    async def test_bulk_update_notification_status(self, notification_logger, mock_session):
        notification_ids = ["notif_1", "notif_2", "notif_3"]
        new_status = NotificationStatus.FAILED
        
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        
        result = await notification_logger.bulk_update_notification_status(notification_ids, new_status)
        
        assert result == len(notification_ids)
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()


class TestNotificationLoggerDatabaseIntegration:
    @pytest.fixture
    async def db_session(self):
        """Create a real database session for integration tests"""
        async with get_async_session() as session:
            yield session

    @pytest.fixture
    def notification_logger_with_db(self, db_session):
        logger = NotificationLogger()
        logger._session = db_session
        return logger

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_contractor_notification_flow(self, notification_logger_with_db, db_session):
        """Test complete flow from logging to querying contractor notifications"""
        contractor_notification = ContractorNotification(
            contractor_id="test_contractor_integration",
            message="Integration test notification",
            delivery_id="test_delivery_integration",
            urgency_level="medium",
            location_data={"lat": 40.7128, "lng": -74.0060},
            metadata={"test": "integration"}
        )
        
        # Log the notification
        logged_notification = await notification_logger_with_db.log_contractor_notification(contractor_notification)
        assert logged_notification.id is not None
        
        # Query it back
        history = await notification_logger_with_db.query_notification_history(
            delivery_id="test_delivery_integration"
        )
        assert len(history) == 1
        assert history[0].id == logged_notification.id
        assert history[0].recipient_id == "test_contractor_integration"
        
        # Update status
        updated = await notification_logger_with_db.update_notification_status(
            logged_notification.id, NotificationStatus.DELIVERED
        )
        assert updated.status == NotificationStatus.DELIVERED
        assert updated.delivered_at is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_customer_handoff_flow(self, notification_logger_with_db, db_session):
        """Test complete flow for customer handoff messages"""
        handoff_message = CustomerHandoffMessage(
            customer_id="test_customer_integration",
            delivery_id="test_delivery_handoff",
            message="Integration test handoff message",
            tracking_number="INTTEST123",
            estimated_delivery=datetime.now(timezone.utc) + timedelta(hours=3),
            handoff_location="Integration Test Center"
        )
        
        # Log the handoff message
        logged_handoff = await notification_logger_with_db.log_customer_handoff_message(handoff_message)
        assert logged_handoff.id is not None
        assert logged_handoff.notification_type == NotificationType.CUSTOMER_HANDOFF
        
        # Query by customer
        customer_history = await notification_logger_with_db.query_notification_history(
            recipient_id="test_customer_integration"
        )
        assert len(customer_history) >= 1
        assert any(h.id == logged_handoff.id for h in customer_history)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_notification_logging(self, notification_logger_with_db):
        """Test concurrent notification logging to ensure database consistency"""
        async def create_notification(index):
            notification = ContractorNotification(
                contractor_id=f"contractor_{index}",
                message=f"Concurrent test message {index}",
                delivery_id=f"delivery_{index}",
                urgency_level="low",
                location_data={"lat": 40.7128, "lng": -74.0060},
                metadata={"concurrent_test": True, "index": index}
            )
            return await notification_logger_with_db.log_contractor_notification(notification)
        
        # Create 10 concurrent notifications
        tasks = [create_notification(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Verify all were created successfully
        assert len(results) == 10
        assert all(r.id is not None for r in results)
        assert len(set(r.id for r in results)) == 10  # All IDs are unique

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_notification_stats_integration(self, notification_logger_with_db):
        """Test notification statistics calculation with real data"""
        delivery_id = "stats_test_delivery"
        
        # Create notifications with different statuses
        notifications = []
        for i in range(5):
            notification = ContractorNotification(
                contractor_id=f"stats_contractor_{i}",
                message=f"Stats test message {i}",
                delivery_id=delivery_id,
                urgency_level="low",
                location_data={"lat": 40.7128, "lng": -74.0060},
                metadata={"stats_test": True}
            )
            logged = await notification_logger_with_db.log_contractor_notification(notification)
            notifications.append(logged)
        
        # Update some to delivered
        for notification in notifications[:3]:
            await notification_logger_with_db.update_notification_status(
                notification.id, NotificationStatus.DELIVERED
            )
        
        # Update one to failed
        await notification_logger_with_db.update_notification_status(
            notifications[3].id, NotificationStatus.FAILED
        )
        
        # Get stats
        stats = await notification_logger_with_db.get_notification_stats(delivery_id=delivery_id)
        
        assert stats["total_notifications"] == 5
        assert stats["by_status"][NotificationStatus.DELIVERED] == 3
        assert stats["by_status"][NotificationStatus.FAILED] == 1
        assert stats["by_status"][NotificationStatus.SENT] == 1
        assert stats["delivery_rate"] == 0.6  # 3/5
        assert stats["failure_rate"] == 0.2   # 1/5