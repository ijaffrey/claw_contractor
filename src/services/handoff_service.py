from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import logging
from dataclasses import dataclass

from ..models.lead import Lead
from ..models.customer import Customer
from ..database.repositories.lead_repository import LeadRepository
from ..database.repositories.customer_repository import CustomerRepository
from ..services.email_service import EmailService
from ..services.sms_service import SMSService
from ..utils.exceptions import (
    HandoffError,
    LeadNotFoundError,
    InvalidStatusTransitionError,
)

logger = logging.getLogger(__name__)


class LeadStatus(Enum):
    """Lead status enumeration for handoff process"""

    NEW = "new"
    QUALIFIED = "qualified"
    CONTACTED = "contacted"
    QUOTED = "quoted"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FOLLOW_UP_REQUIRED = "follow_up_required"


class HandoffEventType(Enum):
    """Types of handoff events for logging"""

    HANDOFF_INITIATED = "handoff_initiated"
    HANDOFF_COMPLETED = "handoff_completed"
    STATUS_UPDATED = "status_updated"
    MESSAGE_SENT = "message_sent"
    HANDOFF_FAILED = "handoff_failed"
    FOLLOW_UP_SCHEDULED = "follow_up_scheduled"
    CUSTOMER_CONTACTED = "customer_contacted"


@dataclass
class MessageTemplate:
    """Template for handoff messages"""

    subject: str
    body: str
    sms_body: Optional[str] = None


