import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.conversation_manager import ConversationManager
from src.models.lead import Lead
from src.models.conversation import ConversationMessage
from src.database.database_manager import DatabaseManager


@pytest.fixture
def mock_db_manager():
    """Mock database manager fixture."""
    return Mock(spec=DatabaseManager)


@pytest.fixture
def conversation_manager(mock_db_manager):
    """ConversationManager instance with mocked database."""
    return ConversationManager(db_manager=mock_db_manager)


@pytest.fixture
def sample_lead():
    """Sample lead data for testing."""
    return Lead(
        id=1,
        name="John Doe",
        phone="+1234567890",
        email="john@example.com",
        company="Test Corp",
        status="new",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def sample_conversation_messages():
    """Sample conversation messages for testing."""
    base_time = datetime(2024, 1, 1, 10, 0, 0)
    return [
        ConversationMessage(
            id=1,
            lead_id=1,
            thread_id="thread_123",
            role="assistant",
            content="Hello! How can I help you today?",
            timestamp=base_time,
            metadata={"step": "greeting"}
        ),
        ConversationMessage(
            id=2,
            lead_id=1,
            thread_id="thread_123",
            role="user",
            content="I'm interested in your services",
            timestamp=base_time.replace(minute=1),
            metadata={}
        ),
        ConversationMessage(
            id=3,
            lead_id=1,
            thread_id="thread_123",
            role="assistant",
            content="Great! What type of project are you working on?",
            timestamp=base_time.replace(minute=2),
            metadata={"step": "project_inquiry"}
        )
    ]


class TestLoadConversationHistory:
    """Test cases for load_conversation_history method."""

    def test_load_conversation_history_valid_lead_id(self, conversation_manager, mock_db_manager, sample_conversation_messages):
        """Test loading conversation history for valid lead ID."""
        # Arrange
        lead_id = 1
        mock_db_manager.get_conversation_history.return_value = sample_conversation_messages
        
        # Act
        result = conversation_manager.load_conversation_history(lead_id)
        
        # Assert
        assert result == sample_conversation_messages
        mock_db_manager.get_conversation_history.assert_called_once_with(lead_id)

    def test_load_conversation_history_invalid_lead_id(self, conversation_manager, mock_db_manager):
        """Test loading conversation history for invalid lead ID."""
        # Arrange
        invalid_lead_id = -1
        mock_db_manager.get_conversation_history.side_effect = ValueError("Invalid lead ID")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid lead ID"):
            conversation_manager.load_conversation_history(invalid_lead_id)

    def test_load_conversation_history_nonexistent_lead(self, conversation_manager, mock_db_manager):
        """Test loading conversation history for non-existent lead."""
        # Arrange
        nonexistent_lead_id = 999
        mock_db_manager.get_conversation_history.return_value = []
        
        # Act
        result = conversation_manager.load_conversation_history(nonexistent_lead_id)
        
        # Assert
        assert result == []
        mock_db_manager.get_conversation_history.assert_called_once_with(nonexistent_lead_id)

    def test_load_conversation_history_empty_history(self, conversation_manager, mock_db_manager):
        """Test loading empty conversation history."""
        # Arrange
        lead_id = 1
        mock_db_manager.get_conversation_history.return_value = []
        
        # Act
        result = conversation_manager.load_conversation_history(lead_id)
        
        # Assert
        assert result == []
        assert len(result) == 0

    def test_load_conversation_history_chronological_ordering(self, conversation_manager, mock_db_manager):
        """Test that conversation history is returned in chronological order."""
        # Arrange
        lead_id = 1
        base_time = datetime(2024, 1, 1, 10, 0, 0)
        unordered_messages = [
            ConversationMessage(
                id=3,
                lead_id=1,
                thread_id="thread_123",
                role="assistant",
                content="Third message",
                timestamp=base_time.replace(minute=2),
                metadata={}
            ),
            ConversationMessage(
                id=1,
                lead_id=1,
                thread_id="thread_123",
                role="user",
                content="First message",
                timestamp=base_time,
                metadata={}
            ),
            ConversationMessage(
                id=2,
                lead_id=1,
                thread_id="thread_123",
                role="assistant",
                content="Second message",
                timestamp=base_time.replace(minute=1),
                metadata={}
            )
        ]
        mock_db_manager.get_conversation_history.return_value = unordered_messages
        
        # Act
        result = conversation_manager.load_conversation_history(lead_id)
        
        # Assert
        assert len(result) == 3
        assert result[0].timestamp <= result[1].timestamp <= result[2].timestamp

    def test_load_conversation_history_database_error(self, conversation_manager, mock_db_manager):
        """Test handling database errors during conversation history loading."""
        # Arrange
        lead_id = 1
        mock_db_manager.get_conversation_history.side_effect = Exception("Database connection failed")
        
        # Act & Assert
        with pytest.raises(Exception, match="Database connection failed"):
            conversation_manager.load_conversation_history(lead_id)


class TestGetConversationContext:
    """Test cases for get_conversation_context method."""

    def test_get_conversation_context_with_history(self, conversation_manager, mock_db_manager, sample_lead, sample_conversation_messages):
        """Test getting conversation context with existing history."""
        # Arrange
        lead_id = 1
        mock_db_manager.get_lead_by_id.return_value = sample_lead
        mock_db_manager.get_conversation_history.return_value = sample_conversation_messages
        
        # Act
        result = conversation_manager.get_conversation_context(lead_id)
        
        # Assert
        assert "lead" in result
        assert "conversation_history" in result
        assert "current_step" in result
        assert "context_summary" in result
        assert result["lead"] == sample_lead
        assert result["conversation_history"] == sample_conversation_messages
        assert len(result["conversation_history"]) == 3

    def test_get_conversation_context_no_history(self, conversation_manager, mock_db_manager, sample_lead):
        """Test getting conversation context with no existing history."""
        # Arrange
        lead_id = 1
        mock_db_manager.get_lead_by_id.return_value = sample_lead
        mock_db_manager.get_conversation_history.return_value = []
        
        # Act
        result = conversation_manager.get_conversation_context(lead_id)
        
        # Assert
        assert result["lead"] == sample_lead
        assert result["conversation_history"] == []
        assert result["current_step"] == "initial"

    def test_get_conversation_context_with_qualification_steps(self, conversation_manager, mock_db_manager, sample_lead):
        """Test conversation context with various qualification steps."""
        # Arrange
        lead_id = 1
        messages_with_steps = [
            ConversationMessage(
                id=1,
                lead_id=1,
                thread_id="thread_123",
                role="assistant",
                content="What's your budget?",
                timestamp=datetime.now(),
                metadata={"step": "budget_qualification"}
            )
        ]
        mock_db_manager.get_lead_by_id.return_value = sample_lead
        mock_db_manager.get_conversation_history.return_value = messages_with_steps
        
        # Act
        result = conversation_manager.get_conversation_context(lead_id)
        
        # Assert
        assert result["current_step"] == "budget_qualification"
        assert "budget_qualification" in result["context_summary"]

    def test_get_conversation_context_invalid_lead(self, conversation_manager, mock_db_manager):
        """Test getting conversation context for invalid lead."""
        # Arrange
        invalid_lead_id = -1
        mock_db_manager.get_lead_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Lead not found"):
            conversation_manager.get_conversation_context(invalid_lead_id)

    def test_get_conversation_context_with_metadata(self, conversation_manager, mock_db_manager, sample_lead):
        """Test conversation context includes message metadata."""
        # Arrange
        lead_id = 1
        messages_with_metadata = [
            ConversationMessage(
                id=1,
                lead_id=1,
                thread_id="thread_123",
                role="assistant",
                content="Test message",
                timestamp=datetime.now(),
                metadata={"step": "testing", "priority": "high", "tags": ["important"]}
            )
        ]
        mock_db_manager.get_lead_by_id.return_value = sample_lead
        mock_db_manager.get_conversation_history.return_value = messages_with_metadata
        
        # Act
        result = conversation_manager.get_conversation_context(lead_id)
        
        # Assert
        message_metadata = result["conversation_history"][0].metadata
        assert message_metadata["step"] == "testing"
        assert message_metadata["priority"] == "high"
        assert "important" in message_metadata["tags"]


class TestUpdateThreadId:
    """Test cases for update_thread_id method."""

    def test_update_thread_id_success(self, conversation_manager, mock_db_manager):
        """Test successful thread ID update."""
        # Arrange
        lead_id = 1
        thread_id = "new_thread_456"
        mock_db_manager.update_thread_mapping.return_value = True
        
        # Act
        result = conversation_manager.update_thread_id(lead_id, thread_id)
        
        # Assert
        assert result is True
        mock_db_manager.update_thread_mapping.assert_called_once_with(lead_id, thread_id)

    def test_update_thread_id_invalid_lead_id(self, conversation_manager, mock_db_manager):
        """Test thread ID update with invalid lead ID."""
        # Arrange
        invalid_lead_id = -1
        thread_id = "thread_123"
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid lead ID"):
            conversation_manager.update_thread_id(invalid_lead_id, thread_id)

    def test_update_thread_id_empty_thread_id(self, conversation_manager, mock_db_manager):
        """Test thread ID update with empty thread ID."""
        # Arrange
        lead_id = 1
        empty_thread_id = ""
        
        # Act & Assert
        with pytest.raises(ValueError, match="Thread ID cannot be empty"):
            conversation_manager.update_thread_id(lead_id, empty_thread_id)

    def test_update_thread_id_none_thread_id(self, conversation_manager, mock_db_manager):
        """Test thread ID update with None thread ID."""
        # Arrange
        lead_id = 1
        none_thread_id = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Thread ID cannot be None"):
            conversation_manager.update_thread_id(lead_id, none_thread_id)

    def test_update_thread_id_database_error(self, conversation_manager, mock_db_manager):
        """Test thread ID update with database error."""
        # Arrange
        lead_id = 1
        thread_id = "thread_123"
        mock_db_manager.update_thread_mapping.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            conversation_manager.update_thread_id(lead_id, thread_id)

    def test_update_thread_id_nonexistent_lead(self, conversation_manager, mock_db_manager):
        """Test thread ID update for non-existent lead."""
        # Arrange
        nonexistent_lead_id = 999
        thread_id = "thread_123"
        mock_db_manager.update_thread_mapping.return_value = False
        
        # Act
        result = conversation_manager.update_thread_id(nonexistent_lead_id, thread_id)
        
        # Assert
        assert result is False

    def test_update_thread_id_existing_mapping(self, conversation_manager, mock_db_manager):
        """Test updating an existing thread ID mapping."""
        # Arrange
        lead_id = 1
        old_thread_id = "old_thread_123"
        new_thread_id = "new_thread_456"
        mock_db_manager.get_thread_id.return_value = old_thread_id
        mock_db_manager.update_thread_mapping.return_value = True
        
        # Act
        result = conversation_manager.update_thread_id(lead_id, new_thread_id)
        
        # Assert
        assert result is True
        mock_db_manager.update_thread_mapping.assert_called_once_with(lead_id, new_thread_id)


class TestGetNextQualificationStep:
    """Test cases for get_next_qualification_step method."""

    def test_get_next_qualification_step_initial(self, conversation_manager, mock_db_manager):
        """Test getting next qualification step for initial conversation."""
        # Arrange
        lead_id = 1
        mock_db_manager.get_conversation_history.return_value = []
        
        # Act
        result = conversation_manager.get_next_qualification_step(lead_id)
        
        # Assert
        assert result == "greeting"

    def test_get_next_qualification_step_after_greeting(self, conversation_manager, mock_db_manager):
        """Test getting next qualification step after greeting."""
        # Arrange
        lead_id = 1
        messages = [
            ConversationMessage(
                id=1,
                lead_id=1,
                thread_id="thread_123",
                role="assistant",
                content="Hello!",
                timestamp=datetime.now(),
                metadata={"step": "greeting"}
            )
        ]
        mock_db_manager.get_conversation_history.return_value = messages
        
        # Act
        result = conversation_manager.get_next_qualification_step(lead_id)
        
        # Assert
        assert result == "project_inquiry"

    def test_get_next_qualification_step_progression(self, conversation_manager, mock_db_manager):
        """Test qualification step progression through multiple steps."""
        # Arrange
        lead_id = 1
        test_cases = [
            ("greeting", "project_inquiry"),
            ("project_inquiry", "budget_qualification"),
            ("budget_qualification", "timeline_discussion"),
            ("timeline_discussion", "contact_information"),
            ("contact_information", "proposal_scheduling"),
            ("proposal_scheduling", "completed")
        ]
        
        for current_step, expected_next in test_cases:
            messages = [
                ConversationMessage(
                    id=1,
                    lead_id=1,
                    thread_id="thread_123",
                    role="assistant",
                    content="Test",
                    timestamp=datetime.now(),
                    metadata={"step": current_step}
                )
            ]
            mock_db_manager.get_conversation_history.return_value = messages
            
            # Act
            result = conversation_manager.get_next_qualification_step(lead_id)
            
            # Assert
            assert result == expected_next

    def test_get_next_qualification_step_completed(self, conversation_manager, mock_db_manager):
        """Test getting next qualification step when already completed."""
        # Arrange
        lead_id = 1
        messages = [
            ConversationMessage(
                id=1,
                lead_id=1,
                thread_id="thread_123",
                role="assistant",
                content="All set!",
                timestamp=datetime.now(),
                metadata={"step": "completed"}
            )
        ]
        mock_db_manager.get_conversation_history.return_value = messages
        
        # Act
        result = conversation_manager.get_next_qualification_step(lead_id)
        
        # Assert
        assert result == "completed"

    def test_get_next_qualification_step_mixed_conversation(self, conversation_manager, mock_db_manager):
        """Test getting next qualification step with mixed conversation types."""
        # Arrange
        lead_id = 1
        messages = [
            ConversationMessage(
                id=1,
                lead_id=1,
                thread_id="thread_123",
                role="assistant",
                content="Hello!",
                timestamp=datetime.now(),
                metadata={"step": "greeting"}
            ),
            ConversationMessage(
                id=2,
                lead_id=1,
                thread_id="thread_123",
                role="user",
                content="Hi there",
                timestamp=datetime.now(),
                metadata={}
            ),
            ConversationMessage(
                id=3,
                lead_id=1,
                thread_id="thread_123",
                role="assistant",
                content="What project?",
                timestamp=datetime.now(),
                metadata={"step": "project_inquiry"}
            )
        ]
        mock_db_manager.get_conversation_history.return_value = messages
        
        # Act
        result = conversation_manager.get_next_qualification_step(lead_id)
        
        # Assert
        assert result == "budget_qualification"

    def test_get_next_qualification_step_no_metadata(self, conversation_manager, mock_db_manager):
        """Test getting next qualification step with messages lacking step metadata."""
        # Arrange
        lead_id = 1
        messages = [
            ConversationMessage(
                id=1,
                lead_id=1,
                thread_id="thread_123",
                role="assistant",
                content="Random message",
                timestamp=datetime.now(),
                metadata={}
            )
        ]
        mock_db_manager.get_conversation_history.return_value = messages
        
        # Act
        result = conversation_manager.get_next_qualification_step(lead_id)
        
        # Assert
        assert result == "greeting"

    def test_get_next_qualification_step_invalid_lead(self, conversation_manager, mock_db_manager):
        """Test getting next qualification step for invalid lead."""
        # Arrange
        invalid_lead_id = -1
        mock_db_manager.get_conversation_history.side_effect = ValueError("Invalid lead ID")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid lead ID"):
            conversation_manager.get_next_qualification_step(invalid_lead_id)


class TestConversationManagerEdgeCases:
    """Test edge cases and error handling."""

    def test_conversation_manager_initialization(self, mock_db_manager):
        """Test ConversationManager initialization."""
        # Act
        cm = ConversationManager(db_manager=mock_db_manager)
        
        # Assert
        assert cm.db_manager == mock_db_manager
        assert hasattr(cm, 'qualification_steps')

    def test_conversation_manager_without_db_manager(self):
        """Test ConversationManager initialization without database manager."""
        # Act & Assert
        with pytest.raises(TypeError):
            ConversationManager()

    def test_large_conversation_history_handling(self, conversation_manager, mock_db_manager, sample_lead):
        """Test handling large conversation histories."""
        # Arrange
        lead_id = 1
        large_history = []
        base_time = datetime.now()
        
        for i in range(1000):
            large_history.append(
                ConversationMessage(
                    id=i,
                    lead_id=1,
                    thread_id="thread_123",
                    role="user" if i % 2 == 0 else "assistant",
                    content=f"Message {i}",
                    timestamp=base_time.replace(minute=i % 60, second=i % 60),
                    metadata={"step": "ongoing"}
                )
            )
        
        mock_db_manager.get_lead_by_id.return_value = sample_lead
        mock_db_manager.get_conversation_history.return_value = large_history
        
        # Act
        result = conversation_manager.get_conversation_context(lead_id)
        
        # Assert
        assert len(result["conversation_history"]) == 1000
        assert result["lead"] == sample_lead

    def test_unicode_content_handling(self, conversation_manager, mock_db_manager):
        """Test handling Unicode content in conversations."""
        # Arrange
        lead_id = 1
        unicode_messages = [
            ConversationMessage(
                id=1,
                lead_id=1,
                thread_id="thread_123",
                role="user",
                content="Hello! 你好 🚀 ñ é ü",
                timestamp=datetime.now(),
                metadata={"language": "mixed"}
            )
        ]
        mock_db_manager.get_conversation_history.return_value = unicode_messages
        
        # Act
        result = conversation_manager.load_conversation_history(lead_id)
        
        # Assert
        assert len(result) == 1
        assert "你好" in result[0].content
        assert "🚀" in result[0].content

    def test_concurrent_access_simulation(self, conversation_manager, mock_db_manager):
        """Test simulation of concurrent access scenarios."""
        # Arrange
        lead_id = 1
        thread_id = "thread_concurrent"
        
        # Simulate concurrent updates
        mock_db_manager.update_thread_mapping.side_effect = [True, False, True]
        
        # Act
        results = []
        for _ in range(3):
            try:
                result = conversation_manager.update_thread_id(lead_id, thread_id)
                results.append(result)
            except Exception as e:
                results.append(str(e))
        
        # Assert
        assert True in results
        assert False in results
        assert len(results) == 3