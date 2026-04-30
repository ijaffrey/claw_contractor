"""
Notification service for handling contractor and customer notifications.

This module provides comprehensive notification functionality including:
- Contractor notification emails with lead summaries
- Customer handoff messages
- Email sending with robust error handling
- Notification logging with timestamps
"""

import logging
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import asyncio
import aiosmtplib
from jinja2 import Template, Environment, FileSystemLoader
import os

from ..database.models import Contractor, Customer, Lead, NotificationLog
from ..database.connection import get_db_session
from ..config.settings import get_settings


class NotificationType(Enum):
    """Enumeration of notification types."""

    CONTRACTOR_LEAD_ASSIGNMENT = "contractor_lead_assignment"
    CONTRACTOR_LEAD_UPDATE = "contractor_lead_update"
    CUSTOMER_HANDOFF = "customer_handoff"
    CUSTOMER_FOLLOW_UP = "customer_follow_up"
    SYSTEM_ALERT = "system_alert"


class NotificationStatus(Enum):
    """Enumeration of notification statuses."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class NotificationData:
    """Data structure for notification information."""

    recipient_email: str
    recipient_name: str
    subject: str
    template_name: str
    template_data: Dict[str, Any]
    notification_type: NotificationType
    priority: int = 1  # 1 = high, 2 = medium, 3 = low
    attachments: Optional[List[Dict[str, Any]]] = None
    send_after: Optional[datetime] = None


@dataclass
class LeadSummary:
    """Data structure for lead summary information."""

    lead_id: int
    customer_name: str
    customer_email: str
    customer_phone: str
    service_type: str
    project_description: str
    budget_range: str
    location: str
    urgency_level: str
    created_at: datetime
    additional_notes: Optional[str] = None


class NotificationService:
    """Service for handling all notification operations."""

    def __init__(self):
        """Initialize the notification service."""
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)

        # Initialize Jinja2 environment for templates
        template_dir = os.path.join(os.path.dirname(__file__), "../templates/emails")
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir), autoescape=True
        )

        # Email configuration
        self.smtp_server = self.settings.SMTP_SERVER
        self.smtp_port = self.settings.SMTP_PORT
        self.smtp_username = self.settings.SMTP_USERNAME
        self.smtp_password = self.settings.SMTP_PASSWORD
        self.smtp_use_tls = self.settings.SMTP_USE_TLS
        self.from_email = self.settings.FROM_EMAIL
        self.from_name = self.settings.FROM_NAME

        # Retry configuration
        self.max_retries = 3
        self.retry_delays = [60, 300, 900]  # 1min, 5min, 15min

    async def send_contractor_lead_notification(
        self,
        contractor: Contractor,
        lead_summary: LeadSummary,
        assignment_type: str = "new",
    ) -> bool:
        """
        Send lead notification email to contractor.

        Args:
            contractor: Contractor object
            lead_summary: Lead summary data
            assignment_type: Type of assignment ("new", "update", "reminder")

        Returns:
            bool: True if notification was sent successfully
        """
        try:
            # Prepare template data
            template_data = {
                "contractor_name": contractor.name,
                "contractor_first_name": contractor.name.split()[0],
                "lead_id": lead_summary.lead_id,
                "customer_name": lead_summary.customer_name,
                "customer_email": lead_summary.customer_email,
                "customer_phone": lead_summary.customer_phone,
                "service_type": lead_summary.service_type,
                "project_description": lead_summary.project_description,
                "budget_range": lead_summary.budget_range,
                "location": lead_summary.location,
                "urgency_level": lead_summary.urgency_level,
                "created_at": lead_summary.created_at,
                "additional_notes": lead_summary.additional_notes,
                "assignment_type": assignment_type,
                "platform_name": self.settings.PLATFORM_NAME,
                "contact_phone": self.settings.SUPPORT_PHONE,
                "contact_email": self.settings.SUPPORT_EMAIL,
            }

            # Determine subject based on assignment type
            subject_map = {
                "new": f"New Lead Assignment - {lead_summary.service_type}",
                "update": f"Lead Update - {lead_summary.customer_name}",
                "reminder": f"Lead Follow-up Reminder - {lead_summary.customer_name}",
            }
            subject = subject_map.get(assignment_type, "Lead Notification")

            notification_data = NotificationData(
                recipient_email=contractor.email,
                recipient_name=contractor.name,
                subject=subject,
                template_name="contractor_lead_notification.html",
                template_data=template_data,
                notification_type=NotificationType.CONTRACTOR_LEAD_ASSIGNMENT,
                priority=1 if assignment_type == "new" else 2,
            )

            return await self._send_notification(notification_data)

        except Exception as e:
            self.logger.error(f"Error sending contractor lead notification: {str(e)}")
            return False

    async def send_customer_handoff_message(
        self,
        customer: Customer,
        contractor: Contractor,
        lead: Lead,
        handoff_message: str,
    ) -> bool:
        """
        Send handoff message to customer with contractor information.

        Args:
            customer: Customer object
            contractor: Contractor object
            lead: Lead object
            handoff_message: Custom handoff message

        Returns:
            bool: True if notification was sent successfully
        """
        try:
            template_data = {
                "customer_name": customer.name,
                "customer_first_name": customer.name.split()[0],
                "contractor_name": contractor.name,
                "contractor_email": contractor.email,
                "contractor_phone": contractor.phone,
                "contractor_company": getattr(contractor, "company", ""),
                "contractor_bio": getattr(contractor, "bio", ""),
                "contractor_rating": getattr(contractor, "rating", 0),
                "contractor_reviews_count": getattr(contractor, "reviews_count", 0),
                "service_type": lead.service_type,
                "project_description": lead.project_description,
                "handoff_message": handoff_message,
                "lead_id": lead.id,
                "platform_name": self.settings.PLATFORM_NAME,
                "support_email": self.settings.SUPPORT_EMAIL,
                "support_phone": self.settings.SUPPORT_PHONE,
            }

            notification_data = NotificationData(
                recipient_email=customer.email,
                recipient_name=customer.name,
                subject=f"Your {lead.service_type} Project - Contractor Match Found",
                template_name="customer_handoff_message.html",
                template_data=template_data,
                notification_type=NotificationType.CUSTOMER_HANDOFF,
                priority=1,
            )

            return await self._send_notification(notification_data)

        except Exception as e:
            self.logger.error(f"Error sending customer handoff message: {str(e)}")
            return False

    async def send_bulk_contractor_notifications(
        self,
        contractors: List[Contractor],
        lead_summary: LeadSummary,
        max_concurrent: int = 5,
    ) -> Dict[str, List[str]]:
        """
        Send notifications to multiple contractors concurrently.

        Args:
            contractors: List of contractor objects
            lead_summary: Lead summary data
            max_concurrent: Maximum concurrent email sends

        Returns:
            Dict with 'success' and 'failed' lists of contractor emails
        """
        results = {"success": [], "failed": []}

        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(max_concurrent)

        async def send_single_notification(contractor):
            async with semaphore:
                success = await self.send_contractor_lead_notification(
                    contractor, lead_summary
                )
                if success:
                    results["success"].append(contractor.email)
                else:
                    results["failed"].append(contractor.email)

        # Execute all notifications concurrently
        tasks = [send_single_notification(contractor) for contractor in contractors]
        await asyncio.gather(*tasks, return_exceptions=True)

        self.logger.info(
            f"Bulk notification results: {len(results['success'])} success, {len(results['failed'])} failed"
        )
        return results

    async def _send_notification(self, notification_data: NotificationData) -> bool:
        """
        Internal method to send notification with error handling and logging.

        Args:
            notification_data: Notification data structure

        Returns:
            bool: True if notification was sent successfully
        """
        notification_log_id = None

        try:
            # Log notification attempt to database
            notification_log_id = await self._log_notification(
                notification_data, NotificationStatus.PENDING
            )

            # Render email template
            email_content = await self._render_email_template(
                notification_data.template_name, notification_data.template_data
            )

            # Send email
            success = await self._send_email(
                to_email=notification_data.recipient_email,
                to_name=notification_data.recipient_name,
                subject=notification_data.subject,
                html_content=email_content,
                attachments=notification_data.attachments,
            )

            # Update notification log
            status = NotificationStatus.SENT if success else NotificationStatus.FAILED
            await self._update_notification_log(notification_log_id, status)

            return success

        except Exception as e:
            self.logger.error(f"Error in _send_notification: {str(e)}")
            if notification_log_id:
                await self._update_notification_log(
                    notification_log_id, NotificationStatus.FAILED, error_message=str(e)
                )
            return False

    async def _send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """
        Send email using SMTP with retry logic.

        Args:
            to_email: Recipient email address
            to_name: Recipient name
            subject: Email subject
            html_content: HTML content
            text_content: Plain text content (optional)
            attachments: List of attachment dictionaries

        Returns:
            bool: True if email was sent successfully
        """
        for attempt in range(self.max_retries):
            try:
                # Create message
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = f"{self.from_name} <{self.from_email}>"
                msg["To"] = f"{to_name} <{to_email}>"

                # Add text content if provided
                if text_content:
                    text_part = MIMEText(text_content, "plain")
                    msg.attach(text_part)

                # Add HTML content
                html_part = MIMEText(html_content, "html")
                msg.attach(html_part)

                # Add attachments if provided
                if attachments:
                    for attachment in attachments:
                        self._add_attachment(msg, attachment)

                # Send email using aiosmtplib for async support
                await aiosmtplib.send(
                    msg,
                    hostname=self.smtp_server,
                    port=self.smtp_port,
                    username=self.smtp_username,
                    password=self.smtp_password,
                    use_tls=self.smtp_use_tls,
                )

                self.logger.info(f"Email sent successfully to {to_email}")
                return True

            except Exception as e:
                self.logger.error(f"Email send attempt {attempt + 1} failed: {str(e)}")

                if attempt < self.max_retries - 1:
                    # Wait before retry
                    await asyncio.sleep(self.retry_delays[attempt])
                else:
                    self.logger.error(
                        f"Failed to send email to {to_email} after {self.max_retries} attempts"
                    )
                    return False

    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]) -> None:
        """
        Add attachment to email message.

        Args:
            msg: Email message object
            attachment: Attachment dictionary with 'filename', 'content', 'content_type'
        """
        try:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment["content"])
            encoders.encode_base64(part)

            part.add_header(
                "Content-Disposition", f'attachment; filename= {attachment["filename"]}'
            )

            msg.attach(part)

        except Exception as e:
            self.logger.error(f"Error adding attachment: {str(e)}")

    async def _render_email_template(
        self, template_name: str, template_data: Dict[str, Any]
    ) -> str:
        """
        Render email template with provided data.

        Args:
            template_name: Name of the template file
            template_data: Data to populate template

        Returns:
            str: Rendered HTML content
        """
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**template_data)

        except Exception as e:
            self.logger.error(f"Error rendering template {template_name}: {str(e)}")
            # Return fallback template
            return self._get_fallback_template(template_data)

    def _get_fallback_template(self, template_data: Dict[str, Any]) -> str:
        """
        Generate fallback HTML template when main template fails.

        Args:
            template_data: Template data

        Returns:
            str: Fallback HTML content
        """
        return f"""
        <html>
            <body>
                <h2>Notification</h2>
                <p>This is an automated notification from {self.settings.PLATFORM_NAME}.</p>
                <hr>
                <p>Template data: {json.dumps(template_data, indent=2, default=str)}</p>
                <hr>
                <p>If you have any questions, please contact us at {self.settings.SUPPORT_EMAIL}</p>
            </body>
        </html>
        """

    async def _log_notification(
        self,
        notification_data: NotificationData,
        status: NotificationStatus,
        error_message: Optional[str] = None,
    ) -> int:
        """
        Log notification to database.

        Args:
            notification_data: Notification data
            status: Notification status
            error_message: Error message if failed

        Returns:
            int: Notification log ID
        """
        try:
            with get_db_session() as session:
                notification_log = NotificationLog(
                    recipient_email=notification_data.recipient_email,
                    recipient_name=notification_data.recipient_name,
                    subject=notification_data.subject,
                    notification_type=notification_data.notification_type.value,
                    template_name=notification_data.template_name,
                    template_data=json.dumps(
                        notification_data.template_data, default=str
                    ),
                    status=status.value,
                    priority=notification_data.priority,
                    error_message=error_message,
                    created_at=datetime.now(timezone.utc),
                    send_after=notification_data.send_after,
                )

                session.add(notification_log)
                session.commit()
                session.refresh(notification_log)

                return notification_log.id

        except Exception as e:
            self.logger.error(f"Error logging notification: {str(e)}")
            return 0

    async def _update_notification_log(
        self,
        notification_log_id: int,
        status: NotificationStatus,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Update notification log status.

        Args:
            notification_log_id: Notification log ID
            status: New status
            error_message: Error message if failed
        """
        try:
            with get_db_session() as session:
                notification_log = session.query(NotificationLog).get(
                    notification_log_id
                )
                if notification_log:
                    notification_log.status = status.value
                    notification_log.sent_at = (
                        datetime.now(timezone.utc)
                        if status == NotificationStatus.SENT
                        else None
                    )
                    if error_message:
                        notification_log.error_message = error_message

                    session.commit()

        except Exception as e:
            self.logger.error(f"Error updating notification log: {str(e)}")

    async def get_notification_history(
        self,
        recipient_email: Optional[str] = None,
        notification_type: Optional[NotificationType] = None,
        status: Optional[NotificationStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get notification history with optional filters.

        Args:
            recipient_email: Filter by recipient email
            notification_type: Filter by notification type
            status: Filter by status
            limit: Maximum number of records
            offset: Number of records to skip

        Returns:
            List of notification log dictionaries
        """
        try:
            with get_db_session() as session:
                query = session.query(NotificationLog)

                if recipient_email:
                    query = query.filter(
                        NotificationLog.recipient_email == recipient_email
                    )

                if notification_type:
                    query = query.filter(
                        NotificationLog.notification_type == notification_type.value
                    )

                if status:
                    query = query.filter(NotificationLog.status == status.value)

                notifications = (
                    query.order_by(NotificationLog.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                    .all()
                )

                return [
                    {
                        "id": n.id,
                        "recipient_email": n.recipient_email,
                        "recipient_name": n.recipient_name,
                        "subject": n.subject,
                        "notification_type": n.notification_type,
                        "status": n.status,
                        "priority": n.priority,
                        "created_at": n.created_at,
                        "sent_at": n.sent_at,
                        "error_message": n.error_message,
                    }
                    for n in notifications
                ]

        except Exception as e:
            self.logger.error(f"Error getting notification history: {str(e)}")
            return []

    async def retry_failed_notifications(self, max_retries: int = 10) -> Dict[str, int]:
        """
        Retry failed notifications that haven't exceeded maximum retry count.

        Args:
            max_retries: Maximum number of notifications to retry

        Returns:
            Dict with retry statistics
        """
        results = {"attempted": 0, "successful": 0, "failed": 0}

        try:
            with get_db_session() as session:
                failed_notifications = (
                    session.query(NotificationLog)
                    .filter(NotificationLog.status == NotificationStatus.FAILED.value)
                    .limit(max_retries)
                    .all()
                )

                for notification in failed_notifications:
                    results["attempted"] += 1

                    try:
                        # Recreate notification data
                        template_data = json.loads(notification.template_data)
                        notification_data = NotificationData(
                            recipient_email=notification.recipient_email,
                            recipient_name=notification.recipient_name,
                            subject=notification.subject,
                            template_name=notification.template_name,
                            template_data=template_data,
                            notification_type=NotificationType(
                                notification.notification_type
                            ),
                            priority=notification.priority,
                        )

                        # Update status to retry
                        notification.status = NotificationStatus.RETRY.value
                        session.commit()

                        # Attempt to resend
                        success = await self._send_notification(notification_data)

                        if success:
                            results["successful"] += 1
                        else:
                            results["failed"] += 1

                    except Exception as e:
                        self.logger.error(
                            f"Error retrying notification {notification.id}: {str(e)}"
                        )
                        results["failed"] += 1

        except Exception as e:
            self.logger.error(f"Error in retry_failed_notifications: {str(e)}")

        self.logger.info(f"Notification retry results: {results}")
        return results


# Global instance
notification_service = NotificationService()
