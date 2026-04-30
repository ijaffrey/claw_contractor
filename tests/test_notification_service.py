# W1-D skip sweep — see docs/W1D_RECONCILIATION_MANIFEST.md
# Reason: escalation #2 (notification service architecture); imports phantom backend
import pytest
pytest.skip("W1-D: escalation #2 (notification service architecture); imports phantom backend", allow_module_level=True)

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timezone
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from backend.services.notification_service import NotificationService
from backend.core.database import get_database
from backend.core.exceptions import (
    NotificationServiceError,
    EmailDeliveryError,
    TemplateRenderingError,
    DatabaseError,
)


class TestNotificationService:
    """Comprehensive unit tests for NotificationService."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.close = AsyncMock()
        return session

    @pytest.fixture
    def mock_smtp_server(self):
        """Mock SMTP server."""
        server = Mock(spec=smtplib.SMTP)
        server.starttls = Mock()
        server.login = Mock()
        server.send_message = Mock()
        server.quit = Mock()
        return server

    @pytest.fixture
    def notification_service(self, mock_db_session):
        """Create NotificationService instance with mocked dependencies."""
        with patch("backend.services.notification_service.get_database") as mock_get_db:
            mock_get_db.return_value = mock_db_session
            service = NotificationService()
            service.db = mock_db_session
            return service

    @pytest.fixture
    def sample_email_data(self):
        """Sample email data for testing."""
        return {
            "to_email": "test@example.com",
            "subject": "Test Subject",
            "template_name": "welcome",
            "template_data": {
                "username": "testuser",
                "activation_link": "https://example.com/activate/123",
            },
        }

    @pytest.fixture
    def sample_notification_record(self):
        """Sample notification record for database testing."""
        return {
            "id": 1,
            "recipient_email": "test@example.com",
            "subject": "Test Subject",
            "template_name": "welcome",
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
            "sent_at": None,
            "error_message": None,
            "retry_count": 0,
        }


class TestEmailSending:
    """Test email sending functionality."""

    @pytest.mark.asyncio
    async def test_send_email_success(
        self, notification_service, mock_smtp_server, sample_email_data
    ):
        """Test successful email sending."""
        with patch("smtplib.SMTP") as mock_smtp_class:
            mock_smtp_class.return_value.__enter__.return_value = mock_smtp_server

            with patch.object(notification_service, "_render_template") as mock_render:
                mock_render.return_value = "<html><body>Welcome testuser!</body></html>"

                with patch.object(
                    notification_service, "_log_notification"
                ) as mock_log:
                    result = await notification_service.send_email(**sample_email_data)

                    assert result is True
                    mock_smtp_server.starttls.assert_called_once()
                    mock_smtp_server.login.assert_called_once()
                    mock_smtp_server.send_message.assert_called_once()
                    mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_smtp_connection_error(
        self, notification_service, sample_email_data
    ):
        """Test email sending with SMTP connection error."""
        with patch("smtplib.SMTP") as mock_smtp_class:
            mock_smtp_class.side_effect = smtplib.SMTPConnectError("Connection failed")

            with pytest.raises(EmailDeliveryError) as exc_info:
                await notification_service.send_email(**sample_email_data)

            assert "SMTP connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_email_authentication_error(
        self, notification_service, mock_smtp_server, sample_email_data
    ):
        """Test email sending with authentication error."""
        with patch("smtplib.SMTP") as mock_smtp_class:
            mock_smtp_class.return_value.__enter__.return_value = mock_smtp_server
            mock_smtp_server.login.side_effect = smtplib.SMTPAuthenticationError(
                535, "Authentication failed"
            )

            with pytest.raises(EmailDeliveryError) as exc_info:
                await notification_service.send_email(**sample_email_data)

            assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_email_recipient_error(
        self, notification_service, mock_smtp_server, sample_email_data
    ):
        """Test email sending with recipient error."""
        with patch("smtplib.SMTP") as mock_smtp_class:
            mock_smtp_class.return_value.__enter__.return_value = mock_smtp_server
            mock_smtp_server.send_message.side_effect = smtplib.SMTPRecipientsRefused(
                {"test@example.com": (550, "Mailbox unavailable")}
            )

            with pytest.raises(EmailDeliveryError) as exc_info:
                await notification_service.send_email(**sample_email_data)

            assert "Recipients refused" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_email_invalid_email_format(self, notification_service):
        """Test email sending with invalid email format."""
        invalid_data = {
            "to_email": "invalid-email",
            "subject": "Test",
            "template_name": "welcome",
            "template_data": {},
        }

        with pytest.raises(NotificationServiceError) as exc_info:
            await notification_service.send_email(**invalid_data)

        assert "Invalid email format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_bulk_emails_success(
        self, notification_service, mock_smtp_server
    ):
        """Test successful bulk email sending."""
        recipients = [
            {"to_email": "user1@example.com", "template_data": {"username": "user1"}},
            {"to_email": "user2@example.com", "template_data": {"username": "user2"}},
            {"to_email": "user3@example.com", "template_data": {"username": "user3"}},
        ]

        with patch("smtplib.SMTP") as mock_smtp_class:
            mock_smtp_class.return_value.__enter__.return_value = mock_smtp_server

            with patch.object(notification_service, "_render_template") as mock_render:
                mock_render.return_value = "<html><body>Welcome!</body></html>"

                results = await notification_service.send_bulk_emails(
                    recipients=recipients, subject="Welcome", template_name="welcome"
                )

                assert len(results) == 3
                assert all(result["success"] for result in results)
                assert mock_smtp_server.send_message.call_count == 3

    @pytest.mark.asyncio
    async def test_send_bulk_emails_partial_failure(
        self, notification_service, mock_smtp_server
    ):
        """Test bulk email sending with partial failures."""
        recipients = [
            {"to_email": "user1@example.com", "template_data": {"username": "user1"}},
            {"to_email": "invalid-email", "template_data": {"username": "user2"}},
            {"to_email": "user3@example.com", "template_data": {"username": "user3"}},
        ]

        with patch("smtplib.SMTP") as mock_smtp_class:
            mock_smtp_class.return_value.__enter__.return_value = mock_smtp_server

            with patch.object(notification_service, "_render_template") as mock_render:
                mock_render.return_value = "<html><body>Welcome!</body></html>"

                results = await notification_service.send_bulk_emails(
                    recipients=recipients, subject="Welcome", template_name="welcome"
                )

                assert len(results) == 3
                assert results[0]["success"] is True
                assert results[1]["success"] is False
                assert results[2]["success"] is True
                assert "Invalid email format" in results[1]["error"]


class TestTemplateRendering:
    """Test template rendering functionality."""

    def test_render_template_success(self, notification_service):
        """Test successful template rendering."""
        template_name = "welcome"
        template_data = {
            "username": "testuser",
            "activation_link": "https://example.com/activate/123",
        }

        with patch("jinja2.Environment") as mock_env_class:
            mock_env = Mock()
            mock_template = Mock()
            mock_template.render.return_value = (
                "<html><body>Welcome testuser!</body></html>"
            )
            mock_env.get_template.return_value = mock_template
            mock_env_class.return_value = mock_env

            # Patch the environment creation in the service
            notification_service._jinja_env = mock_env

            result = notification_service._render_template(template_name, template_data)

            assert result == "<html><body>Welcome testuser!</body></html>"
            mock_env.get_template.assert_called_once_with(f"{template_name}.html")
            mock_template.render.assert_called_once_with(**template_data)

    def test_render_template_missing_template(self, notification_service):
        """Test template rendering with missing template file."""
        with patch("jinja2.Environment") as mock_env_class:
            mock_env = Mock()
            mock_env.get_template.side_effect = jinja2.TemplateNotFound("welcome.html")
            mock_env_class.return_value = mock_env
            notification_service._jinja_env = mock_env

            with pytest.raises(TemplateRenderingError) as exc_info:
                notification_service._render_template("welcome", {})

            assert "Template not found: welcome.html" in str(exc_info.value)

    def test_render_template_syntax_error(self, notification_service):
        """Test template rendering with syntax error in template."""
        with patch("jinja2.Environment") as mock_env_class:
            mock_env = Mock()
            mock_env.get_template.side_effect = jinja2.TemplateSyntaxError(
                "Unexpected end of template", lineno=5
            )
            mock_env_class.return_value = mock_env
            notification_service._jinja_env = mock_env

            with pytest.raises(TemplateRenderingError) as exc_info:
                notification_service._render_template("welcome", {})

            assert "Template syntax error" in str(exc_info.value)

    def test_render_template_undefined_variable(self, notification_service):
        """Test template rendering with undefined variable."""
        with patch("jinja2.Environment") as mock_env_class:
            mock_env = Mock()
            mock_template = Mock()
            mock_template.render.side_effect = jinja2.UndefinedError(
                "'username' is undefined"
            )
            mock_env.get_template.return_value = mock_template
            mock_env_class.return_value = mock_env
            notification_service._jinja_env = mock_env

            with pytest.raises(TemplateRenderingError) as exc_info:
                notification_service._render_template("welcome", {})

            assert "Template variable error" in str(exc_info.value)


class TestDatabaseOperations:
    """Test database operations and logging."""

    @pytest.mark.asyncio
    async def test_log_notification_success(
        self, notification_service, sample_notification_record
    ):
        """Test successful notification logging."""
        notification_data = {
            "recipient_email": "test@example.com",
            "subject": "Test Subject",
            "template_name": "welcome",
            "status": "sent",
        }

        mock_result = Mock()
        mock_result.scalar_one.return_value = 1
        notification_service.db.execute.return_value = mock_result

        notification_id = await notification_service._log_notification(
            **notification_data
        )

        assert notification_id == 1
        notification_service.db.execute.assert_called_once()
        notification_service.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_notification_database_error(self, notification_service):
        """Test notification logging with database error."""
        notification_data = {
            "recipient_email": "test@example.com",
            "subject": "Test Subject",
            "template_name": "welcome",
            "status": "sent",
        }

        notification_service.db.execute.side_effect = Exception(
            "Database connection failed"
        )

        with pytest.raises(DatabaseError) as exc_info:
            await notification_service._log_notification(**notification_data)

        assert "Failed to log notification" in str(exc_info.value)
        notification_service.db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_notification_status_success(self, notification_service):
        """Test successful notification status update."""
        notification_id = 1
        status = "delivered"

        await notification_service._update_notification_status(notification_id, status)

        notification_service.db.execute.assert_called_once()
        notification_service.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_notification_status_with_error(self, notification_service):
        """Test notification status update with error message."""
        notification_id = 1
        status = "failed"
        error_message = "SMTP connection failed"

        await notification_service._update_notification_status(
            notification_id, status, error_message
        )

        notification_service.db.execute.assert_called_once()
        notification_service.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_notification_history(
        self, notification_service, sample_notification_record
    ):
        """Test retrieving notification history."""
        email = "test@example.com"

        mock_result = Mock()
        mock_result.fetchall.return_value = [sample_notification_record]
        notification_service.db.execute.return_value = mock_result

        history = await notification_service.get_notification_history(email)

        assert len(history) == 1
        assert history[0]["recipient_email"] == email
        notification_service.db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_failed_notifications(
        self, notification_service, sample_notification_record
    ):
        """Test retrieving failed notifications for retry."""
        failed_record = sample_notification_record.copy()
        failed_record["status"] = "failed"
        failed_record["retry_count"] = 1

        mock_result = Mock()
        mock_result.fetchall.return_value = [failed_record]
        notification_service.db.execute.return_value = mock_result

        failed_notifications = await notification_service.get_failed_notifications(
            max_retries=3
        )

        assert len(failed_notifications) == 1
        assert failed_notifications[0]["status"] == "failed"
        notification_service.db.execute.assert_called_once()


class TestErrorHandling:
    """Test comprehensive error handling."""

    @pytest.mark.asyncio
    async def test_retry_failed_notifications_success(
        self, notification_service, mock_smtp_server
    ):
        """Test successful retry of failed notifications."""
        failed_notification = {
            "id": 1,
            "recipient_email": "test@example.com",
            "subject": "Test Subject",
            "template_name": "welcome",
            "template_data": {"username": "testuser"},
            "retry_count": 1,
        }

        with patch.object(
            notification_service, "get_failed_notifications"
        ) as mock_get_failed:
            mock_get_failed.return_value = [failed_notification]

            with patch("smtplib.SMTP") as mock_smtp_class:
                mock_smtp_class.return_value.__enter__.return_value = mock_smtp_server

                with patch.object(
                    notification_service, "_render_template"
                ) as mock_render:
                    mock_render.return_value = "<html><body>Welcome!</body></html>"

                    with patch.object(
                        notification_service, "_update_notification_status"
                    ) as mock_update:
                        result = await notification_service.retry_failed_notifications()

                        assert result["total_processed"] == 1
                        assert result["successful_retries"] == 1
                        assert result["failed_retries"] == 0
                        mock_update.assert_called_with(1, "sent", None)

    @pytest.mark.asyncio
    async def test_retry_failed_notifications_max_retries_exceeded(
        self, notification_service
    ):
        """Test retry with maximum retry count exceeded."""
        failed_notification = {
            "id": 1,
            "recipient_email": "test@example.com",
            "subject": "Test Subject",
            "template_name": "welcome",
            "template_data": {"username": "testuser"},
            "retry_count": 5,
        }

        with patch.object(
            notification_service, "get_failed_notifications"
        ) as mock_get_failed:
            mock_get_failed.return_value = [failed_notification]

            with patch.object(
                notification_service, "_update_notification_status"
            ) as mock_update:
                result = await notification_service.retry_failed_notifications(
                    max_retries=3
                )

                assert result["total_processed"] == 1
                assert result["successful_retries"] == 0
                assert result["failed_retries"] == 0
                assert result["max_retries_exceeded"] == 1
                mock_update.assert_called_with(
                    1, "permanently_failed", "Maximum retry attempts exceeded"
                )

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_template_error(
        self, notification_service, sample_email_data
    ):
        """Test graceful handling of template rendering errors."""
        with patch.object(notification_service, "_render_template") as mock_render:
            mock_render.side_effect = TemplateRenderingError("Template error")

            with pytest.raises(TemplateRenderingError):
                await notification_service.send_email(**sample_email_data)

    @pytest.mark.asyncio
    async def test_connection_pool_exhaustion_handling(
        self, notification_service, sample_email_data
    ):
        """Test handling of connection pool exhaustion."""
        with patch("smtplib.SMTP") as mock_smtp_class:
            mock_smtp_class.side_effect = [
                smtplib.SMTPConnectError("Connection pool exhausted"),
                smtplib.SMTPConnectError("Connection pool exhausted"),
                Mock(),  # Third attempt succeeds
            ]

            # Service should implement retry logic for connection errors
            with pytest.raises(EmailDeliveryError) as exc_info:
                await notification_service.send_email(**sample_email_data)

            assert "SMTP connection failed" in str(exc_info.value)


class TestServiceConfiguration:
    """Test service configuration and initialization."""

    def test_service_initialization_with_custom_config(self):
        """Test service initialization with custom configuration."""
        config = {
            "smtp_host": "custom-smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "custom@example.com",
            "smtp_password": "custom_password",
            "template_dir": "/custom/templates",
        }

        with patch("backend.services.notification_service.get_database"):
            service = NotificationService(config=config)

            assert service.smtp_host == "custom-smtp.example.com"
            assert service.smtp_port == 587
            assert service.smtp_username == "custom@example.com"

    def test_service_initialization_with_missing_config(self):
        """Test service initialization with missing required configuration."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(NotificationServiceError) as exc_info:
                NotificationService()

            assert "Missing required configuration" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_service_health_check(self, notification_service):
        """Test service health check functionality."""
        with patch.object(notification_service.db, "execute") as mock_execute:
            mock_result = Mock()
            mock_result.scalar.return_value = 1
            mock_execute.return_value = mock_result

            health_status = await notification_service.health_check()

            assert health_status["database"] is True
            assert health_status["overall"] is True

    @pytest.mark.asyncio
    async def test_service_health_check_database_failure(self, notification_service):
        """Test service health check with database failure."""
        with patch.object(notification_service.db, "execute") as mock_execute:
            mock_execute.side_effect = Exception("Database error")

            health_status = await notification_service.health_check()

            assert health_status["database"] is False
            assert health_status["overall"] is False
            assert "Database error" in health_status["errors"]


