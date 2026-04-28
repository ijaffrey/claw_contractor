"""
Lead Summary Formatter Module

Handles comprehensive formatting of lead summaries including all qualification data,
customer responses, photo analysis, conversation history, contact details,
problem diagnosis, and structured outputs for notifications and handoffs.
"""

import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class SummaryType(Enum):
    """Types of summary outputs."""

    CONTRACTOR_NOTIFICATION = "contractor_notification"
    CUSTOMER_HANDOFF = "customer_handoff"
    FULL_SUMMARY = "full_summary"
    BRIEF_SUMMARY = "brief_summary"


class UrgencyLevel(Enum):
    """Urgency levels for leads."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


@dataclass
class ContactInfo:
    """Customer contact information structure."""

    name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    preferred_contact_method: Optional[str] = None
    preferred_contact_times: List[str] = None
    alternate_phone: Optional[str] = None


@dataclass
class PhotoAnalysis:
    """Photo analysis results structure."""

    photo_count: int
    analysis_results: List[Dict[str, Any]]
    damage_severity: Optional[str] = None
    estimated_repair_type: Optional[str] = None
    confidence_score: Optional[float] = None
    key_findings: List[str] = None


@dataclass
class ConversationSummary:
    """Conversation history summary structure."""

    total_messages: int
    conversation_duration: Optional[str] = None
    key_topics: List[str] = None
    customer_sentiment: Optional[str] = None
    main_concerns: List[str] = None
    follow_up_requests: List[str] = None


@dataclass
class ProblemDiagnosis:
    """Problem diagnosis summary structure."""

    primary_issue: str
    secondary_issues: List[str]
    affected_areas: List[str]
    urgency_level: UrgencyLevel
    estimated_complexity: str
    recommended_services: List[str]
    timeline_estimate: Optional[str] = None


class LeadSummaryFormatter:
    """Main class for formatting lead summaries."""

    def __init__(self):
        """Initialize the formatter with configuration."""
        self.timestamp_format = "%Y-%m-%d %H:%M:%S %Z"
        self.phone_pattern = re.compile(
            r"^\+?1?[-.\s]?(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})$"
        )
        self.email_pattern = re.compile(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )

    def format_customer_responses(self, responses: Dict[str, Any]) -> str:
        """
        Format customer qualification responses into readable format.

        Args:
            responses: Dictionary of customer responses to qualification questions

        Returns:
            Formatted string of customer responses
        """
        if not responses:
            return "No customer responses recorded."

        formatted_responses = []
        formatted_responses.append("=== CUSTOMER QUALIFICATION RESPONSES ===")

        # Group responses by category if possible
        categories = self._categorize_responses(responses)

        for category, items in categories.items():
            if items:
                formatted_responses.append(f"\n{category.upper()}:")
                for question, answer in items:
                    formatted_answer = self._format_response_value(answer)
                    formatted_responses.append(f"• {question}: {formatted_answer}")

        # Add timestamp if available
        if "timestamp" in responses:
            timestamp = self._format_timestamp(responses["timestamp"])
            formatted_responses.append(f"\nResponses collected: {timestamp}")

        return "\n".join(formatted_responses)

    def format_photo_analysis(self, analysis: PhotoAnalysis) -> str:
        """
        Format photo analysis results into readable format.

        Args:
            analysis: PhotoAnalysis object containing analysis results

        Returns:
            Formatted string of photo analysis
        """
        if not analysis or analysis.photo_count == 0:
            return "No photos provided for analysis."

        formatted_analysis = []
        formatted_analysis.append("=== PHOTO ANALYSIS RESULTS ===")
        formatted_analysis.append(f"Photos analyzed: {analysis.photo_count}")

        if analysis.confidence_score is not None:
            confidence_pct = round(analysis.confidence_score * 100, 1)
            formatted_analysis.append(f"Analysis confidence: {confidence_pct}%")

        if analysis.damage_severity:
            formatted_analysis.append(
                f"Damage severity: {analysis.damage_severity.title()}"
            )

        if analysis.estimated_repair_type:
            formatted_analysis.append(
                f"Estimated repair type: {analysis.estimated_repair_type}"
            )

        if analysis.key_findings:
            formatted_analysis.append("\nKey findings:")
            for finding in analysis.key_findings:
                formatted_analysis.append(f"• {finding}")

        if analysis.analysis_results:
            formatted_analysis.append("\nDetailed analysis:")
            for i, result in enumerate(analysis.analysis_results, 1):
                formatted_analysis.append(f"\nPhoto {i}:")
                if "description" in result:
                    formatted_analysis.append(f"  Description: {result['description']}")
                if "damage_detected" in result:
                    formatted_analysis.append(
                        f"  Damage detected: {', '.join(result['damage_detected'])}"
                    )
                if "materials_identified" in result:
                    formatted_analysis.append(
                        f"  Materials: {', '.join(result['materials_identified'])}"
                    )

        return "\n".join(formatted_analysis)

    def format_conversation_summary(self, summary: ConversationSummary) -> str:
        """
        Format conversation history summary.

        Args:
            summary: ConversationSummary object

        Returns:
            Formatted conversation summary string
        """
        if not summary or summary.total_messages == 0:
            return "No conversation history available."

        formatted_summary = []
        formatted_summary.append("=== CONVERSATION SUMMARY ===")
        formatted_summary.append(f"Total messages: {summary.total_messages}")

        if summary.conversation_duration:
            formatted_summary.append(f"Duration: {summary.conversation_duration}")

        if summary.customer_sentiment:
            formatted_summary.append(
                f"Customer sentiment: {summary.customer_sentiment.title()}"
            )

        if summary.key_topics:
            formatted_summary.append("\nKey topics discussed:")
            for topic in summary.key_topics:
                formatted_summary.append(f"• {topic}")

        if summary.main_concerns:
            formatted_summary.append("\nMain customer concerns:")
            for concern in summary.main_concerns:
                formatted_summary.append(f"• {concern}")

        if summary.follow_up_requests:
            formatted_summary.append("\nFollow-up requests:")
            for request in summary.follow_up_requests:
                formatted_summary.append(f"• {request}")

        return "\n".join(formatted_summary)

    def format_contact_details(self, contact: ContactInfo) -> str:
        """
        Format customer contact details.

        Args:
            contact: ContactInfo object

        Returns:
            Formatted contact details string
        """
        if not contact:
            return "No contact information available."

        formatted_contact = []
        formatted_contact.append("=== CUSTOMER CONTACT DETAILS ===")

        formatted_contact.append(f"Name: {contact.name}")

        # Format phone number
        formatted_phone = self._format_phone_number(contact.phone)
        formatted_contact.append(f"Phone: {formatted_phone}")

        if contact.alternate_phone:
            alt_phone = self._format_phone_number(contact.alternate_phone)
            formatted_contact.append(f"Alternate phone: {alt_phone}")

        if contact.email:
            formatted_contact.append(f"Email: {contact.email}")

        if contact.address:
            formatted_contact.append(f"Address: {contact.address}")

        if contact.preferred_contact_method:
            formatted_contact.append(
                f"Preferred contact method: {contact.preferred_contact_method}"
            )

        if contact.preferred_contact_times:
            times_str = ", ".join(contact.preferred_contact_times)
            formatted_contact.append(f"Preferred contact times: {times_str}")

        return "\n".join(formatted_contact)

    def format_problem_diagnosis(self, diagnosis: ProblemDiagnosis) -> str:
        """
        Format problem diagnosis summary.

        Args:
            diagnosis: ProblemDiagnosis object

        Returns:
            Formatted diagnosis string
        """
        if not diagnosis:
            return "No problem diagnosis available."

        formatted_diagnosis = []
        formatted_diagnosis.append("=== PROBLEM DIAGNOSIS ===")

        formatted_diagnosis.append(f"Primary issue: {diagnosis.primary_issue}")

        if diagnosis.secondary_issues:
            formatted_diagnosis.append("Secondary issues:")
            for issue in diagnosis.secondary_issues:
                formatted_diagnosis.append(f"• {issue}")

        if diagnosis.affected_areas:
            areas_str = ", ".join(diagnosis.affected_areas)
            formatted_diagnosis.append(f"Affected areas: {areas_str}")

        # Format urgency with appropriate styling
        urgency_display = self._format_urgency(diagnosis.urgency_level)
        formatted_diagnosis.append(f"Urgency level: {urgency_display}")

        formatted_diagnosis.append(
            f"Estimated complexity: {diagnosis.estimated_complexity}"
        )

        if diagnosis.recommended_services:
            formatted_diagnosis.append("Recommended services:")
            for service in diagnosis.recommended_services:
                formatted_diagnosis.append(f"• {service}")

        if diagnosis.timeline_estimate:
            formatted_diagnosis.append(
                f"Estimated timeline: {diagnosis.timeline_estimate}"
            )

        return "\n".join(formatted_diagnosis)

    def generate_contractor_notification(
        self,
        contact: ContactInfo,
        diagnosis: ProblemDiagnosis,
        photo_analysis: Optional[PhotoAnalysis] = None,
        responses: Optional[Dict[str, Any]] = None,
        lead_id: Optional[str] = None,
    ) -> str:
        """
        Generate contractor notification message.

        Args:
            contact: Customer contact information
            diagnosis: Problem diagnosis
            photo_analysis: Optional photo analysis results
            responses: Optional customer responses
            lead_id: Optional lead identifier

        Returns:
            Formatted contractor notification
        """
        notification = []

        # Header with urgency indicator
        urgency_indicator = self._get_urgency_indicator(diagnosis.urgency_level)
        notification.append(f"🔧 NEW LEAD {urgency_indicator}")

        if lead_id:
            notification.append(f"Lead ID: {lead_id}")

        notification.append(
            f"Timestamp: {datetime.now(timezone.utc).strftime(self.timestamp_format)}"
        )
        notification.append("")

        # Customer info (essential details only)
        notification.append("👤 CUSTOMER:")
        notification.append(f"Name: {contact.name}")
        notification.append(f"Phone: {self._format_phone_number(contact.phone)}")
        if contact.address:
            notification.append(f"Location: {contact.address}")
        notification.append("")

        # Problem summary
        notification.append("🚨 PROBLEM:")
        notification.append(f"Issue: {diagnosis.primary_issue}")
        notification.append(f"Urgency: {self._format_urgency(diagnosis.urgency_level)}")
        notification.append(f"Complexity: {diagnosis.estimated_complexity}")

        if diagnosis.recommended_services:
            services_str = ", ".join(
                diagnosis.recommended_services[:3]
            )  # Limit to top 3
            if len(diagnosis.recommended_services) > 3:
                services_str += f" (and {len(diagnosis.recommended_services) - 3} more)"
            notification.append(f"Services needed: {services_str}")

        if diagnosis.timeline_estimate:
            notification.append(f"Timeline: {diagnosis.timeline_estimate}")
        notification.append("")

        # Photos available indicator
        if photo_analysis and photo_analysis.photo_count > 0:
            notification.append(
                f"📷 {photo_analysis.photo_count} photos available for review"
            )
            if photo_analysis.damage_severity:
                notification.append(f"Damage level: {photo_analysis.damage_severity}")
            notification.append("")

        # Contact preferences
        if contact.preferred_contact_method or contact.preferred_contact_times:
            notification.append("📞 CONTACT PREFERENCES:")
            if contact.preferred_contact_method:
                notification.append(f"Method: {contact.preferred_contact_method}")
            if contact.preferred_contact_times:
                times_str = ", ".join(contact.preferred_contact_times)
                notification.append(f"Times: {times_str}")
            notification.append("")

        notification.append("Click to view full lead details and accept job.")

        return "\n".join(notification)

    def generate_customer_handoff(
        self,
        contact: ContactInfo,
        diagnosis: ProblemDiagnosis,
        contractor_info: Optional[Dict[str, str]] = None,
        estimated_arrival: Optional[str] = None,
    ) -> str:
        """
        Generate customer handoff message.

        Args:
            contact: Customer contact information
            diagnosis: Problem diagnosis
            contractor_info: Optional contractor details
            estimated_arrival: Optional arrival estimate

        Returns:
            Formatted customer handoff message
        """
        handoff = []

        handoff.append(f"Hi {contact.name.split()[0]},")
        handoff.append("")
        handoff.append(
            "Great news! We've reviewed your service request and have the perfect contractor for your project."
        )
        handoff.append("")

        # Problem acknowledgment
        handoff.append("📋 YOUR REQUEST:")
        handoff.append(f"Issue: {diagnosis.primary_issue}")

        if diagnosis.affected_areas:
            areas_str = ", ".join(diagnosis.affected_areas)
            handoff.append(f"Areas: {areas_str}")

        if diagnosis.recommended_services:
            handoff.append("Services to be provided:")
            for service in diagnosis.recommended_services[:3]:  # Top 3 services
                handoff.append(f"• {service}")
        handoff.append("")

        # Contractor info
        if contractor_info:
            handoff.append("👨‍🔧 YOUR CONTRACTOR:")
            handoff.append(
                f"Company: {contractor_info.get('company_name', 'Professional Service Provider')}"
            )
            if "rating" in contractor_info:
                handoff.append(f"Rating: {contractor_info['rating']} ⭐")
            if "years_experience" in contractor_info:
                handoff.append(
                    f"Experience: {contractor_info['years_experience']} years"
                )
            handoff.append("")

        # Next steps
        handoff.append("🕐 NEXT STEPS:")
        if estimated_arrival:
            handoff.append(f"• Contractor will arrive: {estimated_arrival}")
        else:
            handoff.append("• Contractor will contact you within 2 hours to schedule")

        handoff.append("• They will provide a detailed assessment and quote")
        handoff.append("• All work comes with our satisfaction guarantee")
        handoff.append("")

        # Urgency handling
        if diagnosis.urgency_level in [UrgencyLevel.HIGH, UrgencyLevel.EMERGENCY]:
            handoff.append("⚡ PRIORITY SERVICE:")
            handoff.append(
                "We've marked this as priority due to the urgent nature of your request."
            )
            handoff.append("")

        # Contact info
        handoff.append("📞 STAY IN TOUCH:")
        handoff.append(f"Your phone: {self._format_phone_number(contact.phone)}")
        if contact.preferred_contact_method:
            handoff.append(f"Preferred contact: {contact.preferred_contact_method}")
        handoff.append("")
        handoff.append("Questions? Reply to this message or call our support line.")
        handoff.append("")
        handoff.append("Thank you for choosing our service!")

        return "\n".join(handoff)

    def generate_full_summary(
        self,
        contact: ContactInfo,
        diagnosis: ProblemDiagnosis,
        responses: Optional[Dict[str, Any]] = None,
        photo_analysis: Optional[PhotoAnalysis] = None,
        conversation: Optional[ConversationSummary] = None,
        lead_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> str:
        """
        Generate comprehensive lead summary.

        Args:
            contact: Customer contact information
            diagnosis: Problem diagnosis
            responses: Customer qualification responses
            photo_analysis: Photo analysis results
            conversation: Conversation summary
            lead_id: Lead identifier
            created_at: Lead creation timestamp

        Returns:
            Complete formatted lead summary
        """
        summary_parts = []

        # Header
        summary_parts.append("=" * 60)
        summary_parts.append("COMPREHENSIVE LEAD SUMMARY")
        summary_parts.append("=" * 60)

        if lead_id:
            summary_parts.append(f"Lead ID: {lead_id}")

        if created_at:
            timestamp = created_at.strftime(self.timestamp_format)
            summary_parts.append(f"Created: {timestamp}")

        summary_parts.append("")

        # Add each section
        sections = [
            self.format_contact_details(contact),
            self.format_problem_diagnosis(diagnosis),
        ]

        if responses:
            sections.append(self.format_customer_responses(responses))

        if photo_analysis:
            sections.append(self.format_photo_analysis(photo_analysis))

        if conversation:
            sections.append(self.format_conversation_summary(conversation))

        # Join all sections
        summary_parts.extend(sections)
        summary_parts.append("")
        summary_parts.append("=" * 60)
        summary_parts.append(
            f"Summary generated: {datetime.now(timezone.utc).strftime(self.timestamp_format)}"
        )

        return "\n\n".join(summary_parts)

    def generate_brief_summary(
        self, contact: ContactInfo, diagnosis: ProblemDiagnosis, photo_count: int = 0
    ) -> str:
        """
        Generate brief lead summary for quick review.

        Args:
            contact: Customer contact information
            diagnosis: Problem diagnosis
            photo_count: Number of photos provided

        Returns:
            Brief formatted summary
        """
        brief = []

        urgency_indicator = self._get_urgency_indicator(diagnosis.urgency_level)
        brief.append(f"LEAD SUMMARY {urgency_indicator}")
        brief.append(
            f"Customer: {contact.name} | {self._format_phone_number(contact.phone)}"
        )
        brief.append(f"Issue: {diagnosis.primary_issue}")
        brief.append(f"Urgency: {diagnosis.urgency_level.value.title()}")

        if photo_count > 0:
            brief.append(f"Photos: {photo_count} provided")

        if diagnosis.recommended_services:
            services_str = ", ".join(diagnosis.recommended_services[:2])
            if len(diagnosis.recommended_services) > 2:
                services_str += "..."
            brief.append(f"Services: {services_str}")

        return " | ".join(brief)

    def _categorize_responses(
        self, responses: Dict[str, Any]
    ) -> Dict[str, List[Tuple[str, Any]]]:
        """Categorize customer responses by topic."""
        categories = {
            "contact_info": [],
            "problem_details": [],
            "property_info": [],
            "preferences": [],
            "other": [],
        }

        contact_keywords = ["name", "phone", "email", "address", "contact"]
        problem_keywords = [
            "issue",
            "problem",
            "damage",
            "repair",
            "broken",
            "leak",
            "emergency",
        ]
        property_keywords = ["property", "home", "building", "room", "area", "location"]
        preference_keywords = ["prefer", "schedule", "time", "budget", "timeline"]

        for question, answer in responses.items():
            if question.lower() == "timestamp":
                continue

            question_lower = question.lower()
            categorized = False

            for keyword in contact_keywords:
                if keyword in question_lower:
                    categories["contact_info"].append((question, answer))
                    categorized = True
                    break

            if not categorized:
                for keyword in problem_keywords:
                    if keyword in question_lower:
                        categories["problem_details"].append((question, answer))
                        categorized = True
                        break

            if not categorized:
                for keyword in property_keywords:
                    if keyword in question_lower:
                        categories["property_info"].append((question, answer))
                        categorized = True
                        break

            if not categorized:
                for keyword in preference_keywords:
                    if keyword in question_lower:
                        categories["preferences"].append((question, answer))
                        categorized = True
                        break

            if not categorized:
                categories["other"].append((question, answer))

        return categories

    def _format_response_value(self, value: Any) -> str:
        """Format a response value for display."""
        if value is None:
            return "Not provided"
        elif isinstance(value, bool):
            return "Yes" if value else "No"
        elif isinstance(value, list):
            return ", ".join(str(item) for item in value)
        elif isinstance(value, dict):
            return json.dumps(value, indent=2)
        else:
            return str(value)

    def _format_phone_number(self, phone: str) -> str:
        """Format phone number for display."""
        if not phone:
            return "Not provided"

        # Remove all non-digit characters
        digits = re.sub(r"\D", "", phone)

        # Format as (XXX) XXX-XXXX if 10 digits, +1 (XXX) XXX-XXXX if 11
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == "1":
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return phone  # Return as-is if can't format

    def _format_urgency(self, urgency: UrgencyLevel) -> str:
        """Format urgency level with appropriate indicators."""
        urgency_map = {
            UrgencyLevel.LOW: "🟢 Low",
            UrgencyLevel.MEDIUM: "🟡 Medium",
            UrgencyLevel.HIGH: "🟠 High",
            UrgencyLevel.EMERGENCY: "🔴 EMERGENCY",
        }
        return urgency_map.get(urgency, urgency.value.title())

    def _get_urgency_indicator(self, urgency: UrgencyLevel) -> str:
        """Get urgency indicator emoji."""
        indicators = {
            UrgencyLevel.LOW: "",
            UrgencyLevel.MEDIUM: "⚠️",
            UrgencyLevel.HIGH: "🚨",
            UrgencyLevel.EMERGENCY: "🚨🚨",
        }
        return indicators.get(urgency, "")

    def _format_timestamp(self, timestamp: Any) -> str:
        """Format timestamp for display."""
        if isinstance(timestamp, datetime):
            return timestamp.strftime(self.timestamp_format)
        elif isinstance(timestamp, str):
            try:
                # Try to parse ISO format
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                return dt.strftime(self.timestamp_format)
            except ValueError:
                return timestamp
        else:
            return str(timestamp)


# Utility functions for common formatting tasks


def create_lead_summary(
    customer_data: Dict[str, Any],
    summary_type: SummaryType = SummaryType.FULL_SUMMARY,
    **kwargs,
) -> str:
    """
    Create a lead summary from customer data dictionary.

    Args:
        customer_data: Dictionary containing all customer and lead data
        summary_type: Type of summary to generate
        **kwargs: Additional parameters for specific summary types

    Returns:
        Formatted summary string
    """
    formatter = LeadSummaryFormatter()

    # Extract data components
    contact = ContactInfo(
        name=customer_data.get("name", "Unknown"),
        phone=customer_data.get("phone", ""),
        email=customer_data.get("email"),
        address=customer_data.get("address"),
        preferred_contact_method=customer_data.get("preferred_contact_method"),
        preferred_contact_times=customer_data.get("preferred_contact_times", []),
        alternate_phone=customer_data.get("alternate_phone"),
    )

    diagnosis = ProblemDiagnosis(
        primary_issue=customer_data.get("primary_issue", "Service request"),
        secondary_issues=customer_data.get("secondary_issues", []),
        affected_areas=customer_data.get("affected_areas", []),
        urgency_level=UrgencyLevel(customer_data.get("urgency_level", "medium")),
        estimated_complexity=customer_data.get("estimated_complexity", "Standard"),
        recommended_services=customer_data.get("recommended_services", []),
        timeline_estimate=customer_data.get("timeline_estimate"),
    )

    # Optional components
    photo_analysis = None
    if customer_data.get("photo_analysis"):
        photo_data = customer_data["photo_analysis"]
        photo_analysis = PhotoAnalysis(
            photo_count=photo_data.get("photo_count", 0),
            analysis_results=photo_data.get("analysis_results", []),
            damage_severity=photo_data.get("damage_severity"),
            estimated_repair_type=photo_data.get("estimated_repair_type"),
            confidence_score=photo_data.get("confidence_score"),
            key_findings=photo_data.get("key_findings", []),
        )

    conversation = None
    if customer_data.get("conversation_summary"):
        conv_data = customer_data["conversation_summary"]
        conversation = ConversationSummary(
            total_messages=conv_data.get("total_messages", 0),
            conversation_duration=conv_data.get("conversation_duration"),
            key_topics=conv_data.get("key_topics", []),
            customer_sentiment=conv_data.get("customer_sentiment"),
            main_concerns=conv_data.get("main_concerns", []),
            follow_up_requests=conv_data.get("follow_up_requests", []),
        )

    # Generate appropriate summary type
    if summary_type == SummaryType.CONTRACTOR_NOTIFICATION:
        return formatter.generate_contractor_notification(
            contact=contact,
            diagnosis=diagnosis,
            photo_analysis=photo_analysis,
            responses=customer_data.get("responses"),
            lead_id=customer_data.get("lead_id"),
        )

    elif summary_type == SummaryType.CUSTOMER_HANDOFF:
        return formatter.generate_customer_handoff(
            contact=contact,
            diagnosis=diagnosis,
            contractor_info=kwargs.get("contractor_info"),
            estimated_arrival=kwargs.get("estimated_arrival"),
        )

    elif summary_type == SummaryType.BRIEF_SUMMARY:
        return formatter.generate_brief_summary(
            contact=contact,
            diagnosis=diagnosis,
            photo_count=photo_analysis.photo_count if photo_analysis else 0,
        )

    else:  # FULL_SUMMARY
        return formatter.generate_full_summary(
            contact=contact,
            diagnosis=diagnosis,
            responses=customer_data.get("responses"),
            photo_analysis=photo_analysis,
            conversation=conversation,
            lead_id=customer_data.get("lead_id"),
            created_at=customer_data.get("created_at"),
        )


def format_multiple_leads(
    leads_data: List[Dict[str, Any]],
    summary_type: SummaryType = SummaryType.BRIEF_SUMMARY,
) -> str:
    """
    Format multiple leads into a consolidated summary.

    Args:
        leads_data: List of lead data dictionaries
        summary_type: Type of summary for each lead

    Returns:
        Consolidated summary string
    """
    if not leads_data:
        return "No leads to display."

    summaries = []
    summaries.append(f"=== LEADS SUMMARY ({len(leads_data)} leads) ===")
    summaries.append(
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}"
    )
    summaries.append("")

    for i, lead_data in enumerate(leads_data, 1):
        summaries.append(f"LEAD {i}:")
        lead_summary = create_lead_summary(lead_data, summary_type)
        summaries.append(lead_summary)
        summaries.append("-" * 40)

    return "\n".join(summaries)
