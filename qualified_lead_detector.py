"""
Qualified Lead Detector Module

This module analyzes conversation state and lead data to determine if a lead is fully qualified
and ready for contractor handoff.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class QualificationStatus(Enum):
    """Lead qualification status enumeration."""
    NOT_QUALIFIED = "not_qualified"
    PARTIALLY_QUALIFIED = "partially_qualified"
    FULLY_QUALIFIED = "fully_qualified"
    QUALIFIED_PENDING_REVIEW = "qualified_pending_review"
    DISQUALIFIED = "disqualified"


class QualificationCriteria(Enum):
    """Required qualification criteria."""
    CONTACT_INFO = "contact_info"
    PROBLEM_DESCRIPTION = "problem_description"
    LOCATION_INFO = "location_info"
    PHOTOS_UPLOADED = "photos_uploaded"
    URGENCY_ASSESSED = "urgency_assessed"
    BUDGET_DISCUSSED = "budget_discussed"
    AVAILABILITY_CONFIRMED = "availability_confirmed"
    DIAGNOSIS_COMPLETE = "diagnosis_complete"


@dataclass
class QualificationScore:
    """Qualification scoring data structure."""
    total_score: float = 0.0
    max_possible_score: float = 0.0
    criteria_scores: Dict[str, float] = field(default_factory=dict)
    completion_percentage: float = 0.0
    missing_criteria: List[str] = field(default_factory=list)
    
    @property
    def percentage(self) -> float:
        """Calculate completion percentage."""
        if self.max_possible_score == 0:
            return 0.0
        return (self.total_score / self.max_possible_score) * 100


@dataclass
class QualificationResult:
    """Result of lead qualification analysis."""
    status: QualificationStatus
    score: QualificationScore
    is_ready_for_handoff: bool
    qualification_timestamp: datetime
    missing_requirements: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    contractor_notes: str = ""
    estimated_completion_time: Optional[datetime] = None


class QualifiedLeadDetector:
    """Main class for analyzing lead qualification status."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the qualified lead detector.
        
        Args:
            config: Configuration dictionary with scoring weights and thresholds
        """
        self.config = config or self._get_default_config()
        self.qualification_weights = self.config.get('qualification_weights', {})
        self.minimum_score_threshold = self.config.get('minimum_score_threshold', 75.0)
        self.handoff_threshold = self.config.get('handoff_threshold', 85.0)
        self.required_photos_count = self.config.get('required_photos_count', 2)
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for qualification scoring."""
        return {
            'qualification_weights': {
                QualificationCriteria.CONTACT_INFO.value: 15.0,
                QualificationCriteria.PROBLEM_DESCRIPTION.value: 20.0,
                QualificationCriteria.LOCATION_INFO.value: 10.0,
                QualificationCriteria.PHOTOS_UPLOADED.value: 15.0,
                QualificationCriteria.URGENCY_ASSESSED.value: 10.0,
                QualificationCriteria.BUDGET_DISCUSSED.value: 10.0,
                QualificationCriteria.AVAILABILITY_CONFIRMED.value: 10.0,
                QualificationCriteria.DIAGNOSIS_COMPLETE.value: 10.0,
            },
            'minimum_score_threshold': 75.0,
            'handoff_threshold': 85.0,
            'required_photos_count': 2,
            'max_qualification_time_hours': 24,
            'auto_disqualify_keywords': ['spam', 'test', 'fake'],
        }
    
    def analyze_lead_qualification(
        self, 
        conversation_state: Dict[str, Any], 
        lead_data: Dict[str, Any]
    ) -> QualificationResult:
        """
        Analyze lead qualification status based on conversation and lead data.
        
        Args:
            conversation_state: Current conversation state data
            lead_data: Lead information and collected data
            
        Returns:
            QualificationResult with status and scoring details
        """
        try:
            # Check for immediate disqualification
            if self._is_disqualified(conversation_state, lead_data):
                return self._create_disqualified_result()
            
            # Calculate qualification score
            score = self._calculate_qualification_score(conversation_state, lead_data)
            
            # Determine qualification status
            status = self._determine_qualification_status(score)
            
            # Check readiness for contractor handoff
            is_ready = self._is_ready_for_handoff(score, conversation_state, lead_data)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(score, conversation_state, lead_data)
            
            # Create contractor notes
            contractor_notes = self._generate_contractor_notes(conversation_state, lead_data)
            
            # Estimate completion time if not fully qualified
            estimated_completion = None
            if status != QualificationStatus.FULLY_QUALIFIED:
                estimated_completion = self._estimate_completion_time(score, conversation_state)
            
            return QualificationResult(
                status=status,
                score=score,
                is_ready_for_handoff=is_ready,
                qualification_timestamp=datetime.now(),
                missing_requirements=score.missing_criteria,
                recommendations=recommendations,
                contractor_notes=contractor_notes,
                estimated_completion_time=estimated_completion
            )
            
        except Exception as e:
            logger.error(f"Error analyzing lead qualification: {e}")
            return self._create_error_result()
    
    def check_required_data_collected(
        self, 
        conversation_state: Dict[str, Any], 
        lead_data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Check if all required qualification data has been collected.
        
        Args:
            conversation_state: Current conversation state
            lead_data: Lead data collected so far
            
        Returns:
            Tuple of (all_collected, missing_items)
        """
        missing_items = []
        
        try:
            # Check contact information
            if not self._has_contact_info(lead_data):
                missing_items.append("Contact information (phone or email)")
            
            # Check problem description
            if not self._has_problem_description(conversation_state, lead_data):
                missing_items.append("Detailed problem description")
            
            # Check location information
            if not self._has_location_info(lead_data):
                missing_items.append("Service location details")
            
            # Check photos
            if not self._has_required_photos(lead_data):
                missing_items.append(f"At least {self.required_photos_count} photos")
            
            # Check urgency assessment
            if not self._has_urgency_assessment(conversation_state, lead_data):
                missing_items.append("Urgency level assessment")
            
            # Check budget discussion
            if not self._has_budget_discussion(conversation_state, lead_data):
                missing_items.append("Budget or cost expectations")
            
            # Check availability
            if not self._has_availability_info(conversation_state, lead_data):
                missing_items.append("Customer availability windows")
            
            # Check diagnosis completion
            if not self._has_diagnosis_complete(conversation_state, lead_data):
                missing_items.append("Complete problem diagnosis")
            
            all_collected = len(missing_items) == 0
            return all_collected, missing_items
            
        except Exception as e:
            logger.error(f"Error checking required data: {e}")
            return False, ["Error checking requirements"]
    
    def validate_lead_completeness(self, lead_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that lead data is complete and properly formatted.
        
        Args:
            lead_data: Lead data to validate
            
        Returns:
            Tuple of (is_valid, validation_errors)
        """
        validation_errors = []
        
        try:
            # Validate contact info format
            contact_errors = self._validate_contact_info(lead_data)
            validation_errors.extend(contact_errors)
            
            # Validate location data
            location_errors = self._validate_location_data(lead_data)
            validation_errors.extend(location_errors)
            
            # Validate photo data
            photo_errors = self._validate_photo_data(lead_data)
            validation_errors.extend(photo_errors)
            
            # Validate problem description quality
            description_errors = self._validate_problem_description(lead_data)
            validation_errors.extend(description_errors)
            
            # Validate urgency and priority data
            urgency_errors = self._validate_urgency_data(lead_data)
            validation_errors.extend(urgency_errors)
            
            is_valid = len(validation_errors) == 0
            return is_valid, validation_errors
            
        except Exception as e:
            logger.error(f"Error validating lead completeness: {e}")
            return False, [f"Validation error: {str(e)}"]
    
    def get_qualification_progress(
        self, 
        conversation_state: Dict[str, Any], 
        lead_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get detailed qualification progress information.
        
        Args:
            conversation_state: Current conversation state
            lead_data: Lead data collected
            
        Returns:
            Dictionary with progress details
        """
        try:
            score = self._calculate_qualification_score(conversation_state, lead_data)
            all_collected, missing_items = self.check_required_data_collected(
                conversation_state, lead_data
            )
            
            progress = {
                'overall_progress': score.completion_percentage,
                'score_breakdown': score.criteria_scores,
                'completed_criteria': [
                    criteria for criteria in QualificationCriteria 
                    if criteria.value not in score.missing_criteria
                ],
                'missing_criteria': score.missing_criteria,
                'missing_items': missing_items,
                'next_steps': self._get_next_steps(score, conversation_state, lead_data),
                'estimated_time_to_complete': self._estimate_completion_time(
                    score, conversation_state
                ),
                'is_on_track': self._is_qualification_on_track(conversation_state),
            }
            
            return progress
            
        except Exception as e:
            logger.error(f"Error getting qualification progress: {e}")
            return {'error': str(e)}
    
    def _calculate_qualification_score(
        self, 
        conversation_state: Dict[str, Any], 
        lead_data: Dict[str, Any]
    ) -> QualificationScore:
        """Calculate detailed qualification score."""
        score = QualificationScore()
        max_score = sum(self.qualification_weights.values())
        score.max_possible_score = max_score
        
        # Score each qualification criteria
        for criteria in QualificationCriteria:
            weight = self.qualification_weights.get(criteria.value, 0.0)
            criteria_score = self._score_criteria(criteria, conversation_state, lead_data)
            
            score.criteria_scores[criteria.value] = criteria_score * weight
            score.total_score += criteria_score * weight
            
            if criteria_score < 1.0:
                score.missing_criteria.append(criteria.value)
        
        score.completion_percentage = score.percentage
        return score
    
    def _score_criteria(
        self, 
        criteria: QualificationCriteria, 
        conversation_state: Dict[str, Any], 
        lead_data: Dict[str, Any]
    ) -> float:
        """Score individual qualification criteria (0.0 to 1.0)."""
        try:
            if criteria == QualificationCriteria.CONTACT_INFO:
                return 1.0 if self._has_contact_info(lead_data) else 0.0
            
            elif criteria == QualificationCriteria.PROBLEM_DESCRIPTION:
                return self._score_problem_description(conversation_state, lead_data)
            
            elif criteria == QualificationCriteria.LOCATION_INFO:
                return 1.0 if self._has_location_info(lead_data) else 0.0
            
            elif criteria == QualificationCriteria.PHOTOS_UPLOADED:
                return self._score_photos(lead_data)
            
            elif criteria == QualificationCriteria.URGENCY_ASSESSED:
                return 1.0 if self._has_urgency_assessment(conversation_state, lead_data) else 0.0
            
            elif criteria == QualificationCriteria.BUDGET_DISCUSSED:
                return 1.0 if self._has_budget_discussion(conversation_state, lead_data) else 0.0
            
            elif criteria == QualificationCriteria.AVAILABILITY_CONFIRMED:
                return 1.0 if self._has_availability_info(conversation_state, lead_data) else 0.0
            
            elif criteria == QualificationCriteria.DIAGNOSIS_COMPLETE:
                return 1.0 if self._has_diagnosis_complete(conversation_state, lead_data) else 0.0
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error scoring criteria {criteria}: {e}")
            return 0.0
    
    def _has_contact_info(self, lead_data: Dict[str, Any]) -> bool:
        """Check if lead has valid contact information."""
        contact_info = lead_data.get('contact_info', {})
        has_phone = bool(contact_info.get('phone'))
        has_email = bool(contact_info.get('email'))
        has_name = bool(contact_info.get('name'))
        
        return has_name and (has_phone or has_email)
    
    def _has_problem_description(
        self, 
        conversation_state: Dict[str, Any], 
        lead_data: Dict[str, Any]
    ) -> bool:
        """Check if problem description is adequately detailed."""
        problem_desc = lead_data.get('problem_description', '')
        if not problem_desc or len(problem_desc.strip()) < 20:
            return False
        
        # Check if key problem details are captured
        messages = conversation_state.get('messages', [])
        has_detailed_discussion = any(
            len(msg.get('content', '')) > 50 
            for msg in messages 
            if msg.get('role') == 'user'
        )
        
        return has_detailed_discussion
    
    def _has_location_info(self, lead_data: Dict[str, Any]) -> bool:
        """Check if location information is complete."""
        location = lead_data.get('location', {})
        has_address = bool(location.get('address'))
        has_city = bool(location.get('city'))
        has_zip = bool(location.get('zip_code'))
        
        return has_address and has_city and has_zip
    
    def _has_required_photos(self, lead_data: Dict[str, Any]) -> bool:
        """Check if required number of photos are uploaded."""
        photos = lead_data.get('photos', [])
        return len(photos) >= self.required_photos_count
    
    def _has_urgency_assessment(
        self, 
        conversation_state: Dict[str, Any], 
        lead_data: Dict[str, Any]
    ) -> bool:
        """Check if urgency has been properly assessed."""
        urgency = lead_data.get('urgency')
        return urgency is not None and urgency in ['low', 'medium', 'high', 'emergency']
    
    def _has_budget_discussion(
        self, 
        conversation_state: Dict[str, Any], 
        lead_data: Dict[str, Any]
    ) -> bool:
        """Check if budget has been discussed."""
        budget_range = lead_data.get('budget_range')
        budget_discussed = conversation_state.get('topics_discussed', {}).get('budget', False)
        
        return budget_range is not None or budget_discussed
    
    def _has_availability_info(
        self, 
        conversation_state: Dict[str, Any], 
        lead_data: Dict[str, Any]
    ) -> bool:
        """Check if customer availability has been confirmed."""
        availability = lead_data.get('availability', {})
        return bool(availability.get('preferred_times') or availability.get('flexible'))
    
    def _has_diagnosis_complete(
        self, 
        conversation_state: Dict[str, Any], 
        lead_data: Dict[str, Any]
    ) -> bool:
        """Check if problem diagnosis is complete."""
        diagnosis = lead_data.get('diagnosis', {})
        conversation_complete = conversation_state.get('conversation_complete', False)
        
        return bool(diagnosis.get('assessment')) and conversation_complete
    
    def _score_problem_description(
        self, 
        conversation_state: Dict[str, Any], 
        lead_data: Dict[str, Any]
    ) -> float:
        """Score problem description quality (0.0 to 1.0)."""
        description = lead_data.get('problem_description', '')
        
        if not description:
            return 0.0
        
        score = 0.0
        
        # Length factor
        if len(description) >= 50:
            score += 0.4
        elif len(description) >= 20:
            score += 0.2
        
        # Detail factor - check for specific keywords
        detail_keywords = ['when', 'where', 'how', 'why', 'started', 'noticed', 'problem']
        detail_count = sum(1 for keyword in detail_keywords if keyword.lower() in description.lower())
        score += min(0.4, detail_count * 0.1)
        
        # Conversation depth factor
        messages = conversation_state.get('messages', [])
        user_messages = [msg for msg in messages if msg.get('role') == 'user']
        if len(user_messages) >= 3:
            score += 0.2
        
        return min(1.0, score)
    
    def _score_photos(self, lead_data: Dict[str, Any]) -> float:
        """Score photo uploads (0.0 to 1.0)."""
        photos = lead_data.get('photos', [])
        photo_count = len(photos)
        
        if photo_count == 0:
            return 0.0
        elif photo_count >= self.required_photos_count:
            return 1.0
        else:
            return photo_count / self.required_photos_count
    
    def _determine_qualification_status(self, score: QualificationScore) -> QualificationStatus:
        """Determine qualification status based on score."""
        percentage = score.completion_percentage
        
        if percentage >= self.handoff_threshold:
            return QualificationStatus.FULLY_QUALIFIED
        elif percentage >= self.minimum_score_threshold:
            return QualificationStatus.QUALIFIED_PENDING_REVIEW
        elif percentage >= 50.0:
            return QualificationStatus.PARTIALLY_QUALIFIED
        else:
            return QualificationStatus.NOT_QUALIFIED
    
    def _is_ready_for_handoff(
        self, 
        score: QualificationScore, 
        conversation_state: Dict[str, Any], 
        lead_data: Dict[str, Any]
    ) -> bool:
        """Check if lead is ready for contractor handoff."""
        # Must be fully qualified
        if score.completion_percentage < self.handoff_threshold:
            return False
        
        # Must pass validation
        is_valid, _ = self.validate_lead_completeness(lead_data)
        if not is_valid:
            return False
        
        # Must have all critical data
        all_collected, _ = self.check_required_data_collected(conversation_state, lead_data)
        if not all_collected:
            return False
        
        # Conversation should be in a completed state
        conversation_complete = conversation_state.get('conversation_complete', False)
        if not conversation_complete:
            return False
        
        return True
    
    def _is_disqualified(
        self, 
        conversation_state: Dict[str, Any], 
        lead_data: Dict[str, Any]
    ) -> bool:
        """Check if lead should be immediately disqualified."""
        # Check for spam/test keywords
        auto_disqualify_keywords = self.config.get('auto_disqualify_keywords', [])
        problem_desc = lead_data.get('problem_description', '').lower()
        
        for keyword in auto_disqualify_keywords:
            if keyword.lower() in problem_desc:
                return True
        
        # Check for invalid contact info patterns
        contact_info = lead_data.get('contact_info', {})
        phone = contact_info.get('phone', '')
        email = contact_info.get('email', '')
        
        if phone and (phone == '1111111111' or phone == '0000000000'):
            return True
        
        if email and ('test' in email.lower() or 'fake' in email.lower()):
            return True
        
        return False
    
    def _validate_contact_info(self, lead_data: Dict[str, Any]) -> List[str]:
        """Validate contact information format."""
        errors = []
        contact_info = lead_data.get('contact_info', {})
        
        # Validate phone number format
        phone = contact_info.get('phone')
        if phone:
            # Basic phone validation (US format)
            clean_phone = ''.join(filter(str.isdigit, phone))
            if len(clean_phone) != 10:
                errors.append("Phone number must be 10 digits")
        
        # Validate email format
        email = contact_info.get('email')
        if email:
            if '@' not in email or '.' not in email.split('@')[-1]:
                errors.append("Invalid email format")
        
        # Validate name
        name = contact_info.get('name')
        if name and len(name.strip()) < 2:
            errors.append("Name must be at least 2 characters")
        
        return errors
    
    def _validate_location_data(self, lead_data: Dict[str, Any]) -> List[str]:
        """Validate location data format."""
        errors = []
        location = lead_data.get('location', {})
        
        # Validate zip code
        zip_code = location.get('zip_code')
        if zip_code:
            clean_zip = ''.join(filter(str.isdigit, zip_code))
            if len(clean_zip) != 5:
                errors.append("ZIP code must be 5 digits")
        
        return errors
    
    def _validate_photo_data(self, lead_data: Dict[str, Any]) -> List[str]:
        """Validate photo data."""
        errors = []
        photos = lead_data.get('photos', [])
        
        for i, photo in enumerate(photos):
            if not isinstance(photo, dict):
                errors.append(f"Photo {i+1} data is malformed")
                continue
            
            if 'url' not in photo and 'data' not in photo:
                errors.append(f"Photo {i+1} missing URL or data")
            
            if 'timestamp' not in photo:
                errors.append(f"Photo {i+1} missing timestamp")
        
        return errors
    
    def _validate_problem_description(self, lead_data: Dict[str, Any]) -> List[str]:
        """Validate problem description quality."""
        errors = []
        description = lead_data.get('problem_description', '')
        
        if len(description.strip()) < 10:
            errors.append("Problem description too short")
        
        if len(description.strip()) > 2000:
            errors.append("Problem description too long")
        
        return errors
    
    def _validate_urgency_data(self, lead_data: Dict[str, Any]) -> List[str]:
        """Validate urgency and priority data."""
        errors = []
        urgency = lead_data.get('urgency')
        
        if urgency and urgency not in ['low', 'medium', 'high', 'emergency']:
            errors.append("Invalid urgency level")
        
        return errors
    
    def _generate_recommendations(
        self, 
        score: QualificationScore, 
        conversation_state: Dict[str, Any], 
        lead_data: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for improving qualification."""
        recommendations = []
        
        # Recommendations based on missing criteria
        for missing_criteria in score.missing_criteria:
            if missing_criteria == QualificationCriteria.CONTACT_INFO.value:
                recommendations.append("Collect complete contact information")
            elif missing_criteria == QualificationCriteria.PROBLEM_DESCRIPTION.value:
                recommendations.append("Ask for more detailed problem description")
            elif missing_criteria == QualificationCriteria.PHOTOS_UPLOADED.value:
                recommendations.append("Request photos of the problem area")
            elif missing_criteria == QualificationCriteria.URGENCY_ASSESSED.value:
                recommendations.append("Assess urgency level with customer")
            elif missing_criteria == QualificationCriteria.BUDGET_DISCUSSED.value:
                recommendations.append("Discuss budget expectations")
            elif missing_criteria == QualificationCriteria.AVAILABILITY_CONFIRMED.value:
                recommendations.append("Confirm customer availability windows")
        
        # General recommendations based on score
        if score.completion_percentage < 50:
            recommendations.append("Continue conversation to gather more information")
        elif score.completion_percentage < 75:
            recommendations.append("Focus on completing missing requirements")
        
        return recommendations
    
    def _generate_contractor_notes(
        self, 
        conversation_state: Dict[str, Any], 
        lead_data: Dict[str, Any]
    ) -> str:
        """Generate notes for contractor handoff."""
        notes = []
        
        # Problem summary
        problem = lead_data.get('problem_description', 'No description provided')
        notes.append(f"Problem: {problem}")
        
        # Urgency level
        urgency = lead_data.get('urgency', 'Not specified')
        notes.append(f"Urgency: {urgency}")
        
        # Customer preferences
        budget = lead_data.get('budget_range')
        if budget:
            notes.append(f"Budget range: {budget}")
        
        availability = lead_data.get('availability', {})
        if availability:
            notes.append(f"Availability: {availability}")
        
        # Special considerations from conversation
        messages = conversation_state.get('messages', [])
        user_messages = [msg.get('content', '') for msg in messages if msg.get('role') == 'user']
        
        # Look for special requests or concerns
        special_keywords = ['urgent', 'asap', 'emergency', 'water', 'leak', 'electrical']
        special_mentions = []
        
        for message in user_messages:
            for keyword in special_keywords:
                if keyword.lower() in message.lower():
                    special_mentions.append(keyword)
        
        if special_mentions:
            notes.append(f"Special considerations: {', '.join(set(special_mentions))}")
        
        return '\n'.join(notes)
    
    def _get_next_steps(
        self, 
        score: QualificationScore, 
        conversation_state: Dict[str, Any], 
        lead_data: Dict[str, Any]
    ) -> List[str]:
        """Get next steps for qualification completion."""
        next_steps = []
        
        # Prioritize missing criteria
        critical_missing = [
            criteria for criteria in score.missing_criteria
            if criteria in [
                QualificationCriteria.CONTACT_INFO.value,
                QualificationCriteria.PROBLEM_DESCRIPTION.value,
                QualificationCriteria.PHOTOS_UPLOADED.value
            ]
        ]
        
        for criteria in critical_missing:
            if criteria == QualificationCriteria.CONTACT_INFO.value:
                next_steps.append("1. Collect customer contact information")
            elif criteria == QualificationCriteria.PROBLEM_DESCRIPTION.value:
                next_steps.append("2. Get detailed problem description")
            elif criteria == QualificationCriteria.PHOTOS_UPLOADED.value:
                next_steps.append("3. Request photos of the issue")
        
        # Add other missing items
        other_missing = [
            criteria for criteria in score.missing_criteria
            if criteria not in critical_missing
        ]
        
        step_num = len(next_steps) + 1
        for criteria in other_missing[:3]:  # Limit to next 3 steps
            if criteria == QualificationCriteria.URGENCY_ASSESSED.value:
                next_steps.append(f"{step_num}. Assess urgency level")
            elif criteria == QualificationCriteria.BUDGET_DISCUSSED.value:
                next_steps.append(f"{step_num}. Discuss budget expectations")
            elif criteria == QualificationCriteria.AVAILABILITY_CONFIRMED.value:
                next_steps.append(f"{step_num}. Confirm availability")
            step_num += 1
        
        return next_steps
    
    def _estimate_completion_time(
        self, 
        score: QualificationScore, 
        conversation_state: Dict[str, Any]
    ) -> Optional[datetime]:
        """Estimate when qualification might be completed."""
        if score.completion_percentage >= 100:
            return datetime.now()
        
        # Base estimation on current progress and conversation activity
        missing_count = len(score.missing_criteria)
        conversation_start = conversation_state.get('start_time')
        
        if conversation_start:
            start_time = datetime.fromisoformat(conversation_start) if isinstance(conversation_start, str) else conversation_start
            elapsed_time = datetime.now() - start_time
            
            # Estimate based on current pace
            if score.completion_percentage > 0:
                estimated_total_time = elapsed_time * (100 / score.completion_percentage)
                return start_time + estimated_total_time
        
        # Default estimation based on missing items
        estimated_minutes = missing_count * 10  # 10 minutes per missing item
        return datetime.now() + timedelta(minutes=estimated_minutes)
    
    def _is_qualification_on_track(self, conversation_state: Dict[str, Any]) -> bool:
        """Check if qualification is progressing at expected pace."""
        start_time = conversation_state.get('start_time')
        if not start_time:
            return True
        
        start_dt = datetime.fromisoformat(start_time) if isinstance(start_time, str) else start_time