from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json
import logging

from ..models.lead import Lead, LeadStatus
from ..models.contractor import Contractor
from ..models.customer import Customer
from .lead_service import LeadService
from .notification_service import NotificationService
from .storage_service import StorageService
from .contractor_service import ContractorService
from .customer_service import CustomerService

logger = logging.getLogger(__name__)


class HandoffStatus(Enum):
    """Status types for lead handoff process"""

    PENDING_QUALIFICATION = "pending_qualification"
    READY_FOR_HANDOFF = "ready_for_handoff"
    HANDOFF_IN_PROGRESS = "handoff_in_progress"
    HANDOFF_COMPLETED = "handoff_completed"
    HANDOFF_FAILED = "handoff_failed"


@dataclass
class QualificationCriteria:
    """Criteria required for lead qualification"""

    min_responses_required: int = 5
    required_photo_count: int = 3
    contact_info_verified: bool = True
    project_scope_defined: bool = True
    budget_range_provided: bool = True
    timeline_specified: bool = True


@dataclass
class LeadSummary:
    """Comprehensive lead summary for contractor handoff"""

    lead_id: str
    customer_info: Dict
    project_details: Dict
    responses: List[Dict]
    photos: List[Dict]
    qualification_score: float
    estimated_value: Optional[float]
    urgency_level: str
    created_at: datetime
    qualified_at: datetime
    summary_text: str


@dataclass
class HandoffResult:
    """Result of lead handoff operation"""

    success: bool
    handoff_id: str
    lead_id: str
    contractor_id: str
    summary: Optional[LeadSummary]
    notification_sent: bool
    error_message: Optional[str] = None


