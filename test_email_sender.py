import pytest
import smtplib
from unittest.mock import Mock, patch, MagicMock, call
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
import ssl
import socket
from typing import Dict, List, Any

from src.email_sender import (
    EmailSender,
    EmailConfig,
    EmailTemplate,
    EmailError,
    SMTPConnectionError,
    EmailValidationError,
    EmailTemplateError
)


class TestEmailSender:
    """Test suite for EmailSender class functionality."""

    @pytest.fixture
    def email_config(self):
        """Create a test email configuration."""
        return EmailConfig(
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password="test_password",
            use_tls=True,
            timeout=30
        )

    @pytest.fixture
    def email_sender(self, email_config):
        """Create an EmailSender instance with test configuration."""
        return EmailSender(email_config)

    @pytest.fixture
    def mock_smtp(self):
        """Create a mock SMTP server."""
        smtp_mock = MagicMock(spec=smtplib.SMTP)
        smtp_mock.starttls.return_value = None
        smtp_mock.login.return_value = None
        smtp_mock.send_message.return_value = {}
        smtp_mock.quit.return_value = None
        return smtp_mock

    @pytest.fixture
    def contractor_data(self):
        """Sample contractor notification data."""
        return {
            "contractor_name": "John Smith",
            "contractor_email": "john@contractor.com",
            "project_id": "PRJ-001",
            "project_name": "Kitchen Renovation",
            "customer_name": "Jane Doe",
            "start_date": "2024-01-15",
            "completion_date": "2024-02-15",
            "total_amount": 15000.00,
            "payment_schedule": "50% upfront, 50% on completion",
            "special_instructions": "Use eco-friendly materials"
        }

    @pytest.fixture
    def customer_handoff_data(self):
        """Sample customer handoff data."""
        return {
            "customer_name": "Jane Doe",
            "customer_email": "jane@customer.com",
            "project_id": "PRJ-001",
            "project_name": "Kitchen Renovation",
            "contractor_name": "John Smith",
            "contractor_email": "john@contractor.com",
            "contractor_phone": "+1-555-123-4567",
            "project_summary": "Complete kitchen renovation with new cabinets and appliances",
            "next_steps": "Contractor will contact you within 24 hours to schedule initial consultation",
            "support_email": "support@example.com",
            "support_phone": "+1-555-999-8888"
        }

    @patch('smtplib.SMTP')
    def test_send_contractor_notification_success(self, mock_smtp_class, email_sender, contractor_data):
        """Test successful contractor notification email sending."""
        # Setup
        mock_smtp_instance = MagicMock()
        mock_smtp_class.return_value = mock_smtp_instance
        mock_smtp_instance.__enter__.return_value = mock_smtp_instance
        mock_smtp_instance.send_message.return_value = {}

        # Execute
        result = email_sender.send_contractor_notification(contractor_data)

        # Assert
        assert result is True
        mock_smtp_class.assert_called_once_with(
            email_sender.config.smtp_server,
            email_sender.config.smtp_port,
            timeout=email_sender.config.timeout
        )
        mock_smtp_instance.starttls.assert_called_once()
        mock_smtp_instance.login.assert_called_once_with(
            email_sender.config.username,
            email_sender.config.password
        )
        mock_smtp_instance.send_message.assert_called_once()

        # Verify email content
        sent_message = mock_smtp_instance.send_message.call_args[0][0]
        assert sent_message['To'] == contractor_data['contractor_email']
        assert sent_message['Subject'] == f"New Project Assignment: {contractor_data['project_name']}"
        assert contractor_data['contractor_name'] in sent_message.get_content()

    @patch('smtplib.SMTP')
    def test_send_contractor_notification_with_attachments(self, mock_smtp_class, email_sender, contractor_data):
        """Test contractor notification with attachments."""
        # Setup
        mock_smtp_instance = MagicMock()
        mock_smtp_class.return_value = mock_smtp_instance
        mock_smtp_instance.__enter__.return_value = mock_smtp_instance
        
        attachments = [
            {"filename": "project_specs.pdf", "content": b"PDF content", "content_type": "application/pdf"},
            {"filename": "blueprint.jpg", "content": b"Image content", "content_type": "image/jpeg"}
        ]

        # Execute
        result = email_sender.send_contractor_notification(contractor_data, attachments=attachments)

        # Assert
        assert result is True
        sent_message = mock_smtp_instance.send_message.call_args[0][0]
        assert sent_message.is_multipart()

    @patch('smtplib.SMTP')
    def test_send_contractor_notification_smtp_error(self, mock_smtp_class, email_sender, contractor_data):
        """Test contractor notification with SMTP error."""
        # Setup
        mock_smtp_instance = MagicMock()
        mock_smtp_class.return_value = mock_smtp_instance
        mock_smtp_instance.__enter__.return_value = mock_smtp_instance
        mock_smtp_instance.send_message.side_effect = smtplib.SMTPException("SMTP Error")

        # Execute & Assert
        with pytest.raises(EmailError) as exc_info:
            email_sender.send_contractor_notification(contractor_data)
        
        assert "Failed to send contractor notification" in str(exc_info.value)

    @patch('smtplib.SMTP')
    def test_send_customer_handoff_success(self, mock_smtp_class, email_sender, customer_handoff_data):
        """Test successful customer handoff email sending."""
        # Setup
        mock_smtp_instance = MagicMock()
        mock_smtp_class.return_value = mock_smtp_instance
        mock_smtp_instance.__enter__.return_value = mock_smtp_instance
        mock_smtp_instance.send_message.return_value = {}

        # Execute
        result = email_sender.send_customer_handoff(customer_handoff_data)

        # Assert
        assert result is True
        mock_smtp_instance.send_message.assert_called_once()
        
        sent_message = mock_smtp_instance.send_message.call_args[0][0]
        assert sent_message['To'] == customer_handoff_data['customer_email']
        assert sent_message['Subject'] == f"Project Handoff: {customer_handoff_data['project_name']}"
        assert customer_handoff_data['contractor_name'] in sent_message.get_content()

    @patch('smtplib.SMTP')
    def test_send_customer_handoff_with_cc(self, mock_smtp_class, email_sender, customer_handoff_data):
        """Test customer handoff email with CC recipients."""
        # Setup
        mock_smtp_instance = MagicMock()
        mock_smtp_class.return_value = mock_smtp_instance
        mock_smtp_instance.__enter__.return_value = mock_smtp_instance
        
        cc_recipients = ["manager@example.com", "support@example.com"]

        # Execute
        result = email_sender.send_customer_handoff(customer_handoff_data, cc=cc_recipients)

        # Assert
        assert result is True
        sent_message = mock_smtp_instance.send_message.call_args[0][0]
        assert sent_message['Cc'] == ", ".join(cc_recipients)

    @patch('smtplib.SMTP')
    def test_configure_smtp_success(self, mock_smtp_class, email_sender):
        """Test successful SMTP configuration and connection."""
        # Setup
        mock_smtp_instance = MagicMock()
        mock_smtp_class.return_value = mock_smtp_instance
        mock_smtp_instance.__enter__.return_value = mock_smtp_instance

        # Execute
        with email_sender._configure_smtp() as smtp:
            # Assert
            assert smtp == mock_smtp_instance
            mock_smtp_class.assert_called_once_with(
                email_sender.config.smtp_server,
                email_sender.config.smtp_port,
                timeout=email_sender.config.timeout
            )
            mock_smtp_instance.starttls.assert_called_once()
            mock_smtp_instance.login.assert_called_once_with(
                email_sender.config.username,
                email_sender.config.password
            )

    @patch('smtplib.SMTP')
    def test_configure_smtp_no_tls(self, mock_smtp_class):
        """Test SMTP configuration without TLS."""
        # Setup
        config = EmailConfig(
            smtp_server="smtp.example.com",
            smtp_port=25,
            username="test@example.com",
            password="test_password",
            use_tls=False
        )
        email_sender = EmailSender(config)
        mock_smtp_instance = MagicMock()
        mock_smtp_class.return_value = mock_smtp_instance
        mock_smtp_instance.__enter__.return_value = mock_smtp_instance

        # Execute
        with email_sender._configure_smtp():
            # Assert
            mock_smtp_instance.starttls.assert_not_called()

    @patch('smtplib.SMTP')
    def test_configure_smtp_connection_error(self, mock_smtp_class, email_sender):
        """Test SMTP configuration with connection error."""
        # Setup
        mock_smtp_class.side_effect = socket.gaierror("Name resolution error")

        # Execute & Assert
        with pytest.raises(SMTPConnectionError) as exc_info:
            with email_sender._configure_smtp():
                pass
        
        assert "Failed to connect to SMTP server" in str(exc_info.value)

    @patch('smtplib.SMTP')
    def test_configure_smtp_auth_error(self, mock_smtp_class, email_sender):
        """Test SMTP configuration with authentication error."""
        # Setup
        mock_smtp_instance = MagicMock()
        mock_smtp_class.return_value = mock_smtp_instance
        mock_smtp_instance.__enter__.return_value = mock_smtp_instance
        mock_smtp_instance.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")

        # Execute & Assert
        with pytest.raises(SMTPConnectionError) as exc_info:
            with email_sender._configure_smtp():
                pass
        
        assert "SMTP authentication failed" in str(exc_info.value)

    def test_format_email_html_contractor_template(self, email_sender, contractor_data):
        """Test HTML email formatting for contractor notification."""
        # Execute
        html_content = email_sender.format_email_html("contractor_notification", contractor_data)

        # Assert
        assert isinstance(html_content, str)
        assert "<html>" in html_content
        assert contractor_data['contractor_name'] in html_content
        assert contractor_data['project_name'] in html_content
        assert contractor_data['customer_name'] in html_content
        assert str(contractor_data['total_amount']) in html_content

    def test_format_email_html_customer_handoff_template(self, email_sender, customer_handoff_data):
        """Test HTML email formatting for customer handoff."""
        # Execute
        html_content = email_sender.format_email_html("customer_handoff", customer_handoff_data)

        # Assert
        assert isinstance(html_content, str)
        assert "<html>" in html_content
        assert customer_handoff_data['customer_name'] in html_content
        assert customer_handoff_data['contractor_name'] in html_content
        assert customer_handoff_data['contractor_phone'] in html_content

    def test_format_email_html_invalid_template(self, email_sender):
        """Test HTML formatting with invalid template."""
        # Execute & Assert
        with pytest.raises(EmailTemplateError) as exc_info:
            email_sender.format_email_html("invalid_template", {})
        
        assert "Template not found" in str(exc_info.value)

    def test_format_email_html_missing_data(self, email_sender):
        """Test HTML formatting with missing template data."""
        # Setup
        incomplete_data = {"contractor_name": "John Smith"}

        # Execute & Assert
        with pytest.raises(EmailTemplateError) as exc_info:
            email_sender.format_email_html("contractor_notification", incomplete_data)
        
        assert "Missing required template data" in str(exc_info.value)

    @patch('smtplib.SMTP')
    def test_handle_email_errors_smtp_exception(self, mock_smtp_class, email_sender, contractor_data):
        """Test handling of SMTP exceptions."""
        # Setup
        mock_smtp_instance = MagicMock()
        mock_smtp_class.return_value = mock_smtp_instance
        mock_smtp_instance.__enter__.return_value = mock_smtp_instance
        mock_smtp_instance.send_message.side_effect = smtplib.SMTPRecipientsRefused({
            contractor_data['contractor_email']: (550, "Mailbox not found")
        })

        # Execute & Assert
        with pytest.raises(EmailError) as exc_info:
            email_sender.send_contractor_notification(contractor_data)
        
        assert "Recipients refused" in str(exc_info.value)

    @patch('smtplib.SMTP')
    def test_handle_email_errors_data_error(self, mock_smtp_class, email_sender, contractor_data):
        """Test handling of SMTP data errors."""
        # Setup
        mock_smtp_instance = MagicMock()
        mock_smtp_class.return_value = mock_smtp_instance
        mock_smtp_instance.__enter__.return_value = mock_smtp_instance
        mock_smtp_instance.send_message.side_effect = smtplib.SMTPDataError(552, "Message size exceeds limit")

        # Execute & Assert
        with pytest.raises(EmailError) as exc_info:
            email_sender.send_contractor_notification(contractor_data)
        
        assert "Message size exceeds limit" in str(exc_info.value)

    @patch('smtplib.SMTP')
    def test_handle_email_errors_server_disconnect(self, mock_smtp_class, email_sender, contractor_data):
        """Test handling of server disconnection errors."""
        # Setup
        mock_smtp_instance = MagicMock()
        mock_smtp_class.return_value = mock_smtp_instance
        mock_smtp_instance.__enter__.return_value = mock_smtp_instance
        mock_smtp_instance.send_message.side_effect = smtplib.SMTPServerDisconnected("Connection lost")

        # Execute & Assert
        with pytest.raises(EmailError) as exc_info:
            email_sender.send_contractor_notification(contractor_data)
        
        assert "Connection lost" in str(exc_info.value)

    def test_validate_email_addresses_valid_single(self, email_sender):
        """Test validation of a single valid email address."""
        # Execute
        result = email_sender.validate_email_addresses("test@example.com")

        # Assert
        assert result is True

    def test_validate_email_addresses_valid_multiple(self, email_sender):
        """Test validation of multiple valid email addresses."""
        # Setup
        emails = ["test1@example.com", "test2@domain.org", "user+tag@company.co.uk"]

        # Execute
        result = email_sender.validate_email_addresses(emails)

        # Assert
        assert result is True

    def test_validate_email_addresses_invalid_format(self, email_sender):
        """Test validation of invalid email format."""
        # Execute & Assert
        with pytest.raises(EmailValidationError) as exc_info:
            email_sender.validate_email_addresses("invalid-email")
        
        assert "Invalid email format" in str(exc_info.value)

    def test_validate_email_addresses_empty_string(self, email_sender):
        """Test validation of empty email string."""
        # Execute & Assert
        with pytest.raises(EmailValidationError) as exc_info:
            email_sender.validate_email_addresses("")
        
        assert "Email address cannot be empty" in str(exc_info.value)

    def test_validate_email_addresses_mixed_valid_invalid(self, email_sender):
        """Test validation with mix of valid and invalid emails."""
        # Setup
        emails = ["valid@example.com", "invalid-email", "another@valid.com"]

        # Execute & Assert
        with pytest.raises(EmailValidationError) as exc_info:
            email_sender.validate_email_addresses(emails)
        
        assert "invalid-email" in str(exc_info.value)

    def test_validate_email_addresses_special_characters(self, email_sender):
        """Test validation of emails with special characters."""
        # Setup
        valid_emails = [
            "user+tag@example.com",
            "user.name@domain.co.uk",
            "user_name@sub.domain.org",
            "123@numeric-domain.com"
        ]

        # Execute
        result = email_sender.validate_email_addresses(valid_emails)

        # Assert
        assert result is True


