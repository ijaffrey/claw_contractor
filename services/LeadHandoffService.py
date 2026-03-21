from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from dataclasses import dataclass

from ..models.lead import Lead
from ..services.notification_service import NotificationService
from ..repositories.lead_repository import LeadRepository
from ..utils.exceptions import LeadHandoffError, ValidationError


@dataclass
class QualificationCriteria:
    """Configuration for lead qualification criteria"""
    min_score: int = 75
    required_fields: List[str] = None
    required_engagement_actions: int = 3
    min_budget: Optional[float] = None
    required_contact_attempts: int = 2
    
    def __post_init__(self):
        if self.required_fields is None:
            self.required_fields = ['email', 'company', 'phone']


class LeadHandoffService:
    """Service for handling qualified lead detection and handoff process"""
    
    def __init__(
        self,
        lead_repository: LeadRepository,
        notification_service: NotificationService,
        qualification_criteria: Optional[QualificationCriteria] = None
    ):
        self.lead_repository = lead_repository
        self.notification_service = notification_service
        self.qualification_criteria = qualification_criteria or QualificationCriteria()
        self.logger = logging.getLogger(__name__)
    
    def is_lead_qualified(self, lead: Lead) -> bool:
        """
        Determine if a lead meets qualification criteria for handoff
        
        Args:
            lead: Lead object to evaluate
            
        Returns:
            bool: True if lead is qualified, False otherwise
        """
        try:
            if not lead:
                self.logger.warning("Cannot qualify None lead")
                return False
            
            # Check lead score threshold
            if not self._check_score_threshold(lead):
                self.logger.debug(f"Lead {lead.id} failed score threshold check")
                return False
            
            # Check required fields are populated
            if not self._check_required_fields(lead):
                self.logger.debug(f"Lead {lead.id} missing required fields")
                return False
            
            # Check engagement level
            if not self._check_engagement_level(lead):
                self.logger.debug(f"Lead {lead.id} insufficient engagement")
                return False
            
            # Check budget qualification if specified
            if not self._check_budget_qualification(lead):
                self.logger.debug(f"Lead {lead.id} does not meet budget requirements")
                return False
            
            # Check contact attempts
            if not self._check_contact_attempts(lead):
                self.logger.debug(f"Lead {lead.id} insufficient contact attempts")
                return False
            
            # Check lead is in correct status for handoff
            if not self._check_handoff_eligibility(lead):
                self.logger.debug(f"Lead {lead.id} not eligible for handoff")
                return False
            
            self.logger.info(f"Lead {lead.id} qualified for handoff")
            return True
            
        except Exception as e:
            self.logger.error(f"Error qualifying lead {lead.id if lead else 'None'}: {str(e)}")
            return False
    
    def process_lead_handoff(self, lead: Lead) -> Dict[str, Any]:
        """
        Process the complete handoff workflow for a qualified lead
        
        Args:
            lead: Lead object to hand off
            
        Returns:
            Dict containing handoff results and metadata
            
        Raises:
            LeadHandoffError: If handoff process fails
            ValidationError: If lead data is invalid
        """
        try:
            if not lead:
                raise ValidationError("Cannot process handoff for None lead")
            
            self.logger.info(f"Starting handoff process for lead {lead.id}")
            
            # Validate lead qualification
            if not self.is_lead_qualified(lead):
                raise LeadHandoffError(f"Lead {lead.id} does not meet qualification criteria")
            
            # Update lead status to completed
            self.update_lead_status(lead.id, 'completed')
            
            # Add handoff metadata
            handoff_data = self._prepare_handoff_data(lead)
            self._update_lead_handoff_metadata(lead.id, handoff_data)
            
            # Trigger notifications
            notification_results = self._send_handoff_notifications(lead, handoff_data)
            
            # Log successful handoff
            self._log_handoff_completion(lead, handoff_data)
            
            result = {
                'lead_id': lead.id,
                'status': 'completed',
                'handoff_timestamp': datetime.utcnow().isoformat(),
                'qualification_score': self._calculate_qualification_score(lead),
                'handoff_data': handoff_data,
                'notifications_sent': notification_results,
                'success': True
            }
            
            self.logger.info(f"Successfully completed handoff for lead {lead.id}")
            return result
            
        except (LeadHandoffError, ValidationError):
            raise
        except Exception as e:
            error_msg = f"Unexpected error during lead handoff for {lead.id if lead else 'None'}: {str(e)}"
            self.logger.error(error_msg)
            raise LeadHandoffError(error_msg) from e
    
    def update_lead_status(self, lead_id: str, status: str) -> bool:
        """
        Update lead status in the repository
        
        Args:
            lead_id: ID of the lead to update
            status: New status value
            
        Returns:
            bool: True if update successful
            
        Raises:
            ValidationError: If parameters are invalid
            LeadHandoffError: If update fails
        """
        try:
            if not lead_id:
                raise ValidationError("Lead ID cannot be empty")
            
            if not status:
                raise ValidationError("Status cannot be empty")
            
            # Validate status value
            valid_statuses = ['new', 'contacted', 'qualified', 'completed', 'unqualified', 'closed']
            if status not in valid_statuses:
                raise ValidationError(f"Invalid status: {status}. Must be one of {valid_statuses}")
            
            # Update in repository
            update_data = {
                'status': status,
                'updated_at': datetime.utcnow(),
                'status_changed_at': datetime.utcnow()
            }
            
            success = self.lead_repository.update_lead(lead_id, update_data)
            
            if not success:
                raise LeadHandoffError(f"Failed to update status for lead {lead_id}")
            
            self.logger.info(f"Updated lead {lead_id} status to {status}")
            return True
            
        except (ValidationError, LeadHandoffError):
            raise
        except Exception as e:
            error_msg = f"Error updating lead status for {lead_id}: {str(e)}"
            self.logger.error(error_msg)
            raise LeadHandoffError(error_msg) from e
    
    def _check_score_threshold(self, lead: Lead) -> bool:
        """Check if lead score meets minimum threshold"""
        if not hasattr(lead, 'score') or lead.score is None:
            return False
        return lead.score >= self.qualification_criteria.min_score
    
    def _check_required_fields(self, lead: Lead) -> bool:
        """Check if all required fields are populated"""
        for field in self.qualification_criteria.required_fields:
            value = getattr(lead, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                return False
        return True
    
    def _check_engagement_level(self, lead: Lead) -> bool:
        """Check if lead has sufficient engagement actions"""
        if not hasattr(lead, 'engagement_actions') or not lead.engagement_actions:
            return False
        return len(lead.engagement_actions) >= self.qualification_criteria.required_engagement_actions
    
    def _check_budget_qualification(self, lead: Lead) -> bool:
        """Check if lead meets budget requirements"""
        if self.qualification_criteria.min_budget is None:
            return True
        
        if not hasattr(lead, 'budget') or lead.budget is None:
            return False
        
        return lead.budget >= self.qualification_criteria.min_budget
    
    def _check_contact_attempts(self, lead: Lead) -> bool:
        """Check if minimum contact attempts have been made"""
        if not hasattr(lead, 'contact_attempts') or not lead.contact_attempts:
            return False
        return len(lead.contact_attempts) >= self.qualification_criteria.required_contact_attempts
    
    def _check_handoff_eligibility(self, lead: Lead) -> bool:
        """Check if lead is in correct status for handoff"""
        if not hasattr(lead, 'status') or not lead.status:
            return False
        
        eligible_statuses = ['qualified', 'contacted']
        return lead.status in eligible_statuses
    
    def _calculate_qualification_score(self, lead: Lead) -> float:
        """Calculate overall qualification score for the lead"""
        score = 0.0
        max_score = 100.0
        
        # Base score from lead scoring
        if hasattr(lead, 'score') and lead.score:
            score += min(lead.score, 40)  # Max 40 points from base score
        
        # Engagement score
        if hasattr(lead, 'engagement_actions') and lead.engagement_actions:
            engagement_score = min(len(lead.engagement_actions) * 5, 25)  # Max 25 points
            score += engagement_score
        
        # Data completeness score
        completed_fields = sum(1 for field in self.qualification_criteria.required_fields 
                             if getattr(lead, field, None))
        data_score = (completed_fields / len(self.qualification_criteria.required_fields)) * 20  # Max 20 points
        score += data_score
        
        # Contact attempts score
        if hasattr(lead, 'contact_attempts') and lead.contact_attempts:
            contact_score = min(len(lead.contact_attempts) * 3, 15)  # Max 15 points
            score += contact_score
        
        return min(score, max_score)
    
    def _prepare_handoff_data(self, lead: Lead) -> Dict[str, Any]:
        """Prepare comprehensive handoff data package"""
        return {
            'lead_id': lead.id,
            'qualification_score': self._calculate_qualification_score(lead),
            'handoff_timestamp': datetime.utcnow().isoformat(),
            'qualification_criteria_met': {
                'score_threshold': self._check_score_threshold(lead),
                'required_fields': self._check_required_fields(lead),
                'engagement_level': self._check_engagement_level(lead),
                'budget_qualification': self._check_budget_qualification(lead),
                'contact_attempts': self._check_contact_attempts(lead)
            },
            'lead_summary': {
                'company': getattr(lead, 'company', None),
                'contact_name': getattr(lead, 'name', None),
                'email': getattr(lead, 'email', None),
                'phone': getattr(lead, 'phone', None),
                'budget': getattr(lead, 'budget', None),
                'source': getattr(lead, 'source', None),
                'industry': getattr(lead, 'industry', None)
            },
            'engagement_summary': {
                'total_actions': len(getattr(lead, 'engagement_actions', [])),
                'last_engagement': self._get_last_engagement_date(lead),
                'contact_attempts': len(getattr(lead, 'contact_attempts', []))
            }
        }
    
    def _get_last_engagement_date(self, lead: Lead) -> Optional[str]:
        """Get the date of last engagement action"""
        if not hasattr(lead, 'engagement_actions') or not lead.engagement_actions:
            return None
        
        try:
            last_action = max(lead.engagement_actions, 
                            key=lambda x: x.get('timestamp', datetime.min))
            return last_action.get('timestamp', '').isoformat() if hasattr(last_action.get('timestamp', ''), 'isoformat') else str(last_action.get('timestamp', ''))
        except (ValueError, AttributeError):
            return None
    
    def _update_lead_handoff_metadata(self, lead_id: str, handoff_data: Dict[str, Any]) -> None:
        """Update lead with handoff metadata"""
        metadata_update = {
            'handoff_data': handoff_data,
            'handed_off_at': datetime.utcnow(),
            'handoff_completed': True
        }
        
        self.lead_repository.update_lead(lead_id, metadata_update)
    
    def _send_handoff_notifications(self, lead: Lead, handoff_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Send notifications for lead handoff"""
        notifications = []
        
        try:
            # Notify sales team
            sales_notification = self.notification_service.send_lead_handoff_notification(
                lead=lead,
                handoff_data=handoff_data,
                recipients=['sales-team']
            )
            notifications.append({
                'type': 'sales_team',
                'status': 'sent' if sales_notification else 'failed',
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Notify marketing team
            marketing_notification = self.notification_service.send_lead_status_update(
                lead_id=lead.id,
                old_status=getattr(lead, 'previous_status', 'unknown'),
                new_status='completed',
                recipients=['marketing-team']
            )
            notifications.append({
                'type': 'marketing_team',
                'status': 'sent' if marketing_notification else 'failed',
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Notify lead owner if specified
            if hasattr(lead, 'owner_id') and lead.owner_id:
                owner_notification = self.notification_service.send_personal_notification(
                    user_id=lead.owner_id,
                    message=f"Lead {lead.id} has been qualified and handed off",
                    notification_type='lead_handoff'
                )
                notifications.append({
                    'type': 'lead_owner',
                    'status': 'sent' if owner_notification else 'failed',
                    'timestamp': datetime.utcnow().isoformat()
                })
            
        except Exception as e:
            self.logger.error(f"Error sending handoff notifications for lead {lead.id}: {str(e)}")
            notifications.append({
                'type': 'error',
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        
        return notifications
    
    def _log_handoff_completion(self, lead: Lead, handoff_data: Dict[str, Any]) -> None:
        """Log handoff completion for audit purposes"""
        self.logger.info(
            f"Lead handoff completed - ID: {lead.id}, "
            f"Score: {handoff_data.get('qualification_score', 'N/A')}, "
            f"Company: {getattr(lead, 'company', 'Unknown')}, "
            f"Timestamp: {handoff_data.get('handoff_timestamp')}"
        )
    
    def get_handoff_statistics(self, date_range: Optional[Dict[str, datetime]] = None) -> Dict[str, Any]:
        """Get statistics about lead handoffs"""
        try:
            stats = self.lead_repository.get_handoff_statistics(date_range)
            return {
                'total_handoffs': stats.get('total_handoffs', 0),
                'average_qualification_score': stats.get('avg_score', 0.0),
                'handoff_success_rate': stats.get('success_rate', 0.0),
                'top_sources': stats.get('top_sources', []),
                'date_range': date_range
            }
        except Exception as e:
            self.logger.error(f"Error retrieving handoff statistics: {str(e)}")
            return {
                'total_handoffs': 0,
                'error': str(e)
            }