class LeadHandoffService:
    """Service for managing lead handoff workflow and contractor notifications"""

    def __init__(
        self,
        lead_service: LeadService,
        notification_service: NotificationService,
        storage_service: StorageService,
        contractor_service: ContractorService,
        customer_service: CustomerService,
    ):
        self.lead_service = lead_service
        self.notification_service = notification_service
        self.storage_service = storage_service
        self.contractor_service = contractor_service
        self.customer_service = customer_service
        self.default_criteria = QualificationCriteria()

    async def detect_qualified_leads(
        self, criteria: Optional[QualificationCriteria] = None
    ) -> List[str]:
        """
        Detect leads that meet qualification criteria for handoff

        Args:
            criteria: Custom qualification criteria, uses default if None

        Returns:
            List of qualified lead IDs
        """
        try:
            criteria = criteria or self.default_criteria
            qualified_leads = []

            # Get all active leads
            active_leads = await self.lead_service.get_leads_by_status(
                [LeadStatus.IN_PROGRESS, LeadStatus.PENDING_REVIEW]
            )

            for lead in active_leads:
                if await self._is_lead_qualified(lead, criteria):
                    qualified_leads.append(lead.id)
                    logger.info(f"Lead {lead.id} qualified for handoff")

            logger.info(f"Found {len(qualified_leads)} qualified leads")
            return qualified_leads

        except Exception as e:
            logger.error(f"Error detecting qualified leads: {e}")
            raise

    async def _is_lead_qualified(
        self, lead: Lead, criteria: QualificationCriteria
    ) -> bool:
        """Check if a lead meets qualification criteria"""
        try:
            # Check response count
            responses = await self.lead_service.get_lead_responses(lead.id)
            if len(responses) < criteria.min_responses_required:
                return False

            # Check photo count
            photos = await self.storage_service.get_lead_photos(lead.id)
            if len(photos) < criteria.required_photo_count:
                return False

            # Check customer contact verification
            customer = await self.customer_service.get_customer(lead.customer_id)
            if criteria.contact_info_verified and not customer.contact_verified:
                return False

            # Check project scope definition
            project_data = lead.metadata.get("project_details", {})
            if criteria.project_scope_defined and not project_data.get("scope_defined"):
                return False

            # Check budget range
            if criteria.budget_range_provided and not project_data.get("budget_range"):
                return False

            # Check timeline
            if criteria.timeline_specified and not project_data.get("timeline"):
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking lead qualification for {lead.id}: {e}")
            return False

    async def format_lead_summary(self, lead_id: str) -> LeadSummary:
        """
        Format comprehensive lead summary for contractor handoff

        Args:
            lead_id: ID of lead to summarize

        Returns:
            Formatted lead summary
        """
        try:
            # Get lead data
            lead = await self.lead_service.get_lead(lead_id)
            if not lead:
                raise ValueError(f"Lead {lead_id} not found")

            # Get customer info
            customer = await self.customer_service.get_customer(lead.customer_id)
            customer_info = {
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "address": customer.address,
                "contact_verified": customer.contact_verified,
                "preferred_contact_method": customer.preferred_contact_method,
            }

            # Get project details
            project_details = lead.metadata.get("project_details", {})

            # Get responses
            responses = await self.lead_service.get_lead_responses(lead_id)
            formatted_responses = [
                {
                    "question": r.question,
                    "answer": r.answer,
                    "timestamp": r.created_at,
                    "confidence": r.confidence_score,
                }
                for r in responses
            ]

            # Get photos
            photos = await self.storage_service.get_lead_photos(lead_id)
            formatted_photos = [
                {
                    "url": p.url,
                    "description": p.description,
                    "analysis": p.analysis_results,
                    "timestamp": p.uploaded_at,
                }
                for p in photos
            ]

            # Calculate qualification score
            qualification_score = await self._calculate_qualification_score(lead)

            # Estimate project value
            estimated_value = await self._estimate_project_value(lead, responses)

            # Determine urgency level
            urgency_level = self._determine_urgency_level(lead, responses)

            # Generate summary text
            summary_text = await self._generate_summary_text(
                lead, customer, responses, project_details
            )

            return LeadSummary(
                lead_id=lead_id,
                customer_info=customer_info,
                project_details=project_details,
                responses=formatted_responses,
                photos=formatted_photos,
                qualification_score=qualification_score,
                estimated_value=estimated_value,
                urgency_level=urgency_level,
                created_at=lead.created_at,
                qualified_at=datetime.utcnow(),
                summary_text=summary_text,
            )

        except Exception as e:
            logger.error(f"Error formatting lead summary for {lead_id}: {e}")
            raise

    async def _calculate_qualification_score(self, lead: Lead) -> float:
        """Calculate qualification score based on lead completeness"""
        try:
            score = 0.0
            max_score = 10.0

            # Response completeness (30%)
            responses = await self.lead_service.get_lead_responses(lead.id)
            response_score = min(len(responses) / 10, 1.0) * 3.0
            score += response_score

            # Photo completeness (20%)
            photos = await self.storage_service.get_lead_photos(lead.id)
            photo_score = min(len(photos) / 5, 1.0) * 2.0
            score += photo_score

            # Customer verification (20%)
            customer = await self.customer_service.get_customer(lead.customer_id)
            if customer.contact_verified:
                score += 2.0

            # Project details (30%)
            project_details = lead.metadata.get("project_details", {})
            detail_score = 0
            if project_details.get("scope_defined"):
                detail_score += 1.0
            if project_details.get("budget_range"):
                detail_score += 1.0
            if project_details.get("timeline"):
                detail_score += 1.0
            score += detail_score

            return round(score, 2)

        except Exception as e:
            logger.error(f"Error calculating qualification score for {lead.id}: {e}")
            return 0.0

    async def _estimate_project_value(
        self, lead: Lead, responses: List
    ) -> Optional[float]:
        """Estimate project value based on responses and project type"""
        try:
            project_type = lead.metadata.get("project_type")

            # Base estimates by project type
            base_estimates = {
                "kitchen_remodel": 25000,
                "bathroom_remodel": 15000,
                "roofing": 12000,
                "flooring": 8000,
                "painting": 3000,
                "plumbing": 2000,
                "electrical": 2500,
            }

            base_value = base_estimates.get(project_type, 5000)

            # Adjust based on responses
            multiplier = 1.0

            for response in responses:
                answer = response.answer.lower()

                # Size indicators
                if any(word in answer for word in ["large", "big", "major"]):
                    multiplier *= 1.5
                elif any(word in answer for word in ["small", "minor", "simple"]):
                    multiplier *= 0.7

                # Quality indicators
                if any(word in answer for word in ["high-end", "luxury", "premium"]):
                    multiplier *= 2.0
                elif any(word in answer for word in ["budget", "basic", "cheap"]):
                    multiplier *= 0.6

            return round(base_value * multiplier, 2)

        except Exception as e:
            logger.error(f"Error estimating project value for {lead.id}: {e}")
            return None

    def _determine_urgency_level(self, lead: Lead, responses: List) -> str:
        """Determine urgency level based on lead data"""
        try:
            urgency_keywords = {
                "high": [
                    "urgent",
                    "emergency",
                    "asap",
                    "immediately",
                    "leak",
                    "broken",
                ],
                "medium": ["soon", "this month", "quickly", "few weeks"],
                "low": ["eventually", "no rush", "when possible", "future"],
            }

            # Check responses for urgency keywords
            for response in responses:
                answer = response.answer.lower()

                for level, keywords in urgency_keywords.items():
                    if any(keyword in answer for keyword in keywords):
                        return level

            # Default based on lead age
            days_old = (datetime.utcnow() - lead.created_at).days
            if days_old < 1:
                return "high"
            elif days_old < 7:
                return "medium"
            else:
                return "low"

        except Exception as e:
            logger.error(f"Error determining urgency level for {lead.id}: {e}")
            return "medium"

    async def _generate_summary_text(
        self, lead: Lead, customer: Customer, responses: List, project_details: Dict
    ) -> str:
        """Generate human-readable summary text"""
        try:
            summary_parts = []

            # Customer intro
            summary_parts.append(
                f"Customer: {customer.name} ({customer.email}, {customer.phone})"
            )

            # Project type and scope
            project_type = (
                lead.metadata.get("project_type", "General").replace("_", " ").title()
            )
            summary_parts.append(f"Project Type: {project_type}")

            if project_details.get("scope_defined"):
                summary_parts.append(
                    f"Scope: {project_details.get('scope_description', 'Defined')}"
                )

            # Key responses
            key_responses = responses[:3]  # Top 3 responses
            if key_responses:
                summary_parts.append("Key Requirements:")
                for response in key_responses:
                    summary_parts.append(f"- {response.question}: {response.answer}")

            # Budget and timeline
            if project_details.get("budget_range"):
                summary_parts.append(f"Budget Range: {project_details['budget_range']}")

            if project_details.get("timeline"):
                summary_parts.append(f"Timeline: {project_details['timeline']}")

            return "\n".join(summary_parts)

        except Exception as e:
            logger.error(f"Error generating summary text for {lead.id}: {e}")
            return "Summary generation failed"

    async def coordinate_contractor_notifications(
        self, lead_summary: LeadSummary, target_contractors: Optional[List[str]] = None
    ) -> List[str]:
        """
        Send notifications to appropriate contractors

        Args:
            lead_summary: Formatted lead summary
            target_contractors: Specific contractor IDs, auto-select if None

        Returns:
            List of contractor IDs that were notified
        """
        try:
            if target_contractors is None:
                target_contractors = await self._select_target_contractors(lead_summary)

            notified_contractors = []

            for contractor_id in target_contractors:
                try:
                    contractor = await self.contractor_service.get_contractor(
                        contractor_id
                    )
                    if not contractor:
                        logger.warning(f"Contractor {contractor_id} not found")
                        continue

                    # Create notification content
                    notification_content = self._create_contractor_notification(
                        lead_summary, contractor
                    )

                    # Send notification
                    success = (
                        await self.notification_service.send_contractor_notification(
                            contractor_id=contractor_id,
                            content=notification_content,
                            priority=(
                                "high"
                                if lead_summary.urgency_level == "high"
                                else "normal"
                            ),
                        )
                    )

                    if success:
                        notified_contractors.append(contractor_id)
                        logger.info(
                            f"Notified contractor {contractor_id} about lead {lead_summary.lead_id}"
                        )
                    else:
                        logger.error(f"Failed to notify contractor {contractor_id}")

                except Exception as e:
                    logger.error(f"Error notifying contractor {contractor_id}: {e}")
                    continue

            return notified_contractors

        except Exception as e:
            logger.error(f"Error coordinating contractor notifications: {e}")
            raise

    async def _select_target_contractors(self, lead_summary: LeadSummary) -> List[str]:
        """Select appropriate contractors based on lead requirements"""
        try:
            project_type = lead_summary.project_details.get("project_type")
            location = lead_summary.customer_info.get("address", {}).get("zip_code")

            # Get contractors by specialization and location
            contractors = await self.contractor_service.find_contractors_by_criteria(
                specializations=[project_type] if project_type else None,
                service_area=location,
                min_rating=4.0,
                is_active=True,
            )

            # Limit to top 3 contractors
            selected = []
            for contractor in contractors[:3]:
                if contractor.is_available and contractor.accepts_new_leads:
                    selected.append(contractor.id)

            return selected

        except Exception as e:
            logger.error(f"Error selecting target contractors: {e}")
            return []

    def _create_contractor_notification(
        self, lead_summary: LeadSummary, contractor: Contractor
    ) -> Dict:
        """Create notification content for contractor"""
        return {
            "type": "new_lead",
            "subject": f"New {lead_summary.urgency_level.title()} Priority Lead Available",
            "lead_id": lead_summary.lead_id,
            "customer_name": lead_summary.customer_info["name"],
            "project_type": lead_summary.project_details.get("project_type", "General")
            .replace("_", " ")
            .title(),
            "location": lead_summary.customer_info.get("address", {}).get(
                "city", "Unknown"
            ),
            "qualification_score": lead_summary.qualification_score,
            "estimated_value": lead_summary.estimated_value,
            "urgency_level": lead_summary.urgency_level,
            "summary": lead_summary.summary_text,
            "photos_count": len(lead_summary.photos),
            "responses_count": len(lead_summary.responses),
            "action_url": f"/contractor/leads/{lead_summary.lead_id}",
            "expires_at": datetime.utcnow().isoformat(),
        }

    async def update_lead_status_to_completed(self, lead_id: str) -> bool:
        """
        Update lead status to completed after successful handoff

        Args:
            lead_id: ID of lead to update

        Returns:
            True if update successful, False otherwise
        """
        try:
            success = await self.lead_service.update_lead_status(
                lead_id=lead_id,
                new_status=LeadStatus.COMPLETED,
                metadata={
                    "completed_at": datetime.utcnow().isoformat(),
                    "handoff_completed": True,
                },
            )

            if success:
                logger.info(f"Lead {lead_id} status updated to completed")
            else:
                logger.error(f"Failed to update lead {lead_id} status")

            return success

        except Exception as e:
            logger.error(f"Error updating lead status for {lead_id}: {e}")
            return False

    async def orchestrate_handoff_workflow(self, lead_id: str) -> HandoffResult:
        """
        Orchestrate the complete lead handoff workflow

        Args:
            lead_id: ID of lead to hand off

        Returns:
            HandoffResult with operation details
        """
        handoff_id = f"handoff_{lead_id}_{int(datetime.utcnow().timestamp())}"

        try:
            logger.info(f"Starting handoff workflow for lead {lead_id}")

            # 1. Verify lead is qualified
            lead = await self.lead_service.get_lead(lead_id)
            if not lead:
                return HandoffResult(
                    success=False,
                    handoff_id=handoff_id,
                    lead_id=lead_id,
                    contractor_id="",
                    summary=None,
                    notification_sent=False,
                    error_message="Lead not found",
                )

            is_qualified = await self._is_lead_qualified(lead, self.default_criteria)
            if not is_qualified:
                return HandoffResult(
                    success=False,
                    handoff_id=handoff_id,
                    lead_id=lead_id,
                    contractor_id="",
                    summary=None,
                    notification_sent=False,
                    error_message="Lead does not meet qualification criteria",
                )

            # 2. Format lead summary
            lead_summary = await self.format_lead_summary(lead_id)

            # 3. Coordinate contractor notifications
            notified_contractors = await self.coordinate_contractor_notifications(
                lead_summary
            )

            if not notified_contractors:
                return HandoffResult(
                    success=False,
                    handoff_id=handoff_id,
                    lead_id=lead_id,
                    contractor_id="",
                    summary=lead_summary,
                    notification_sent=False,
                    error_message="No contractors available for notification",
                )

            # 4. Update lead status
            status_updated = await self.update_lead_status_to_completed(lead_id)

            # 5. Store handoff record
            handoff_record = {
                "handoff_id": handoff_id,
                "lead_id": lead_id,
                "contractors_notified": notified_contractors,
                "handoff_completed_at": datetime.utcnow().isoformat(),
                "qualification_score": lead_summary.qualification_score,
                "estimated_value": lead_summary.estimated_value,
            }

            await self.storage_service.store_handoff_record(handoff_record)

            # 6. Send confirmation to customer
            await self._send_customer_handoff_confirmation(
                lead_id, len(notified_contractors)
            )

            logger.info(
                f"Handoff workflow completed for lead {lead_id}. "
                f"Notified {len(notified_contractors)} contractors."
            )

            return HandoffResult(
                success=True,
                handoff_id=handoff_id,
                lead_id=lead_id,
                contractor_id=notified_contractors[0] if notified_contractors else "",
                summary=lead_summary,
                notification_sent=True,
                error_message=None,
            )

        except Exception as e:
            error_msg = f"Handoff workflow failed for lead {lead_id}: {e}"
            logger.error(error_msg)

            return HandoffResult(
                success=False,
                handoff_id=handoff_id,
                lead_id=lead_id,
                contractor_id="",
                summary=None,
                notification_sent=False,
                error_message=error_msg,
            )

    async def _send_customer_handoff_confirmation(
        self, lead_id: str, contractor_count: int
    ) -> bool:
        """Send handoff confirmation to customer"""
        try:
            lead = await self.lead_service.get_lead(lead_id)
            customer = await self.customer_service.get_customer(lead.customer_id)

            confirmation_content = {
                "type": "handoff_confirmation",
                "subject": "Your Project Request Has Been Submitted",
                "message": f"Great news! Your project request has been submitted to {contractor_count} qualified contractors in your area. You should expect to hear from them within 24 hours.",
                "next_steps": [
                    "Contractors will review your project details",
                    "You'll receive quotes and proposals directly",
                    "Compare options and choose the best fit",
                    "Schedule consultations as needed",
                ],
            }

            return await self.notification_service.send_customer_notification(
                customer_id=customer.id, content=confirmation_content
            )

        except Exception as e:
            logger.error(f"Error sending customer handoff confirmation: {e}")
            return False

    async def get_handoff_analytics(
        self, date_range: Tuple[datetime, datetime]
    ) -> Dict:
        """Get analytics for handoff operations"""
        try:
            start_date, end_date = date_range

            # Get handoff records in date range
            handoff_records = await self.storage_service.get_handoff_records(
                start_date=start_date, end_date=end_date
            )

            if not handoff_records:
                return {
                    "total_handoffs": 0,
                    "success_rate": 0.0,
                    "avg_qualification_score": 0.0,
                    "total_estimated_value": 0.0,
                    "contractors_engaged": 0,
                }

            successful_handoffs = [
                r for r in handoff_records if r.get("handoff_completed_at")
            ]
            contractors_engaged = set()

            for record in handoff_records:
                contractors_engaged.update(record.get("contractors_notified", []))

            return {
                "total_handoffs": len(handoff_records),
                "successful_handoffs": len(successful_handoffs),
                "success_rate": len(successful_handoffs) / len(handoff_records),
                "avg_qualification_score": sum(
                    r.get("qualification_score", 0) for r in handoff_records
                )
                / len(handoff_records),
                "total_estimated_value": sum(
                    r.get("estimated_value", 0)
                    for r in handoff_records
                    if r.get("estimated_value")
                ),
                "unique_contractors_engaged": len(contractors_engaged),
                "avg_contractors_per_lead": sum(
                    len(r.get("contractors_notified", [])) for r in handoff_records
                )
                / len(handoff_records),
            }

        except Exception as e:
            logger.error(f"Error getting handoff analytics: {e}")
            raise
