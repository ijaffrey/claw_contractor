"""
Lead qualification detection service for Claw Contractor.

This module provides functionality to determine if leads are qualified
based on required information and completeness criteria.
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class QualificationStatus(Enum):
    """Lead qualification status enumeration."""

    QUALIFIED = "qualified"
    PARTIALLY_QUALIFIED = "partially_qualified"
    UNQUALIFIED = "unqualified"


class RequirementType(Enum):
    """Types of requirements for lead qualification."""

    CONTACT_INFO = "contact_info"
    PROJECT_DETAILS = "project_details"
    PHOTOS = "photos"
    RESPONSES = "responses"
    BUDGET = "budget"
    TIMELINE = "timeline"


@dataclass
class QualificationResult:
    """Result of lead qualification analysis."""

    status: QualificationStatus
    completeness_score: float
    missing_requirements: List[str]
    satisfied_requirements: List[str]
    recommendations: List[str]


@dataclass
class RequirementConfig:
    """Configuration for qualification requirements."""

    min_photos: int = 1
    required_contact_fields: List[str] = None
    required_project_fields: List[str] = None
    required_response_questions: List[str] = None
    min_completeness_score: float = 0.7
    budget_required: bool = False
    timeline_required: bool = False

    def __post_init__(self):
        if self.required_contact_fields is None:
            self.required_contact_fields = ["name", "email", "phone"]
        if self.required_project_fields is None:
            self.required_project_fields = ["project_type", "description", "location"]
        if self.required_response_questions is None:
            self.required_response_questions = []


class LeadQualificationDetector:
    """
    Service class for detecting and analyzing lead qualification status.

    This class evaluates leads based on completeness of contact information,
    project details, photo submissions, and required responses.
    """

    def __init__(self, config: Optional[RequirementConfig] = None):
        """
        Initialize the lead qualification detector.

        Args:
            config: Configuration for qualification requirements
        """
        self.config = config or RequirementConfig()
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def is_lead_qualified(self, lead: Dict[str, Any]) -> bool:
        """
        Determine if a lead is qualified based on all requirements.

        Args:
            lead: Lead data dictionary

        Returns:
            True if lead meets qualification criteria, False otherwise
        """
        try:
            qualification_result = self._analyze_qualification(lead)
            return qualification_result.status == QualificationStatus.QUALIFIED
        except Exception as e:
            self.logger.error(f"Error checking lead qualification: {str(e)}")
            return False

    def get_qualification_completeness(self, lead: Dict[str, Any]) -> float:
        """
        Calculate the completeness score of a lead (0.0 to 1.0).

        Args:
            lead: Lead data dictionary

        Returns:
            Completeness score as a float between 0.0 and 1.0
        """
        try:
            total_requirements = 0
            satisfied_requirements = 0

            # Check contact information completeness
            contact_score, contact_total = self._check_contact_completeness(lead)
            satisfied_requirements += contact_score
            total_requirements += contact_total

            # Check project details completeness
            project_score, project_total = self._check_project_completeness(lead)
            satisfied_requirements += project_score
            total_requirements += project_total

            # Check photo submissions
            photo_score, photo_total = self._check_photo_completeness(lead)
            satisfied_requirements += photo_score
            total_requirements += photo_total

            # Check required responses
            response_score, response_total = self._check_response_completeness(lead)
            satisfied_requirements += response_score
            total_requirements += response_total

            # Check optional requirements
            if self.config.budget_required:
                budget_score, budget_total = self._check_budget_completeness(lead)
                satisfied_requirements += budget_score
                total_requirements += budget_total

            if self.config.timeline_required:
                timeline_score, timeline_total = self._check_timeline_completeness(lead)
                satisfied_requirements += timeline_score
                total_requirements += timeline_total

            if total_requirements == 0:
                return 0.0

            return satisfied_requirements / total_requirements

        except Exception as e:
            self.logger.error(f"Error calculating qualification completeness: {str(e)}")
            return 0.0

    def validate_required_data(self, lead: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that all required data is present in the lead.

        Args:
            lead: Lead data dictionary

        Returns:
            Tuple of (is_valid, list_of_missing_requirements)
        """
        try:
            qualification_result = self._analyze_qualification(lead)
            is_valid = len(qualification_result.missing_requirements) == 0
            return is_valid, qualification_result.missing_requirements
        except Exception as e:
            self.logger.error(f"Error validating required data: {str(e)}")
            return False, [f"Validation error: {str(e)}"]

    def get_detailed_qualification_analysis(
        self, lead: Dict[str, Any]
    ) -> QualificationResult:
        """
        Get detailed qualification analysis including recommendations.

        Args:
            lead: Lead data dictionary

        Returns:
            QualificationResult with detailed analysis
        """
        try:
            return self._analyze_qualification(lead)
        except Exception as e:
            self.logger.error(
                f"Error performing detailed qualification analysis: {str(e)}"
            )
            return QualificationResult(
                status=QualificationStatus.UNQUALIFIED,
                completeness_score=0.0,
                missing_requirements=[f"Analysis error: {str(e)}"],
                satisfied_requirements=[],
                recommendations=["Please contact support for assistance"],
            )

    def _analyze_qualification(self, lead: Dict[str, Any]) -> QualificationResult:
        """
        Perform comprehensive qualification analysis.

        Args:
            lead: Lead data dictionary

        Returns:
            QualificationResult with analysis details
        """
        missing_requirements = []
        satisfied_requirements = []
        recommendations = []

        # Analyze each requirement category
        self._analyze_contact_requirements(
            lead, missing_requirements, satisfied_requirements
        )
        self._analyze_project_requirements(
            lead, missing_requirements, satisfied_requirements
        )
        self._analyze_photo_requirements(
            lead, missing_requirements, satisfied_requirements
        )
        self._analyze_response_requirements(
            lead, missing_requirements, satisfied_requirements
        )

        if self.config.budget_required:
            self._analyze_budget_requirements(
                lead, missing_requirements, satisfied_requirements
            )

        if self.config.timeline_required:
            self._analyze_timeline_requirements(
                lead, missing_requirements, satisfied_requirements
            )

        # Calculate completeness score
        completeness_score = self.get_qualification_completeness(lead)

        # Determine qualification status
        if len(missing_requirements) == 0:
            status = QualificationStatus.QUALIFIED
        elif completeness_score >= self.config.min_completeness_score:
            status = QualificationStatus.PARTIALLY_QUALIFIED
        else:
            status = QualificationStatus.UNQUALIFIED

        # Generate recommendations
        recommendations = self._generate_recommendations(
            missing_requirements, completeness_score
        )

        return QualificationResult(
            status=status,
            completeness_score=completeness_score,
            missing_requirements=missing_requirements,
            satisfied_requirements=satisfied_requirements,
            recommendations=recommendations,
        )

    def _analyze_contact_requirements(
        self, lead: Dict[str, Any], missing: List[str], satisfied: List[str]
    ) -> None:
        """Analyze contact information requirements."""
        contact_info = lead.get("contact_info", {})

        for field in self.config.required_contact_fields:
            value = contact_info.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                missing.append(f"Contact {field}")
            else:
                satisfied.append(f"Contact {field}")

        # Validate email format if present
        email = contact_info.get("email")
        if email and not self._is_valid_email(email):
            missing.append("Valid email format")
        elif email:
            satisfied.append("Valid email format")

        # Validate phone format if present
        phone = contact_info.get("phone")
        if phone and not self._is_valid_phone(phone):
            missing.append("Valid phone format")
        elif phone:
            satisfied.append("Valid phone format")

    def _analyze_project_requirements(
        self, lead: Dict[str, Any], missing: List[str], satisfied: List[str]
    ) -> None:
        """Analyze project details requirements."""
        project_details = lead.get("project_details", {})

        for field in self.config.required_project_fields:
            value = project_details.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                missing.append(f"Project {field}")
            else:
                satisfied.append(f"Project {field}")

        # Check description length
        description = project_details.get("description", "")
        if isinstance(description, str) and len(description.strip()) < 20:
            missing.append("Detailed project description (minimum 20 characters)")
        elif description:
            satisfied.append("Detailed project description")

    def _analyze_photo_requirements(
        self, lead: Dict[str, Any], missing: List[str], satisfied: List[str]
    ) -> None:
        """Analyze photo submission requirements."""
        photos = lead.get("photos", [])

        if len(photos) < self.config.min_photos:
            missing.append(f"At least {self.config.min_photos} photo(s)")
        else:
            satisfied.append(f"{len(photos)} photo(s) submitted")

        # Check photo quality indicators
        valid_photos = 0
        for photo in photos:
            if self._is_valid_photo(photo):
                valid_photos += 1

        if valid_photos < self.config.min_photos:
            missing.append("Valid photo submissions")
        elif valid_photos > 0:
            satisfied.append(f"{valid_photos} valid photo(s)")

    def _analyze_response_requirements(
        self, lead: Dict[str, Any], missing: List[str], satisfied: List[str]
    ) -> None:
        """Analyze required response requirements."""
        responses = lead.get("responses", {})

        for question in self.config.required_response_questions:
            response = responses.get(question)
            if not response or (isinstance(response, str) and not response.strip()):
                missing.append(f"Response to: {question}")
            else:
                satisfied.append(f"Response to: {question}")

    def _analyze_budget_requirements(
        self, lead: Dict[str, Any], missing: List[str], satisfied: List[str]
    ) -> None:
        """Analyze budget requirements."""
        budget = lead.get("budget")
        if not budget:
            missing.append("Budget information")
        else:
            satisfied.append("Budget information")

    def _analyze_timeline_requirements(
        self, lead: Dict[str, Any], missing: List[str], satisfied: List[str]
    ) -> None:
        """Analyze timeline requirements."""
        timeline = lead.get("timeline")
        if not timeline:
            missing.append("Project timeline")
        else:
            satisfied.append("Project timeline")

    def _check_contact_completeness(self, lead: Dict[str, Any]) -> Tuple[int, int]:
        """Check contact information completeness."""
        contact_info = lead.get("contact_info", {})
        satisfied = 0
        total = len(self.config.required_contact_fields)

        for field in self.config.required_contact_fields:
            value = contact_info.get(field)
            if value and (not isinstance(value, str) or value.strip()):
                satisfied += 1

        return satisfied, total

    def _check_project_completeness(self, lead: Dict[str, Any]) -> Tuple[int, int]:
        """Check project details completeness."""
        project_details = lead.get("project_details", {})
        satisfied = 0
        total = len(self.config.required_project_fields)

        for field in self.config.required_project_fields:
            value = project_details.get(field)
            if value and (not isinstance(value, str) or value.strip()):
                satisfied += 1

        return satisfied, total

    def _check_photo_completeness(self, lead: Dict[str, Any]) -> Tuple[int, int]:
        """Check photo submission completeness."""
        photos = lead.get("photos", [])
        valid_photos = sum(1 for photo in photos if self._is_valid_photo(photo))

        satisfied = 1 if valid_photos >= self.config.min_photos else 0
        total = 1

        return satisfied, total

    def _check_response_completeness(self, lead: Dict[str, Any]) -> Tuple[int, int]:
        """Check required response completeness."""
        responses = lead.get("responses", {})
        satisfied = 0
        total = len(self.config.required_response_questions)

        for question in self.config.required_response_questions:
            response = responses.get(question)
            if response and (not isinstance(response, str) or response.strip()):
                satisfied += 1

        return satisfied, total

    def _check_budget_completeness(self, lead: Dict[str, Any]) -> Tuple[int, int]:
        """Check budget completeness."""
        budget = lead.get("budget")
        satisfied = 1 if budget else 0
        total = 1
        return satisfied, total

    def _check_timeline_completeness(self, lead: Dict[str, Any]) -> Tuple[int, int]:
        """Check timeline completeness."""
        timeline = lead.get("timeline")
        satisfied = 1 if timeline else 0
        total = 1
        return satisfied, total

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email.strip()))

    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone format."""
        import re

        # Remove all non-digit characters
        digits = re.sub(r"\D", "", phone)
        # Check if it's a valid US phone number (10 or 11 digits)
        return len(digits) in [10, 11]

    def _is_valid_photo(self, photo: Dict[str, Any]) -> bool:
        """Check if photo submission is valid."""
        if not isinstance(photo, dict):
            return False

        # Check for required photo fields
        required_fields = ["url", "filename"]
        for field in required_fields:
            if not photo.get(field):
                return False

        # Check file extension
        filename = photo.get("filename", "").lower()
        valid_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
        if not any(filename.endswith(ext) for ext in valid_extensions):
            return False

        return True

    def _generate_recommendations(
        self, missing_requirements: List[str], completeness_score: float
    ) -> List[str]:
        """Generate recommendations based on missing requirements."""
        recommendations = []

        if not missing_requirements:
            recommendations.append("Lead is fully qualified and ready for follow-up")
            return recommendations

        # Priority recommendations based on missing items
        contact_missing = any("Contact" in req for req in missing_requirements)
        project_missing = any("Project" in req for req in missing_requirements)
        photo_missing = any("photo" in req.lower() for req in missing_requirements)

        if contact_missing:
            recommendations.append(
                "Priority: Complete contact information to enable communication"
            )

        if project_missing:
            recommendations.append(
                "Important: Provide detailed project information for accurate estimation"
            )

        if photo_missing:
            recommendations.append(
                "Helpful: Add project photos to improve assessment accuracy"
            )

        # Score-based recommendations
        if completeness_score < 0.3:
            recommendations.append("Lead requires significant additional information")
        elif completeness_score < 0.7:
            recommendations.append(
                "Lead is partially complete - focus on missing critical items"
            )
        else:
            recommendations.append("Lead is mostly complete - minor items needed")

        return recommendations