class TestAsyncOperations:
    """Test asynchronous operations and concurrency."""

    @pytest.mark.asyncio
    async def test_concurrent_email_sending(
        self, notification_service, mock_smtp_server
    ):
        """Test concurrent email sending operations."""
        email_tasks = []
        for i in range(5):
            email_data = {
                "to_email": f"user{i}@example.com",
                "subject": f"Test {i}",
                "template_name": "welcome",
                "template_data": {"username": f"user{i}"},
            }
            email_tasks.append(email_data)

        with patch("smtplib.SMTP") as mock_smtp_class:
            mock_smtp_class.return_value.__enter__.return_value = mock_smtp_server

            with patch.object(notification_service, "_render_template") as mock_render:
                mock_render.return_value = "<html><body>Welcome!</body></html>"

                # Send emails concurrently
                tasks = [
                    notification_service.send_email(**email_data)
                    for email_data in email_tasks
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # All should succeed
                assert len(results) == 5
                assert all(
                    result is True
                    for result in results
                    if not isinstance(result, Exception)
                )

    @pytest.mark.asyncio
    async def test_rate_limiting(self, notification_service):
        """Test rate limiting functionality."""
        with patch.object(notification_service, "_check_rate_limit") as mock_rate_limit:
            mock_rate_limit.side_effect = [
                True,
                True,
                False,
            ]  # Third call hits rate limit

            # First two should succeed
            result1 = await notification_service._check_rate_limit("test@example.com")
            result2 = await notification_service._check_rate_limit("test@example.com")
            result3 = await notification_service._check_rate_limit("test@example.com")

            assert result1 is True
            assert result2 is True
            assert result3 is False

    @pytest.mark.asyncio
    async def test_cleanup_old_notifications(self, notification_service):
        """Test cleanup of old notification records."""
        days_to_keep = 30

        with patch.object(notification_service.db, "execute") as mock_execute:
            mock_result = Mock()
            mock_result.rowcount = 150
            mock_execute.return_value = mock_result

            deleted_count = await notification_service.cleanup_old_notifications(
                days_to_keep
            )

            assert deleted_count == 150
            notification_service.db.execute.assert_called_once()
            notification_service.db.commit.assert_called_once()
