import os
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Text,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Create a separate Base for this module to avoid circular imports
ConversationBase = declarative_base()

logger = logging.getLogger(__name__)


class ConversationState(ConversationBase):
    """Model for tracking conversation state and question-answer flow."""

    __tablename__ = "conversation_states"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String(255), unique=True, nullable=False, index=True)
    lead_id = Column(
        Integer, nullable=True, index=True
    )  # No FK constraint to avoid circular dependency

    # Core conversation tracking
    conversation_data = Column(JSON, nullable=False, default=dict)
    current_question_index = Column(Integer, default=0, nullable=False)
    is_complete = Column(Boolean, default=False, nullable=False)

    # Status and metadata
    last_message_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<ConversationState(id={self.id}, thread_id='{self.thread_id}', complete={self.is_complete})>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "lead_id": self.lead_id,
            "conversation_data": self.conversation_data,
            "current_question_index": self.current_question_index,
            "is_complete": self.is_complete,
            "last_message_at": (
                self.last_message_at.isoformat() if self.last_message_at else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_question_answer_pairs(self) -> List[Dict[str, Any]]:
        """Extract question-answer pairs from conversation data."""
        if not self.conversation_data or "questions" not in self.conversation_data:
            return []

        pairs = []
        questions = self.conversation_data.get("questions", [])
        answers = self.conversation_data.get("answers", [])

        for i, question in enumerate(questions):
            answer = answers[i] if i < len(answers) else None
            pairs.append(
                {
                    "question_index": i,
                    "question": question,
                    "answer": answer,
                    "answered": answer is not None,
                }
            )

        return pairs

    def add_answer(self, answer: str) -> bool:
        """Add an answer to the current question and advance."""
        try:
            if not self.conversation_data:
                self.conversation_data = {"questions": [], "answers": []}

            questions = self.conversation_data.get("questions", [])
            answers = self.conversation_data.get("answers", [])

            # Ensure we have a question to answer
            if self.current_question_index >= len(questions):
                return False

            # Add answer at current index
            while len(answers) <= self.current_question_index:
                answers.append(None)

            answers[self.current_question_index] = answer
            self.conversation_data["answers"] = answers

            # Advance to next question
            self.current_question_index += 1

            # Check if conversation is complete
            if self.current_question_index >= len(questions):
                self.is_complete = True

            self.last_message_at = datetime.utcnow()
            return True

        except Exception as e:
            logger.error(
                f"Error adding answer to conversation {self.thread_id}: {str(e)}"
            )
            return False

    def set_questions(self, questions: List[str]) -> bool:
        """Set the list of questions for this conversation."""
        try:
            if not self.conversation_data:
                self.conversation_data = {}

            self.conversation_data["questions"] = questions

            # Initialize answers array if not exists
            if "answers" not in self.conversation_data:
                self.conversation_data["answers"] = []

            return True

        except Exception as e:
            logger.error(
                f"Error setting questions for conversation {self.thread_id}: {str(e)}"
            )
            return False

    def get_current_question(self) -> Optional[str]:
        """Get the current unanswered question."""
        if not self.conversation_data or "questions" not in self.conversation_data:
            return None

        questions = self.conversation_data["questions"]
        if self.current_question_index < len(questions):
            return questions[self.current_question_index]

        return None

    def reset_conversation(self) -> bool:
        """Reset conversation state to beginning."""
        try:
            self.current_question_index = 0
            self.is_complete = False

            if self.conversation_data and "answers" in self.conversation_data:
                self.conversation_data["answers"] = []

            self.last_message_at = datetime.utcnow()
            return True

        except Exception as e:
            logger.error(f"Error resetting conversation {self.thread_id}: {str(e)}")
            return False
