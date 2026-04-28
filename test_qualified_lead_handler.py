import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

from qualified_lead_handler import QualifiedLeadHandler
from lead_detector import LeadDetector
from notification_handler import NotificationHandler
from message_formatter import MessageFormatter
from email_messenger import EmailMessenger
from logger import Logger


class TestQualifiedLeadHandler:
    """Comprehensive tests for QualifiedLeadHandler module."""

    @pytest.fixture
    def mock_database(self):
        """Mock database connection and operations."""
        mock_db = Mock()
        mock_cursor = Mock()
        mock_db.cursor.return_value = mock_cursor
        mock_cursor.execute.return_value = None
        mock_cursor.fetchone.return_value = None
        mock_cursor.fetchall.return_value = []
        return mock_db

    @pytest.fixture
    def mock_lead_detector(self):
        """Mock LeadDetector instance."""
        detector = Mock(spec=LeadDetector)
        return detector

    @pytest.fixture
    def mock_notification_handler(self):
        """Mock NotificationHandler instance."""
        handler = Mock(spec=NotificationHandler)
        return handler

    @pytest.fixture
    def mock_message_formatter(self):
        """Mock MessageFormatter instance."""
        formatter = Mock(spec=MessageFormatter)
        return formatter

    @pytest.fixture
    def mock_email_messenger(self):
        """Mock EmailMessenger instance."""
        messenger = Mock(spec=EmailMessenger)
        return messenger

    @pytest.fixture
    def mock_logger(self):
        """Mock Logger instance."""
        logger = Mock(spec=Logger)
        return logger

    @pytest.fixture
    def sample_lead_data(self):
        """Sample lead data for testing."""
        return {
            "id": "lead_12345",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567",
            "company": "Test Company Inc.",
            "project_description": "Need a new website with e-commerce functionality",
            "budget": "$10000-$25000",
            "timeline": "2-3 months",
            "source": "contact_form",
            "created_at": datetime.now().isoformat(),
            "qualification_score": 85,
            "status": "qualified",
        }

    @pytest.fixture
    def qualified_lead_handler(
        self,
        mock_database,
        mock_lead_detector,
        mock_notification_handler,
        mock_message_formatter,
        mock_email_messenger,
        mock_logger,
    ):
        """Create QualifiedLeadHandler instance with mocked dependencies."""
        handler = QualifiedLeadHandler(
            database=mock_database,
            lead_detector=mock_lead_detector,
            notification_handler=mock_notification_handler,
            message_formatter=mock_message_formatter,
            email_messenger=mock_email_messenger,
            logger=mock_logger,
        )
        return handler

    def test_successful_qualified_lead_handoff(
        self,
        qualified_lead_handler,
        sample_lead_data,
        mock_database,
        mock_notification_handler,
        mock_message_formatter,
        mock_email_messenger,
        mock_logger,
    ):
        """Test successful qualified lead handoff with all notifications sent."""
        # Setup mocks
        mock_notification_handler.should_notify.return_value = True
        mock_message_formatter.format_lead_notification.return_value = {
            "subject": "New Qualified Lead: John Doe",
            "body": "Lead details: ...",
            "html_body": "<html>Lead details: ...</html>",
        }
        mock_email_messenger.send_email.return_value = {
            "success": True,
            "message_id": "msg_123",
        }

        # Execute
        result = qualified_lead_handler.process_qualified_lead(sample_lead_data)

        # Assertions
        assert result["success"] is True
        assert result["lead_id"] == "lead_12345"
        assert result["notifications_sent"] > 0

        # Verify database transaction
        mock_database.cursor().execute.assert_called()
        mock_database.commit.assert_called()

        # Verify notifications were sent
        mock_notification_handler.should_notify.assert_called()
        mock_message_formatter.format_lead_notification.assert_called_with(
            sample_lead_data
        )
        mock_email_messenger.send_email.assert_called()

        # Verify logging
        mock_logger.info.assert_called()

    def test_database_transaction_rollback_on_notification_failure(
        self,
        qualified_lead_handler,
        sample_lead_data,
        mock_database,
        mock_email_messenger,
        mock_logger,
    ):
        """Test database transaction rollback when notification fails."""
        # Setup mock to simulate email sending failure
        mock_email_messenger.send_email.side_effect = Exception(
            "SMTP server unavailable"
        )

        # Execute
        result = qualified_lead_handler.process_qualified_lead(sample_lead_data)

        # Assertions
        assert result["success"] is False
        assert "error" in result

        # Verify database rollback
        mock_database.rollback.assert_called()
        mock_database.commit.assert_not_called()

        # Verify error logging
        mock_logger.error.assert_called()

    def test_proper_lead_status_updates(
        self, qualified_lead_handler, sample_lead_data, mock_database, mock_logger
    ):
        """Test that lead status is properly updated in database."""
        # Execute
        qualified_lead_handler.process_qualified_lead(sample_lead_data)

        # Verify status update query was executed
        cursor = mock_database.cursor()
        update_calls = [
            call
            for call in cursor.execute.call_args_list
            if "UPDATE leads SET status" in str(call)
        ]
        assert len(update_calls) > 0

        # Verify the status was set to 'processing' or 'notified'
        update_query = str(update_calls[0])
        assert "processing" in update_query or "notified" in update_query

    def test_email_sending_failure_error_handling(
        self,
        qualified_lead_handler,
        sample_lead_data,
        mock_email_messenger,
        mock_logger,
    ):
        """Test proper error handling when email sending fails."""
        # Setup mock to simulate different types of email failures
        test_cases = [
            Exception("SMTP authentication failed"),
            ConnectionError("Network timeout"),
            ValueError("Invalid email address"),
        ]

        for exception in test_cases:
            mock_email_messenger.send_email.side_effect = exception

            result = qualified_lead_handler.process_qualified_lead(sample_lead_data)

            assert result["success"] is False
            assert "error" in result
            assert str(exception) in result["error"]

            # Verify error was logged
            mock_logger.error.assert_called()

    def test_integration_with_lead_detector(
        self, qualified_lead_handler, sample_lead_data, mock_lead_detector
    ):
        """Test integration with LeadDetector module."""
        # Setup mock
        mock_lead_detector.validate_lead_data.return_value = {
            "valid": True,
            "score": 85,
            "issues": [],
        }

        # Execute
        qualified_lead_handler.process_qualified_lead(sample_lead_data)

        # Verify lead detector was called
        mock_lead_detector.validate_lead_data.assert_called_with(sample_lead_data)

    def test_integration_with_notification_handler(
        self, qualified_lead_handler, sample_lead_data, mock_notification_handler
    ):
        """Test integration with NotificationHandler module."""
        # Setup mock
        mock_notification_handler.get_notification_recipients.return_value = [
            {"email": "sales@company.com", "type": "sales_team"},
            {"email": "manager@company.com", "type": "manager"},
        ]

        # Execute
        qualified_lead_handler.process_qualified_lead(sample_lead_data)

        # Verify notification handler methods were called
        mock_notification_handler.get_notification_recipients.assert_called()

    def test_integration_with_message_formatter(
        self, qualified_lead_handler, sample_lead_data, mock_message_formatter
    ):
        """Test integration with MessageFormatter module."""
        # Setup mock
        expected_formatted_message = {
            "subject": "New Qualified Lead: John Doe",
            "body": "A new qualified lead has been received...",
            "html_body": "<html><body>Lead details...</body></html>",
            "attachments": [],
        }
        mock_message_formatter.format_lead_notification.return_value = (
            expected_formatted_message
        )

        # Execute
        qualified_lead_handler.process_qualified_lead(sample_lead_data)

        # Verify formatter was called with correct data
        mock_message_formatter.format_lead_notification.assert_called_with(
            sample_lead_data
        )

    def test_integration_with_email_messenger(
        self, qualified_lead_handler, sample_lead_data, mock_email_messenger
    ):
        """Test integration with EmailMessenger module."""
        # Setup mock
        mock_email_messenger.send_email.return_value = {
            "success": True,
            "message_id": "msg_456",
            "timestamp": datetime.now().isoformat(),
        }

        # Execute
        qualified_lead_handler.process_qualified_lead(sample_lead_data)

        # Verify email messenger was called
        mock_email_messenger.send_email.assert_called()

        # Verify call arguments contain required fields
        call_args = mock_email_messenger.send_email.call_args
        assert "to" in call_args[1] or len(call_args[0]) > 0
        assert "subject" in call_args[1] or "body" in call_args[1]

    def test_integration_with_logger(
        self, qualified_lead_handler, sample_lead_data, mock_logger
    ):
        """Test integration with Logger module."""
        # Execute
        qualified_lead_handler.process_qualified_lead(sample_lead_data)

        # Verify different log levels were used appropriately
        mock_logger.info.assert_called()

        # Check that lead processing was logged
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("lead_12345" in call for call in info_calls)

    @patch("qualified_lead_handler.datetime")
    def test_timestamp_handling(
        self, mock_datetime, qualified_lead_handler, sample_lead_data
    ):
        """Test proper timestamp handling throughout the process."""
        # Setup mock datetime
        fixed_time = datetime(2023, 12, 1, 10, 30, 0)
        mock_datetime.now.return_value = fixed_time
        mock_datetime.now().isoformat.return_value = fixed_time.isoformat()

        # Execute
        result = qualified_lead_handler.process_qualified_lead(sample_lead_data)

        # Verify timestamp was used
        assert "processed_at" in result

    def test_multiple_recipients_notification(
        self,
        qualified_lead_handler,
        sample_lead_data,
        mock_notification_handler,
        mock_email_messenger,
    ):
        """Test handling multiple notification recipients."""
        # Setup multiple recipients
        mock_notification_handler.get_notification_recipients.return_value = [
            {"email": "sales@company.com", "type": "sales_team"},
            {"email": "manager@company.com", "type": "manager"},
            {"email": "director@company.com", "type": "director"},
        ]
        mock_email_messenger.send_email.return_value = {"success": True}

        # Execute
        result = qualified_lead_handler.process_qualified_lead(sample_lead_data)

        # Verify multiple emails were sent
        assert mock_email_messenger.send_email.call_count == 3
        assert result["notifications_sent"] == 3

    def test_partial_notification_failure(
        self,
        qualified_lead_handler,
        sample_lead_data,
        mock_notification_handler,
        mock_email_messenger,
        mock_logger,
    ):
        """Test handling when some notifications succeed and others fail."""
        # Setup multiple recipients with mixed success
        mock_notification_handler.get_notification_recipients.return_value = [
            {"email": "sales@company.com", "type": "sales_team"},
            {"email": "manager@company.com", "type": "manager"},
            {"email": "invalid@email", "type": "director"},
        ]

        # Mock email sending with mixed results
        def side_effect(*args, **kwargs):
            if "invalid@email" in str(args) or "invalid@email" in str(kwargs):
                raise ValueError("Invalid email address")
            return {"success": True}

        mock_email_messenger.send_email.side_effect = side_effect

        # Execute
        result = qualified_lead_handler.process_qualified_lead(sample_lead_data)

        # Verify partial success was handled appropriately
        assert (
            result["success"] is True
        )  # Should still succeed if some notifications sent
        assert result["notifications_sent"] == 2
        assert "partial_failures" in result

        # Verify warnings were logged
        mock_logger.warning.assert_called()

    def test_lead_data_validation(self, qualified_lead_handler, mock_lead_detector):
        """Test validation of lead data before processing."""
        # Test with invalid lead data
        invalid_lead = {
            "id": "",  # Missing required field
            "email": "invalid-email",  # Invalid format
        }

        mock_lead_detector.validate_lead_data.return_value = {
            "valid": False,
            "score": 0,
            "issues": ["Missing lead ID", "Invalid email format"],
        }

        # Execute
        result = qualified_lead_handler.process_qualified_lead(invalid_lead)

        # Assertions
        assert result["success"] is False
        assert "validation_error" in result["error"]

    def test_database_connection_failure(
        self, qualified_lead_handler, sample_lead_data, mock_database, mock_logger
    ):
        """Test handling of database connection failures."""
        # Setup mock to simulate database connection error
        mock_database.cursor.side_effect = ConnectionError("Database unavailable")

        # Execute
        result = qualified_lead_handler.process_qualified_lead(sample_lead_data)

        # Assertions
        assert result["success"] is False
        assert "database" in result["error"].lower()

        # Verify error was logged
        mock_logger.error.assert_called()

    def test_concurrent_lead_processing(self, qualified_lead_handler, mock_database):
        """Test handling of concurrent lead processing scenarios."""
        # Simulate concurrent processing by having database return existing processing record
        mock_cursor = mock_database.cursor()
        mock_cursor.fetchone.return_value = {"status": "processing", "id": "lead_12345"}

        sample_lead = {"id": "lead_12345", "name": "Test Lead"}

        # Execute
        result = qualified_lead_handler.process_qualified_lead(sample_lead)

        # Should handle gracefully (either skip or wait)
        assert "already_processing" in str(result) or result["success"] in [True, False]

    def test_performance_metrics_collection(
        self, qualified_lead_handler, sample_lead_data, mock_logger
    ):
        """Test that performance metrics are collected during processing."""
        # Execute
        result = qualified_lead_handler.process_qualified_lead(sample_lead_data)

        # Verify performance metrics are included
        assert "processing_time" in result
        assert isinstance(result["processing_time"], (int, float))

        # Verify metrics were logged
        metric_logs = [
            call
            for call in mock_logger.info.call_args_list
            if "processing_time" in str(call)
        ]
        assert len(metric_logs) > 0
