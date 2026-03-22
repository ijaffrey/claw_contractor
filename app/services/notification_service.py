import logging
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db import transaction

from app.models import Lead, Contractor, NotificationLog


logger = logging.getLogger(__name__)


class NotificationType(Enum):
    CONTRACTOR_NOTIFICATION = "contractor_notification"
    CUSTOMER_HANDOFF = "customer_handoff"
    SYSTEM_ALERT = "system_alert"


class NotificationStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"


class NotificationService:
    """
    Service for handling all notification-related operations including
    email notifications and logging.
    """
    
    def __init__(self):
        self.from_email = settings.DEFAULT_FROM_EMAIL
        self.admin_email = settings.ADMIN_EMAIL
    
    def send_contractor_notification(self, lead_id: int) -> Dict[str, Any]:
        """
        Send notification to contractor about a qualified lead.
        
        Args:
            lead_id: ID of the lead to notify about
            
        Returns:
            Dict containing success status and details
        """
        try:
            lead = Lead.objects.select_related(
                'contractor', 'customer'
            ).get(id=lead_id)
            
            if not lead.contractor:
                raise ValueError(f"No contractor assigned to lead {lead_id}")
            
            if not lead.contractor.email:
                raise ValueError(f"Contractor {lead.contractor.id} has no email address")
            
            # Prepare email context
            context = {
                'contractor_name': lead.contractor.company_name or lead.contractor.user.get_full_name(),
                'customer_name': lead.customer.get_full_name(),
                'customer_phone': lead.customer.phone,
                'customer_email': lead.customer.email,
                'service_type': lead.service_type,
                'project_description': lead.description,
                'estimated_budget': lead.estimated_budget,
                'preferred_timeline': lead.preferred_timeline,
                'customer_address': self._format_customer_address(lead.customer),
                'lead_id': lead.id,
                'urgency': lead.urgency,
                'created_at': lead.created_at
            }
            
            # Render email templates
            subject = f"New Qualified Lead - {lead.service_type}"
            html_message = render_to_string(
                'emails/contractor_notification.html', 
                context
            )
            plain_message = render_to_string(
                'emails/contractor_notification.txt', 
                context
            )
            
            # Send email
            success = send_mail(
                subject=subject,
                message=plain_message,
                from_email=self.from_email,
                recipient_list=[lead.contractor.email],
                html_message=html_message,
                fail_silently=False
            )
            
            status = NotificationStatus.SENT if success else NotificationStatus.FAILED
            
            # Log notification
            self.log_notification(
                notification_type=NotificationType.CONTRACTOR_NOTIFICATION,
                recipient=lead.contractor.email,
                status=status,
                timestamp=datetime.now(),
                lead_id=lead_id,
                additional_data={
                    'contractor_id': lead.contractor.id,
                    'subject': subject
                }
            )
            
            if success:
                # Update lead status
                lead.contractor_notified_at = datetime.now()
                lead.save(update_fields=['contractor_notified_at'])
                
                logger.info(f"Contractor notification sent successfully for lead {lead_id}")
                return {
                    'success': True,
                    'message': 'Contractor notification sent successfully',
                    'lead_id': lead_id,
                    'recipient': lead.contractor.email
                }
            else:
                logger.error(f"Failed to send contractor notification for lead {lead_id}")
                return {
                    'success': False,
                    'message': 'Failed to send contractor notification',
                    'lead_id': lead_id
                }
                
        except Lead.DoesNotExist:
            error_msg = f"Lead {lead_id} not found"
            logger.error(error_msg)
            self.log_notification(
                notification_type=NotificationType.CONTRACTOR_NOTIFICATION,
                recipient="unknown",
                status=NotificationStatus.FAILED,
                timestamp=datetime.now(),
                lead_id=lead_id,
                error_message=error_msg
            )
            return {'success': False, 'message': error_msg}
            
        except Exception as e:
            error_msg = f"Error sending contractor notification for lead {lead_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            try:
                recipient = lead.contractor.email if 'lead' in locals() and lead.contractor else "unknown"
                self.log_notification(
                    notification_type=NotificationType.CONTRACTOR_NOTIFICATION,
                    recipient=recipient,
                    status=NotificationStatus.FAILED,
                    timestamp=datetime.now(),
                    lead_id=lead_id,
                    error_message=str(e)
                )
            except:
                pass
                
            return {'success': False, 'message': error_msg}
    
    def send_customer_handoff(self, lead_id: int) -> Dict[str, Any]:
        """
        Send handoff notification to customer with contractor details.
        
        Args:
            lead_id: ID of the lead for customer handoff
            
        Returns:
            Dict containing success status and details
        """
        try:
            lead = Lead.objects.select_related(
                'contractor', 'customer'
            ).get(id=lead_id)
            
            if not lead.contractor:
                raise ValueError(f"No contractor assigned to lead {lead_id}")
            
            if not lead.customer.email:
                raise ValueError(f"Customer for lead {lead_id} has no email address")
            
            # Prepare email context
            context = {
                'customer_name': lead.customer.get_full_name(),
                'contractor_name': lead.contractor.company_name or lead.contractor.user.get_full_name(),
                'contractor_phone': lead.contractor.phone,
                'contractor_email': lead.contractor.email,
                'contractor_company': lead.contractor.company_name,
                'service_type': lead.service_type,
                'project_description': lead.description,
                'lead_id': lead.id,
                'contractor_rating': lead.contractor.rating,
                'contractor_experience': lead.contractor.years_experience,
                'next_steps': self._get_next_steps_for_service(lead.service_type)
            }
            
            # Render email templates
            subject = f"Your {lead.service_type} Project - Contractor Match Found"
            html_message = render_to_string(
                'emails/customer_handoff.html', 
                context
            )
            plain_message = render_to_string(
                'emails/customer_handoff.txt', 
                context
            )
            
            # Send email
            success = send_mail(
                subject=subject,
                message=plain_message,
                from_email=self.from_email,
                recipient_list=[lead.customer.email],
                html_message=html_message,
                fail_silently=False
            )
            
            status = NotificationStatus.SENT if success else NotificationStatus.FAILED
            
            # Log notification
            self.log_notification(
                notification_type=NotificationType.CUSTOMER_HANDOFF,
                recipient=lead.customer.email,
                status=status,
                timestamp=datetime.now(),
                lead_id=lead_id,
                additional_data={
                    'customer_id': lead.customer.id,
                    'contractor_id': lead.contractor.id,
                    'subject': subject
                }
            )
            
            if success:
                # Update lead status
                lead.customer_notified_at = datetime.now()
                lead.status = 'handed_off'
                lead.save(update_fields=['customer_notified_at', 'status'])
                
                logger.info(f"Customer handoff notification sent successfully for lead {lead_id}")
                return {
                    'success': True,
                    'message': 'Customer handoff notification sent successfully',
                    'lead_id': lead_id,
                    'recipient': lead.customer.email
                }
            else:
                logger.error(f"Failed to send customer handoff notification for lead {lead_id}")
                return {
                    'success': False,
                    'message': 'Failed to send customer handoff notification',
                    'lead_id': lead_id
                }
                
        except Lead.DoesNotExist:
            error_msg = f"Lead {lead_id} not found"
            logger.error(error_msg)
            self.log_notification(
                notification_type=NotificationType.CUSTOMER_HANDOFF,
                recipient="unknown",
                status=NotificationStatus.FAILED,
                timestamp=datetime.now(),
                lead_id=lead_id,
                error_message=error_msg
            )
            return {'success': False, 'message': error_msg}
            
        except Exception as e:
            error_msg = f"Error sending customer handoff notification for lead {lead_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            try:
                recipient = lead.customer.email if 'lead' in locals() and lead.customer else "unknown"
                self.log_notification(
                    notification_type=NotificationType.CUSTOMER_HANDOFF,
                    recipient=recipient,
                    status=NotificationStatus.FAILED,
                    timestamp=datetime.now(),
                    lead_id=lead_id,
                    error_message=str(e)
                )
            except:
                pass
                
            return {'success': False, 'message': error_msg}
    
    def log_notification(
        self,
        notification_type: NotificationType,
        recipient: str,
        status: NotificationStatus,
        timestamp: datetime,
        lead_id: Optional[int] = None,
        error_message: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> NotificationLog:
        """
        Log notification attempt to database.
        
        Args:
            notification_type: Type of notification
            recipient: Email address or identifier of recipient
            status: Status of the notification
            timestamp: When the notification was sent/attempted
            lead_id: Associated lead ID if applicable
            error_message: Error message if notification failed
            additional_data: Additional data to store
            
        Returns:
            NotificationLog instance
        """
        try:
            with transaction.atomic():
                notification_log = NotificationLog.objects.create(
                    notification_type=notification_type.value,
                    recipient=recipient,
                    status=status.value,
                    timestamp=timestamp,
                    lead_id=lead_id,
                    error_message=error_message,
                    additional_data=additional_data or {}
                )
                
                logger.info(
                    f"Notification logged: {notification_type.value} to {recipient} "
                    f"with status {status.value}"
                )
                
                return notification_log
                
        except Exception as e:
            logger.error(f"Failed to log notification: {str(e)}", exc_info=True)
            raise
    
    def send_system_alert(
        self,
        subject: str,
        message: str,
        recipient_email: Optional[str] = None,
        alert_level: str = "info"
    ) -> Dict[str, Any]:
        """
        Send system alert notification to admin or specified recipient.
        
        Args:
            subject: Email subject
            message: Alert message
            recipient_email: Recipient email (defaults to admin)
            alert_level: Level of alert (info, warning, error)
            
        Returns:
            Dict containing success status and details
        """
        try:
            recipient = recipient_email or self.admin_email
            
            context = {
                'alert_level': alert_level,
                'message': message,
                'timestamp': datetime.now(),
                'system_name': settings.SYSTEM_NAME if hasattr(settings, 'SYSTEM_NAME') else 'HomePro'
            }
            
            html_message = render_to_string(
                'emails/system_alert.html',
                context
            )
            plain_message = render_to_string(
                'emails/system_alert.txt',
                context
            )
            
            success = send_mail(
                subject=f"[{alert_level.upper()}] {subject}",
                message=plain_message,
                from_email=self.from_email,
                recipient_list=[recipient],
                html_message=html_message,
                fail_silently=False
            )
            
            status = NotificationStatus.SENT if success else NotificationStatus.FAILED
            
            self.log_notification(
                notification_type=NotificationType.SYSTEM_ALERT,
                recipient=recipient,
                status=status,
                timestamp=datetime.now(),
                additional_data={
                    'alert_level': alert_level,
                    'subject': subject,
                    'message': message
                }
            )
            
            return {
                'success': success,
                'message': 'System alert sent successfully' if success else 'Failed to send system alert',
                'recipient': recipient
            }
            
        except Exception as e:
            error_msg = f"Error sending system alert: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {'success': False, 'message': error_msg}
    
    def get_notification_history(
        self,
        lead_id: Optional[int] = None,
        notification_type: Optional[NotificationType] = None,
        limit: int = 100
    ) -> list:
        """
        Get notification history with optional filtering.
        
        Args:
            lead_id: Filter by lead ID
            notification_type: Filter by notification type
            limit: Maximum number of records to return
            
        Returns:
            List of notification log records
        """
        try:
            queryset = NotificationLog.objects.all()
            
            if lead_id:
                queryset = queryset.filter(lead_id=lead_id)
            
            if notification_type:
                queryset = queryset.filter(notification_type=notification_type.value)
            
            return list(
                queryset.order_by('-timestamp')[:limit].values(
                    'id', 'notification_type', 'recipient', 'status',
                    'timestamp', 'lead_id', 'error_message', 'additional_data'
                )
            )
            
        except Exception as e:
            logger.error(f"Error retrieving notification history: {str(e)}", exc_info=True)
            return []
    
    def _format_customer_address(self, customer) -> str:
        """Format customer address for display."""
        address_parts = []
        if hasattr(customer, 'street_address') and customer.street_address:
            address_parts.append(customer.street_address)
        if hasattr(customer, 'city') and customer.city:
            address_parts.append(customer.city)
        if hasattr(customer, 'state') and customer.state:
            address_parts.append(customer.state)
        if hasattr(customer, 'zip_code') and customer.zip_code:
            address_parts.append(customer.zip_code)
        
        return ', '.join(address_parts) if address_parts else 'Address not provided'
    
    def _get_next_steps_for_service(self, service_type: str) -> str:
        """Get next steps message based on service type."""
        next_steps_map = {
            'plumbing': 'Your contractor will contact you within 24 hours to schedule an assessment.',
            'electrical': 'Your contractor will reach out to discuss your electrical needs and schedule a consultation.',
            'hvac': 'Your HVAC contractor will contact you to schedule a system evaluation.',
            'roofing': 'Your roofing contractor will schedule a roof inspection at your convenience.',
            'landscaping': 'Your landscaping contractor will contact you to discuss your project vision.',
        }
        
        return next_steps_map.get(
            service_type.lower(),
            'Your contractor will contact you within 24-48 hours to discuss your project.'
        )


# Singleton instance
notification_service = NotificationService()