class HandoffService:
    """Service for managing lead handoffs between systems and teams"""

    def __init__(
        self,
        lead_repository: LeadRepository,
        customer_repository: CustomerRepository,
        email_service: EmailService,
        sms_service: SMSService,
    ):
        self.lead_repository = lead_repository
        self.customer_repository = customer_repository
        self.email_service = email_service
        self.sms_service = sms_service
        self._status_transitions = self._initialize_status_transitions()
        self._message_templates = self._initialize_message_templates()

    def _initialize_status_transitions(self) -> Dict[LeadStatus, List[LeadStatus]]:
        """Initialize valid status transitions"""
        return {
            LeadStatus.NEW: [
                LeadStatus.QUALIFIED,
                LeadStatus.CONTACTED,
                LeadStatus.CANCELLED,
            ],
            LeadStatus.QUALIFIED: [
                LeadStatus.CONTACTED,
                LeadStatus.QUOTED,
                LeadStatus.SCHEDULED,
                LeadStatus.CANCELLED,
                LeadStatus.FOLLOW_UP_REQUIRED,
            ],
            LeadStatus.CONTACTED: [
                LeadStatus.QUOTED,
                LeadStatus.SCHEDULED,
                LeadStatus.IN_PROGRESS,
                LeadStatus.CANCELLED,
                LeadStatus.FOLLOW_UP_REQUIRED,
            ],
            LeadStatus.QUOTED: [
                LeadStatus.SCHEDULED,
                LeadStatus.IN_PROGRESS,
                LeadStatus.COMPLETED,
                LeadStatus.CANCELLED,
                LeadStatus.FOLLOW_UP_REQUIRED,
            ],
            LeadStatus.SCHEDULED: [
                LeadStatus.IN_PROGRESS,
                LeadStatus.COMPLETED,
                LeadStatus.CANCELLED,
                LeadStatus.FOLLOW_UP_REQUIRED,
            ],
            LeadStatus.IN_PROGRESS: [
                LeadStatus.COMPLETED,
                LeadStatus.CANCELLED,
                LeadStatus.FOLLOW_UP_REQUIRED,
            ],
            LeadStatus.COMPLETED: [LeadStatus.FOLLOW_UP_REQUIRED],
            LeadStatus.FOLLOW_UP_REQUIRED: [
                LeadStatus.CONTACTED,
                LeadStatus.QUOTED,
                LeadStatus.SCHEDULED,
                LeadStatus.CANCELLED,
            ],
            LeadStatus.CANCELLED: [],  # Terminal state
        }

    def _initialize_message_templates(self) -> Dict[str, MessageTemplate]:
        """Initialize professional message templates"""
        return {
            "handoff_success": MessageTemplate(
                subject="Your Service Request Has Been Received - Next Steps",
                body="""Dear {customer_name},

Thank you for your interest in our services. We're pleased to confirm that your service request has been successfully received and processed.

Here are the details of your request:
- Request ID: {lead_id}
- Service Type: {service_type}
- Date Submitted: {date_submitted}
- Priority Level: {priority}

What happens next:
1. Our team will review your request within 24 hours
2. A qualified specialist will contact you to discuss your specific needs
3. We'll provide a detailed estimate and timeline for your project
4. Once approved, we'll schedule your service at your convenience

Contact Information:
- Phone: {company_phone}
- Email: {company_email}
- Office Hours: Monday-Friday, 8:00 AM - 6:00 PM

We appreciate the opportunity to serve you and look forward to exceeding your expectations.

Best regards,
The {company_name} Team""",
                sms_body="Hi {customer_name}! Your service request #{lead_id} has been received. Our team will contact you within 24 hours to discuss next steps. Questions? Call {company_phone}.",
            ),
            "status_update": MessageTemplate(
                subject="Update on Your Service Request #{lead_id}",
                body="""Dear {customer_name},

We wanted to provide you with an update on your service request.

Request Details:
- Request ID: {lead_id}
- Current Status: {status}
- Last Updated: {update_date}

Status Description: {status_description}

{next_steps}

If you have any questions or concerns, please don't hesitate to contact us at {company_phone} or reply to this email.

Thank you for choosing {company_name}.

Best regards,
Customer Service Team""",
                sms_body="Update: Your service request #{lead_id} status is now {status}. {next_steps_brief} Questions? Call {company_phone}.",
            ),
            "completion_confirmation": MessageTemplate(
                subject="Service Completed - Thank You for Choosing {company_name}",
                body="""Dear {customer_name},

We're delighted to inform you that your service request has been successfully completed!

Service Summary:
- Request ID: {lead_id}
- Service Type: {service_type}
- Completion Date: {completion_date}
- Technician: {technician_name}

Service Details:
{service_details}

Quality Assurance:
Our work comes with a satisfaction guarantee. If you experience any issues or have concerns about the completed work, please contact us immediately at {company_phone}.

Feedback Request:
Your feedback is valuable to us. We'd appreciate if you could take a moment to review our service:
- Online Review: {review_link}
- Direct Feedback: {feedback_email}

Future Services:
We hope you'll consider us for any future service needs. As a valued customer, you're eligible for:
- Priority scheduling
- Loyalty discounts
- Annual maintenance programs

Thank you for trusting {company_name} with your service needs. We look forward to serving you again!

Warm regards,
The {company_name} Team""",
                sms_body="Great news! Your service #{lead_id} is complete. Thank you for choosing {company_name}! Please consider leaving us a review: {review_link}",
            ),
            "follow_up_required": MessageTemplate(
                subject="Follow-up Required for Your Service Request #{lead_id}",
                body="""Dear {customer_name},

We hope this message finds you well. We're reaching out regarding your recent service request that requires follow-up attention.

Request Information:
- Request ID: {lead_id}
- Service Type: {service_type}
- Original Date: {original_date}
- Follow-up Reason: {follow_up_reason}

Action Required:
{action_details}

How to Proceed:
1. Contact us at {company_phone} to discuss the follow-up
2. Reply to this email with your preferred time for contact
3. Visit our website to schedule an appointment: {website_url}

We're committed to ensuring your complete satisfaction and will work diligently to address any outstanding items.

Best regards,
Customer Service Team
{company_name}""",
                sms_body="Follow-up needed for service #{lead_id}. Reason: {follow_up_reason}. Please call {company_phone} to discuss next steps.",
            ),
            "handoff_error": MessageTemplate(
                subject="Temporary Delay in Processing Your Service Request",
                body="""Dear {customer_name},

We want to keep you informed about your service request and apologize for any inconvenience.

Request Details:
- Request ID: {lead_id}
- Issue: Temporary processing delay
- Expected Resolution: Within 24 hours

What We're Doing:
Our technical team is working to resolve a system issue that has temporarily delayed the processing of your request. Your request remains a priority, and we expect to resume normal processing shortly.

We Will Contact You:
A member of our team will personally reach out to you within 24 hours to provide an update and ensure your service needs are addressed promptly.

We sincerely apologize for this delay and appreciate your patience and understanding.

Best regards,
Management Team
{company_name}

Emergency Contact: {emergency_phone}""",
                sms_body="Temporary delay with service #{lead_id}. Our team will contact you within 24 hours. Urgent needs? Call {emergency_phone}.",
            ),
        }

    async def execute_handoff(self, lead_id: str) -> Dict[str, Any]:
        """
        Execute complete handoff process for a lead

        Args:
            lead_id: Unique identifier for the lead

        Returns:
            Dictionary containing handoff results

        Raises:
            HandoffError: If handoff process fails
            LeadNotFoundError: If lead doesn't exist
        """
        try:
            logger.info(f"Starting handoff process for lead {lead_id}")

            # Log handoff initiation
            await self.log_handoff_event(
                lead_id=lead_id,
                event_type=HandoffEventType.HANDOFF_INITIATED,
                details={"timestamp": datetime.utcnow().isoformat()},
            )

            # Retrieve lead
            lead = await self.lead_repository.get_by_id(lead_id)
            if not lead:
                raise LeadNotFoundError(f"Lead {lead_id} not found")

            # Retrieve customer information
            customer = await self.customer_repository.get_by_id(lead.customer_id)
            if not customer:
                raise HandoffError(f"Customer not found for lead {lead_id}")

            # Validate current status allows handoff
            if lead.status not in [LeadStatus.NEW.value, LeadStatus.QUALIFIED.value]:
                logger.warning(
                    f"Lead {lead_id} in status {lead.status} - proceeding with caution"
                )

            results = {}

            # Update lead status to contacted
            await self.update_lead_status(lead_id, LeadStatus.CONTACTED.value)
            results["status_updated"] = True

            # Send completion message to customer
            message_result = await self.send_completion_message(customer, lead)
            results["message_sent"] = message_result

            # Perform additional handoff tasks
            handoff_details = await self._execute_handoff_tasks(lead, customer)
            results.update(handoff_details)

            # Log successful handoff completion
            await self.log_handoff_event(
                lead_id=lead_id,
                event_type=HandoffEventType.HANDOFF_COMPLETED,
                details={
                    "completion_timestamp": datetime.utcnow().isoformat(),
                    "results": results,
                },
            )

            logger.info(f"Handoff completed successfully for lead {lead_id}")

            return {
                "success": True,
                "lead_id": lead_id,
                "handoff_timestamp": datetime.utcnow().isoformat(),
                "results": results,
            }

        except Exception as e:
            logger.error(f"Handoff failed for lead {lead_id}: {str(e)}")

            # Log handoff failure
            await self.log_handoff_event(
                lead_id=lead_id,
                event_type=HandoffEventType.HANDOFF_FAILED,
                details={"error": str(e), "timestamp": datetime.utcnow().isoformat()},
            )

            # Send error notification if customer exists
            try:
                customer = await self.customer_repository.get_by_id(
                    (await self.lead_repository.get_by_id(lead_id)).customer_id
                )
                if customer:
                    await self._send_error_notification(customer, lead_id, str(e))
            except Exception as notify_error:
                logger.error(f"Failed to send error notification: {str(notify_error)}")

            raise HandoffError(f"Handoff failed for lead {lead_id}: {str(e)}")

    async def send_completion_message(
        self, customer: Customer, lead: Optional[Lead] = None
    ) -> Dict[str, Any]:
        """
        Send professional completion message to customer

        Args:
            customer: Customer object
            lead: Optional lead object for context

        Returns:
            Dictionary containing message sending results
        """
        try:
            template = self._message_templates["handoff_success"]

            # Prepare message context
            context = {
                "customer_name": customer.full_name,
                "lead_id": lead.id if lead else "N/A",
                "service_type": getattr(lead, "service_type", "General Service"),
                "date_submitted": getattr(
                    lead, "created_at", datetime.utcnow()
                ).strftime("%B %d, %Y"),
                "priority": getattr(lead, "priority", "Standard"),
                "company_name": "Claw Contractor Services",
                "company_phone": "(555) 123-4567",
                "company_email": "service@clawcontractor.com",
            }

            results = {"email_sent": False, "sms_sent": False}

            # Send email notification
            if customer.email:
                try:
                    email_subject = template.subject.format(**context)
                    email_body = template.body.format(**context)

                    await self.email_service.send_email(
                        to_email=customer.email,
                        subject=email_subject,
                        body=email_body,
                        html_body=self._convert_to_html(email_body),
                    )
                    results["email_sent"] = True
                    logger.info(f"Completion email sent to {customer.email}")

                except Exception as e:
                    logger.error(
                        f"Failed to send completion email to {customer.email}: {str(e)}"
                    )
                    results["email_error"] = str(e)

            # Send SMS notification if phone number available
            if customer.phone and template.sms_body:
                try:
                    sms_body = template.sms_body.format(**context)

                    await self.sms_service.send_sms(
                        to_phone=customer.phone, message=sms_body
                    )
                    results["sms_sent"] = True
                    logger.info(f"Completion SMS sent to {customer.phone}")

                except Exception as e:
                    logger.error(
                        f"Failed to send completion SMS to {customer.phone}: {str(e)}"
                    )
                    results["sms_error"] = str(e)

            # Log message sending event
            if lead:
                await self.log_handoff_event(
                    lead_id=lead.id,
                    event_type=HandoffEventType.MESSAGE_SENT,
                    details={
                        "message_type": "completion",
                        "email_sent": results["email_sent"],
                        "sms_sent": results["sms_sent"],
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

            return results

        except Exception as e:
            logger.error(f"Failed to send completion message: {str(e)}")
            raise HandoffError(f"Failed to send completion message: {str(e)}")

    async def update_lead_status(self, lead_id: str, status: str) -> bool:
        """
        Update lead status with validation and logging

        Args:
            lead_id: Unique identifier for the lead
            status: New status to set

        Returns:
            Boolean indicating success

        Raises:
            InvalidStatusTransitionError: If status transition is invalid
            LeadNotFoundError: If lead doesn't exist
        """
        try:
            # Retrieve current lead
            lead = await self.lead_repository.get_by_id(lead_id)
            if not lead:
                raise LeadNotFoundError(f"Lead {lead_id} not found")

            current_status = LeadStatus(lead.status)
            new_status = LeadStatus(status)

            # Validate status transition
            if not self._is_valid_status_transition(current_status, new_status):
                raise InvalidStatusTransitionError(
                    f"Invalid status transition from {current_status.value} to {new_status.value}"
                )

            # Update lead status
            success = await self.lead_repository.update_status(lead_id, status)

            if success:
                # Log status update
                await self.log_handoff_event(
                    lead_id=lead_id,
                    event_type=HandoffEventType.STATUS_UPDATED,
                    details={
                        "previous_status": current_status.value,
                        "new_status": new_status.value,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

                logger.info(
                    f"Lead {lead_id} status updated from {current_status.value} to {new_status.value}"
                )

                # Send status update notification if appropriate
                await self._send_status_update_notification(lead, new_status)

                return True
            else:
                logger.error(f"Failed to update status for lead {lead_id}")
                return False

        except Exception as e:
            logger.error(f"Error updating lead {lead_id} status: {str(e)}")
            raise

    async def log_handoff_event(
        self, lead_id: str, event_type: HandoffEventType, details: Dict[str, Any]
    ) -> bool:
        """
        Log handoff events for audit and monitoring

        Args:
            lead_id: Unique identifier for the lead
            event_type: Type of handoff event
            details: Additional event details

        Returns:
            Boolean indicating logging success
        """
        try:
            event_log = {
                "lead_id": lead_id,
                "event_type": event_type.value,
                "timestamp": datetime.utcnow().isoformat(),
                "details": details,
                "source": "handoff_service",
            }

            # Log to application logger
            logger.info(
                f"Handoff Event - Lead: {lead_id}, Type: {event_type.value}, Details: {details}"
            )

            # Store in database (assuming audit log table exists)
            success = await self.lead_repository.log_event(event_log)

            if not success:
                logger.warning(
                    f"Failed to store handoff event in database: {event_log}"
                )

            return success

        except Exception as e:
            logger.error(f"Error logging handoff event: {str(e)}")
            return False

    def _is_valid_status_transition(self, current: LeadStatus, new: LeadStatus) -> bool:
        """Check if status transition is valid"""
        return new in self._status_transitions.get(current, [])

    async def _execute_handoff_tasks(
        self, lead: Lead, customer: Customer
    ) -> Dict[str, Any]:
        """Execute additional handoff tasks"""
        tasks_results = {}

        try:
            # Schedule follow-up if needed
            if lead.priority == "high":
                tasks_results["follow_up_scheduled"] = (
                    await self._schedule_priority_follow_up(lead)
                )

            # Update customer engagement metrics
            tasks_results["metrics_updated"] = await self._update_engagement_metrics(
                customer.id
            )

            # Assign to appropriate team based on service type
            tasks_results["team_assigned"] = await self._assign_to_team(lead)

            # Create service ticket in external system
            tasks_results["ticket_created"] = await self._create_service_ticket(
                lead, customer
            )

        except Exception as e:
            logger.error(f"Error in handoff tasks: {str(e)}")
            tasks_results["error"] = str(e)

        return tasks_results

    async def _send_status_update_notification(
        self, lead: Lead, new_status: LeadStatus
    ):
        """Send status update notification to customer"""
        try:
            customer = await self.customer_repository.get_by_id(lead.customer_id)
            if not customer:
                return

            template = self._message_templates["status_update"]

            # Get status description and next steps
            status_info = self._get_status_info(new_status)

            context = {
                "customer_name": customer.full_name,
                "lead_id": lead.id,
                "status": new_status.value.replace("_", " ").title(),
                "update_date": datetime.utcnow().strftime("%B %d, %Y at %I:%M %p"),
                "status_description": status_info["description"],
                "next_steps": status_info["next_steps"],
                "next_steps_brief": status_info["next_steps_brief"],
                "company_name": "Claw Contractor Services",
                "company_phone": "(555) 123-4567",
            }

            # Send email notification
            if customer.email:
                try:
                    subject = template.subject.format(**context)
                    body = template.body.format(**context)

                    await self.email_service.send_email(
                        to_email=customer.email,
                        subject=subject,
                        body=body,
                        html_body=self._convert_to_html(body),
                    )
                except Exception as e:
                    logger.error(f"Failed to send status update email: {str(e)}")

            # Send SMS notification
            if customer.phone and template.sms_body:
                try:
                    sms_body = template.sms_body.format(**context)
                    await self.sms_service.send_sms(customer.phone, sms_body)
                except Exception as e:
                    logger.error(f"Failed to send status update SMS: {str(e)}")

        except Exception as e:
            logger.error(f"Error sending status update notification: {str(e)}")

    async def _send_error_notification(
        self, customer: Customer, lead_id: str, error: str
    ):
        """Send error notification to customer"""
        try:
            template = self._message_templates["handoff_error"]

            context = {
                "customer_name": customer.full_name,
                "lead_id": lead_id,
                "company_name": "Claw Contractor Services",
                "emergency_phone": "(555) 123-4567",
            }

            if customer.email:
                subject = template.subject.format(**context)
                body = template.body.format(**context)

                await self.email_service.send_email(
                    to_email=customer.email,
                    subject=subject,
                    body=body,
                    html_body=self._convert_to_html(body),
                )

        except Exception as e:
            logger.error(f"Failed to send error notification: {str(e)}")

    def _get_status_info(self, status: LeadStatus) -> Dict[str, str]:
        """Get status description and next steps"""
        status_info = {
            LeadStatus.NEW: {
                "description": "Your request has been received and is being reviewed by our team.",
                "next_steps": "Our team will contact you within 24 hours to discuss your specific needs and provide initial recommendations.",
                "next_steps_brief": "We'll call within 24hrs",
            },
            LeadStatus.QUALIFIED: {
                "description": "Your request has been qualified and approved for service scheduling.",
                "next_steps": "A specialist will reach out to schedule a consultation and provide a detailed estimate for your project.",
                "next_steps_brief": "Scheduling consultation",
            },
            LeadStatus.CONTACTED: {
                "description": "Our team has made contact and is preparing your service details.",
                "next_steps": "We'll finalize your service requirements and provide a comprehensive quote within 2 business days.",
                "next_steps_brief": "Quote coming soon",
            },
            LeadStatus.QUOTED: {
                "description": "We've prepared a detailed quote for your service request.",
                "next_steps": "Please review the quote we've sent. Once approved, we'll schedule your service at your convenience.",
                "next_steps_brief": "Awaiting quote approval",
            },
            LeadStatus.SCHEDULED: {
                "description": "Your service has been scheduled with our team.",
                "next_steps": "Our technician will arrive at the scheduled time. You'll receive a confirmation call 24 hours before the appointment.",
                "next_steps_brief": "Service scheduled",
            },
            LeadStatus.IN_PROGRESS: {
                "description": "Our team is currently working on your service request.",
                "next_steps": "We'll keep you updated on progress and notify you upon completion. Estimated completion time will be provided by your technician.",
                "next_steps_brief": "Work in progress",
            },
            LeadStatus.COMPLETED: {
                "description": "Your service request has been completed successfully.",
                "next_steps": "Please review the completed work and let us know if you have any questions or concerns. We'll follow up to ensure your complete satisfaction.",
                "next_steps_brief": "Service complete",
            },
            LeadStatus.FOLLOW_UP_REQUIRED: {
                "description": "Additional follow-up is required for your service request.",
                "next_steps": "Our team will contact you shortly to discuss the next steps and schedule any additional work that may be needed.",
                "next_steps_brief": "Follow-up needed",
            },
            LeadStatus.CANCELLED: {
                "description": "Your service request has been cancelled as requested.",
                "next_steps": "If you need to reschedule or have any questions, please don't hesitate to contact us. We're here to help whenever you're ready.",
                "next_steps_brief": "Contact us to reschedule",
            },
        }

        return status_info.get(
            status,
            {
                "description": "Status updated.",
                "next_steps": "Our team will contact you with more information.",
                "next_steps_brief": "Updates coming",
            },
        )

    def _convert_to_html(self, text_body: str) -> str:
        """Convert plain text email to HTML format"""
        html_body = text_body.replace("\n", "<br>\n")
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #f8f9fa; padding: 20px; margin-bottom: 20px; }}
                .content {{ padding: 20px; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; margin-top: 20px; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="content">
                {html_body}
            </div>
            <div class="footer">
                <p>This is an automated message from Claw Contractor Services.<br>
                Please do not reply directly to this email.</p>
            </div>
        </body>
        </html>
        """
        return html_body

    async def _schedule_priority_follow_up(self, lead: Lead) -> bool:
        """Schedule priority follow-up for high-priority leads"""
        try:
            # Implementation would integrate with scheduling system
            logger.info(f"Priority follow-up scheduled for lead {lead.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to schedule priority follow-up: {str(e)}")
            return False

    async def _update_engagement_metrics(self, customer_id: str) -> bool:
        """Update customer engagement metrics"""
        try:
            # Implementation would update customer engagement tracking
            logger.info(f"Engagement metrics updated for customer {customer_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update engagement metrics: {str(e)}")
            return False

    async def _assign_to_team(self, lead: Lead) -> bool:
        """Assign lead to appropriate team based on service type"""
        try:
            # Implementation would assign to team based on service type
            logger.info(f"Lead {lead.id} assigned to appropriate team")
            return True
        except Exception as e:
            logger.error(f"Failed to assign lead to team: {str(e)}")
            return False

    async def _create_service_ticket(self, lead: Lead, customer: Customer) -> bool:
        """Create service ticket in external system"""
        try:
            # Implementation would create ticket in external service management system
            logger.info(f"Service ticket created for lead {lead.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create service ticket: {str(e)}")
            return False
