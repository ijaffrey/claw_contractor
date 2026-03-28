"""Qualification Flows Module

Defines question sequences for different trade types. Each flow consists of questions
that help qualify leads through structured conversations.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class QuestionType(Enum):
    """Types of qualification questions."""
    CONTACT_INFO = "contact_info"
    PROBLEM_DESCRIPTION = "problem_description"
    LOCATION_INFO = "location_info"
    URGENCY = "urgency"
    BUDGET = "budget"
    AVAILABILITY = "availability"
    PHOTOS = "photos"
    TRADE_SPECIFIC = "trade_specific"
    DIAGNOSTIC = "diagnostic"


@dataclass
class Question:
    """Represents a qualification question with metadata."""
    text: str
    question_type: QuestionType
    scoring_weight: float = 1.0
    is_required: bool = True
    follow_up_questions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize question with default metadata."""
        if not self.metadata:
            self.metadata = {
                'question_id': f"{self.question_type.value}_{hash(self.text) % 10000}",
                'created_at': None,
                'answered': False,
                'answer': None
            }


# Universal questions that apply to all trades
UNIVERSAL_QUESTIONS = [
    Question(
        text="What's the best phone number to reach you at?",
        question_type=QuestionType.CONTACT_INFO,
        scoring_weight=2.0,
        is_required=True,
        metadata={'priority': 'high', 'validates_contact': True}
    ),
    Question(
        text="What's your address or the location where the work needs to be done?",
        question_type=QuestionType.LOCATION_INFO,
        scoring_weight=2.0,
        is_required=True,
        metadata={'priority': 'high', 'enables_routing': True}
    ),
    Question(
        text="Can you describe the problem or project in more detail?",
        question_type=QuestionType.PROBLEM_DESCRIPTION,
        scoring_weight=1.5,
        is_required=True,
        metadata={'priority': 'high', 'enables_diagnosis': True}
    ),
    Question(
        text="How urgent is this? Is this an emergency or can it wait a few days?",
        question_type=QuestionType.URGENCY,
        scoring_weight=1.5,
        is_required=True,
        metadata={'priority': 'medium', 'affects_scheduling': True}
    ),
    Question(
        text="What times work best for you for a service visit?",
        question_type=QuestionType.AVAILABILITY,
        scoring_weight=1.0,
        is_required=False,
        metadata={'priority': 'medium', 'enables_scheduling': True}
    ),
    Question(
        text="Do you have a budget range in mind for this project?",
        question_type=QuestionType.BUDGET,
        scoring_weight=1.0,
        is_required=False,
        metadata={'priority': 'low', 'helps_qualification': True}
    )
]


# Plumbing-specific questions
PLUMBING_QUESTIONS = [
    Question(
        text="Is there any water leaking or flooding right now?",
        question_type=QuestionType.TRADE_SPECIFIC,
        scoring_weight=2.0,
        is_required=True,
        metadata={'emergency_indicator': True, 'affects_urgency': True}
    ),
    Question(
        text="Where is the problem located? (kitchen, bathroom, basement, etc.)",
        question_type=QuestionType.TRADE_SPECIFIC,
        scoring_weight=1.5,
        is_required=True,
        metadata={'helps_diagnosis': True, 'affects_complexity': True}
    ),
    Question(
        text="Can you send photos of the problem area?",
        question_type=QuestionType.PHOTOS,
        scoring_weight=1.5,
        is_required=False,
        metadata={'enables_remote_diagnosis': True, 'improves_accuracy': True}
    ),
    Question(
        text="Have you tried turning off the water supply to that area?",
        question_type=QuestionType.DIAGNOSTIC,
        scoring_weight=1.0,
        is_required=False,
        metadata={'safety_check': True, 'emergency_response': True}
    ),
    Question(
        text="Is this a recurring problem or the first time it's happened?",
        question_type=QuestionType.TRADE_SPECIFIC,
        scoring_weight=1.0,
        is_required=False,
        metadata={'indicates_complexity': True, 'affects_solution': True}
    )
]