class TestEmailSenderIntegration:
    """Integration tests for EmailSender with mock email server."""

    @pytest.fixture
    def mock_email_server(self):
        """Create a mock email server for integration testing."""
        class MockEmailServer:
            def __init__(self):
                self.messages = []
                self.connected = False
                self.authenticated = False

            def connect(self, host, port, timeout=None):
                self.connected = True
                return True

            def starttls(self):
                return True

            def login(self, username, password):
                self.authenticated = True
                return True

            def send_message(self, message):
                if not self.connected or not self.authenticated:
                    raise smtplib.SMTPException("Not connected or authenticated")
                
                self.messages.append({
                    'from': message['From'],
                    'to': message['To'],
                    'subject': message['Subject'],
                    'content': message.get_content()
                })
                return {}

            def quit(self):
                self.connected = False
                self.authenticated = False

        return MockEmailServer()

    @patch('smtplib.SMTP')
    def test_integration_full_email_workflow(self, mock_smtp_class, mock_email_server, email_config):
        """Test complete email sending workflow with mock server."""
        # Setup
        mock_smtp_class.return_value = mock_email_server
        mock_email_server.__enter__ = lambda x: mock_email_server
        mock_email_server.__exit__ = lambda x, y, z, w: None
        
        email_sender = EmailSender(email_config)
        
        contractor_data = {
            "contractor_name": "Integration Test Contractor",
            "contractor_email": "contractor@test.com",
            "project_id": "INT-001",
            "project_name": "Integration Test Project",
            "customer_name": "Test Customer",
            "start_date": "2024-01-01",
            "completion_date": "2024-02-01",
            "total_amount": 10000.00,
            "payment_schedule": "Monthly",
            "special_instructions": "Test instructions"
        }

        # Execute
        result = email_sender.send_contractor_notification(contractor_data)

        # Assert
        assert result is True
        assert len(mock_email_server.messages) == 1
        
        sent_message = mock_email_server.messages[0]
        assert sent_message['to'] == contractor_data['contractor_email']
        assert contractor_data['project_name'] in sent_message['subject']

    @patch('smtplib.SMTP')
    def test_integration_multiple_recipients(self, mock_smtp_class, mock_email_server, email_config):
        """Test sending emails to multiple recipients."""
        # Setup
        mock_smtp_class.return_value = mock_email_server
        mock_email_server.__enter__ = lambda x: mock_email_server
        mock_email_server.__exit__ = lambda x, y, z, w: None
        
        email_sender = EmailSender(email_config)
        
        customer_data = {
            "customer_name": "Test Customer",
            "customer_email": "customer@test.com",
            "project_id": "INT-002",
            "project_name": "Multi-recipient Test",
            "contractor_name": "Test Contractor",
            "contractor_email": "contractor@test.com",
            "contractor_phone": "+1-555-0123",
            "project_summary": "Test project",
            "next_steps": "Contact contractor",
            "support_email": "support@test.com",
            "support_phone": "+1-555-9999"
        }
        
        cc_recipients = ["manager@test.com", "backup@test.com"]

        # Execute
        result = email_sender.send_customer_handoff(customer_data, cc=cc_recipients)

        # Assert
        assert result is True
        assert len(mock_email_server.messages) == 1

    @patch('smtplib.SMTP')
    def test_integration_error_recovery(self, mock_smtp_class, email_config):
        """Test error handling and recovery in integration scenario."""
        # Setup
        failing_server = MagicMock()
        failing_server.__enter__ = lambda x: failing_server
        failing_server.__exit__ = lambda x, y, z, w: None
        failing_server.send_message.side_effect = smtplib.SMTPException("Temporary failure")
        
        mock_smtp_class.return_value = failing_server
        
        email_sender = EmailSender(email_config)
        
        contractor_data = {
            "contractor_name": "Error Test",
            "contractor_email": "error@test.com",
            "project_id": "ERR-001",
            "project_name": "Error Test Project",
            "customer_name": "Test Customer",
            "start_date": "2024-01-01",
            "completion_date": "2024-02-01",
            "total_amount": 5000.00,
            "payment_schedule": "Upfront",
            "special_instructions": "None"
        }

        # Execute & Assert
        with pytest.raises(EmailError):
            email_sender.send_contractor_notification(contractor_data)

    def test_integration_email_template_rendering(self, email_config):
        """Test email template rendering in integration context."""
        # Setup
        email_sender = EmailSender(email_config)
        
        template_data = {
            "contractor_name": "Template Test Contractor",
            "contractor_email": "template@test.com",
            "project_id": "TPL-001",
            "project_name": "Template Rendering Test",
            "customer_name": "Template Customer",
            "start_date": "2024-03-01",
            "completion_date": "2024-04-01",
            "total_amount": 7500.00,
            "payment_schedule": "50/50 split",
            "special_instructions": "Use premium materials"
        }

        # Execute
        html_content = email_sender.format_email_html("contractor_notification", template_data)

        # Assert
        assert isinstance(html_content, str)
        assert len(html_content) > 100  # Should be substantial content
        assert all(str(value) in html_content for key, value in template_data.items() 
                  if key != 'contractor_email')  # Email might not be in body