# Electrical-specific questions  
ELECTRICAL_QUESTIONS = [
    Question(
        text="Is there any immediate safety concern? (sparks, burning smell, no power to critical areas)",
        question_type=QuestionType.TRADE_SPECIFIC,
        scoring_weight=2.5,
        is_required=True,
        metadata={'emergency_indicator': True, 'safety_critical': True}
    ),
    Question(
        text="What electrical problem are you experiencing? (outlet not working, lights flickering, breaker tripping, etc.)",
        question_type=QuestionType.TRADE_SPECIFIC,
        scoring_weight=1.5,
        is_required=True,
        metadata={'helps_diagnosis': True, 'affects_approach': True}
    ),
    Question(
        text="Have you checked your electrical panel/breaker box?",
        question_type=QuestionType.DIAGNOSTIC,
        scoring_weight=1.0,
        is_required=False,
        metadata={'first_troubleshooting_step': True, 'safety_check': True}
    ),
    Question(
        text="Can you send photos of your electrical panel or the problem area?",
        question_type=QuestionType.PHOTOS,
        scoring_weight=1.5,
        is_required=False,
        metadata={'enables_remote_diagnosis': True, 'safety_assessment': True}
    ),
    Question(
        text="When did this problem start? Was it sudden or gradual?",
        question_type=QuestionType.TRADE_SPECIFIC,
        scoring_weight=1.0,
        is_required=False,
        metadata={'indicates_cause': True, 'affects_diagnosis': True}
    )
]

# Trade-specific question flows
TRADE_FLOWS = {
    'plumbing': UNIVERSAL_QUESTIONS + PLUMBING_QUESTIONS,
    'electrical': UNIVERSAL_QUESTIONS + ELECTRICAL_QUESTIONS,
    'general_contractor': UNIVERSAL_QUESTIONS,
    'roofing': UNIVERSAL_QUESTIONS,
    'hvac': UNIVERSAL_QUESTIONS
}


def get_flow(trade_type: str) -> List[Question]:
    """
    Get the question flow for a specific trade type.
    
    Args:
        trade_type (str): The trade type (e.g., 'plumbing', 'electrical')
        
    Returns:
        List[Question]: List of questions for the trade, or universal questions if trade not found
    """
    trade_key = trade_type.lower()
    flow = TRADE_FLOWS.get(trade_key, UNIVERSAL_QUESTIONS)
    
    # Create deep copies to avoid modifying the originals
    questions = []
    for q in flow:
        question_copy = Question(
            text=q.text,
            question_type=q.question_type,
            scoring_weight=q.scoring_weight,
            is_required=q.is_required,
            follow_up_questions=q.follow_up_questions.copy(),
            metadata=q.metadata.copy()
        )
        questions.append(question_copy)
    
    logger.info(f"Retrieved {len(questions)} questions for trade type: {trade_type}")
    return questions


def get_next_question(questions: List[Question], answered_questions: Dict[str, Any]) -> Optional[Question]:
    """
    Find the next unanswered question in the sequence.
    
    Args:
        questions (List[Question]): The question flow
        answered_questions (Dict[str, Any]): Dictionary of answered question IDs and their answers
        
    Returns:
        Optional[Question]: Next unanswered question, or None if all are answered
    """
    if not questions:
        return None
    
    for question in questions:
        question_id = question.metadata.get('question_id', '')
        
        # Check if this question has been answered
        if question_id not in answered_questions:
            logger.debug(f"Next unanswered question: {question.text[:50]}...")
            return question
    
    logger.info("All questions have been answered")
    return None


def get_required_questions(questions: List[Question]) -> List[Question]:
    """
    Get only the required questions from a flow.
    
    Args:
        questions (List[Question]): The question flow
        
    Returns:
        List[Question]: Only the required questions
    """
    required = [q for q in questions if q.is_required]
    logger.debug(f"Found {len(required)} required questions out of {len(questions)} total")
    return required


def calculate_flow_completeness(questions: List[Question], answered_questions: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate how complete a qualification flow is based on answered questions.
    
    Args:
        questions (List[Question]): The question flow
        answered_questions (Dict[str, Any]): Dictionary of answered question IDs
        
    Returns:
        Dict[str, float]: Completeness metrics including overall, required, and weighted scores
    """
    if not questions:
        return {'overall': 1.0, 'required': 1.0, 'weighted_score': 0.0, 'max_weighted_score': 0.0}
    
    total_questions = len(questions)
    required_questions = [q for q in questions if q.is_required]
    required_count = len(required_questions)
    
    answered_count = 0
    required_answered = 0
    weighted_score = 0.0
    max_weighted_score = 0.0
    
    for question in questions:
        question_id = question.metadata.get('question_id', '')
        max_weighted_score += question.scoring_weight
        
        if question_id in answered_questions:
            answered_count += 1
            weighted_score += question.scoring_weight
            
            if question.is_required:
                required_answered += 1
    
    overall_completeness = answered_count / total_questions if total_questions > 0 else 1.0
    required_completeness = required_answered / required_count if required_count > 0 else 1.0
    
    return {
        'overall': overall_completeness,
        'required': required_completeness,
        'weighted_score': weighted_score,
        'max_weighted_score': max_weighted_score
    }