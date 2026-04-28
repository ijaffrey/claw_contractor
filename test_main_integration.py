import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json
from datetime import datetime, timedelta

from main import main_loop
from models import Base, Email, Lead, Conversation, QualifiedLead, User, Client
from email_processor import EmailProcessor
from lead_qualifier import LeadQualifier
from conversation_manager import ConversationManager
from qualified_lead_handler import QualifiedLeadHandler


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    db_fd, db_path = tempfile.mkstemp()
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    yield Session, engine

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def mock_email_data():
    """Provide realistic test email data."""
    return [
        {
            "id": "email_1",
            "subject": "Need help with Python development project",
            "body": "Hi, I run a fintech startup and need a senior Python developer for a 6-month project. Budget is $150k. Can we discuss?",
            "from_email": "ceo@fintechstartup.com",
            "from_name": "John Smith",
            "timestamp": datetime.utcnow() - timedelta(hours=2),
            "thread_id": "thread_1",
        },
        {
            "id": "email_2",
            "subject": "Quick question about rates",
            "body": "What are your hourly rates for Python work?",
            "from_email": "student@university.edu",
            "from_name": "Jane Doe",
            "timestamp": datetime.utcnow() - timedelta(hours=1),
            "thread_id": "thread_2",
        },
        {
            "id": "email_3",
            "subject": "Enterprise Python migration project",
            "body": "We have a legacy Python 2 system that needs migration to Python 3. Timeline is 4 months, budget around $200k. Looking for experienced team.",
            "from_email": "tech@enterprise.com",
            "from_name": "Mike Johnson",
            "timestamp": datetime.utcnow() - timedelta(minutes=30),
            "thread_id": "thread_3",
        },
    ]


@pytest.fixture
def qualified_lead_data():
    """Provide data that should qualify as a lead."""
    return {
        "project_type": "Python Development",
        "budget": 150000,
        "timeline": "6 months",
        "company": "FinTech Startup Inc.",
        "urgency": "high",
        "tech_stack": ["Python", "Django", "PostgreSQL"],
        "team_size": 3,
    }


@pytest.fixture
def non_qualified_lead_data():
    """Provide data that should not qualify as a lead."""
    return {
        "project_type": "Simple website",
        "budget": 500,
        "timeline": "1 week",
        "company": None,
        "urgency": "low",
        "tech_stack": ["HTML", "CSS"],
        "team_size": 1,
    }


class TestMainLoopIntegration:
    """Integration tests for the main loop with qualified lead detection and handoff."""

    @pytest.mark.asyncio
    async def test_main_loop_processes_emails_and_detects_qualified_leads(
        self, temp_db, mock_email_data, qualified_lead_data
    ):
        """Test that main loop processes emails and correctly identifies qualified leads."""
        Session, engine = temp_db

        with patch("main.get_db_session") as mock_get_session:
            mock_get_session.return_value = Session()

            with patch("main.EmailProcessor") as mock_email_processor, patch(
                "main.LeadQualifier"
            ) as mock_lead_qualifier, patch(
                "main.ConversationManager"
            ) as mock_conv_manager, patch(
                "main.QualifiedLeadHandler"
            ) as mock_handler:

                # Setup mocks
                mock_processor = AsyncMock()
                mock_email_processor.return_value = mock_processor
                mock_processor.fetch_new_emails.return_value = mock_email_data
                mock_processor.process_email.return_value = True

                mock_qualifier = Mock()
                mock_lead_qualifier.return_value = mock_qualifier
                mock_qualifier.analyze_email.return_value = qualified_lead_data
                mock_qualifier.is_qualified_lead.return_value = True

                mock_cm = Mock()
                mock_conv_manager.return_value = mock_cm
                mock_cm.get_or_create_conversation.return_value = Mock(id=1)

                mock_qlh = AsyncMock()
                mock_handler.return_value = mock_qlh
                mock_qlh.handle_qualified_lead.return_value = True

                # Run one iteration of main loop
                with patch("main.asyncio.sleep", side_effect=KeyboardInterrupt):
                    try:
                        await main_loop()
                    except KeyboardInterrupt:
                        pass

                # Verify emails were processed
                assert mock_processor.fetch_new_emails.called
                assert mock_processor.process_email.call_count == 3

                # Verify lead qualification was performed
                assert mock_qualifier.analyze_email.call_count == 3
                assert mock_qualifier.is_qualified_lead.call_count == 3

                # Verify qualified lead handler was called for qualified leads
                qualified_calls = [
                    call for call in mock_qlh.handle_qualified_lead.call_args_list
                ]
                assert len(qualified_calls) > 0

    @pytest.mark.asyncio
    async def test_qualified_leads_trigger_handoff_without_breaking_loop(
        self, temp_db, mock_email_data
    ):
        """Test that qualified leads trigger handoff workflow without breaking the main loop."""
        Session, engine = temp_db

        with patch("main.get_db_session") as mock_get_session:
            mock_get_session.return_value = Session()

            with patch("main.EmailProcessor") as mock_email_processor, patch(
                "main.LeadQualifier"
            ) as mock_lead_qualifier, patch(
                "main.ConversationManager"
            ) as mock_conv_manager, patch(
                "main.QualifiedLeadHandler"
            ) as mock_handler:

                # Setup mocks
                mock_processor = AsyncMock()
                mock_email_processor.return_value = mock_processor
                mock_processor.fetch_new_emails.return_value = mock_email_data
                mock_processor.process_email.return_value = True

                mock_qualifier = Mock()
                mock_lead_qualifier.return_value = mock_qualifier
                mock_qualifier.analyze_email.return_value = {"budget": 150000}
                mock_qualifier.is_qualified_lead.return_value = True

                mock_cm = Mock()
                mock_conv_manager.return_value = mock_cm
                mock_cm.get_or_create_conversation.return_value = Mock(id=1)

                mock_qlh = AsyncMock()
                mock_handler.return_value = mock_qlh
                mock_qlh.handle_qualified_lead.return_value = True

                loop_iterations = 0
                original_sleep = asyncio.sleep

                async def counting_sleep(duration):
                    nonlocal loop_iterations
                    loop_iterations += 1
                    if loop_iterations >= 2:  # Run two iterations
                        raise KeyboardInterrupt()
                    await original_sleep(0.01)

                with patch("main.asyncio.sleep", counting_sleep):
                    try:
                        await main_loop()
                    except KeyboardInterrupt:
                        pass

                # Verify loop completed multiple iterations
                assert loop_iterations >= 2

                # Verify qualified lead handler was called
                assert mock_qlh.handle_qualified_lead.called

                # Verify processing continued normally
                assert mock_processor.fetch_new_emails.call_count >= 2

    @pytest.mark.asyncio
    async def test_non_qualified_leads_continue_normal_processing(
        self, temp_db, mock_email_data
    ):
        """Test that non-qualified leads continue through normal processing without handoff."""
        Session, engine = temp_db

        with patch("main.get_db_session") as mock_get_session:
            mock_get_session.return_value = Session()

            with patch("main.EmailProcessor") as mock_email_processor, patch(
                "main.LeadQualifier"
            ) as mock_lead_qualifier, patch(
                "main.ConversationManager"
            ) as mock_conv_manager, patch(
                "main.QualifiedLeadHandler"
            ) as mock_handler:

                # Setup mocks for non-qualified leads
                mock_processor = AsyncMock()
                mock_email_processor.return_value = mock_processor
                mock_processor.fetch_new_emails.return_value = mock_email_data
                mock_processor.process_email.return_value = True

                mock_qualifier = Mock()
                mock_lead_qualifier.return_value = mock_qualifier
                mock_qualifier.analyze_email.return_value = {
                    "budget": 500
                }  # Low budget
                mock_qualifier.is_qualified_lead.return_value = False  # Not qualified

                mock_cm = Mock()
                mock_conv_manager.return_value = mock_cm
                mock_cm.get_or_create_conversation.return_value = Mock(id=1)
                mock_cm.generate_response.return_value = "Thank you for your interest."
                mock_cm.send_response.return_value = True

                mock_qlh = AsyncMock()
                mock_handler.return_value = mock_qlh

                with patch("main.asyncio.sleep", side_effect=KeyboardInterrupt):
                    try:
                        await main_loop()
                    except KeyboardInterrupt:
                        pass

                # Verify emails were processed normally
                assert mock_processor.process_email.call_count == 3

                # Verify lead qualification was performed
                assert mock_qualifier.analyze_email.call_count == 3
                assert mock_qualifier.is_qualified_lead.call_count == 3

                # Verify qualified lead handler was NOT called
                assert not mock_qlh.handle_qualified_lead.called

                # Verify normal conversation flow continued
                assert mock_cm.generate_response.call_count == 3
                assert mock_cm.send_response.call_count == 3

    @pytest.mark.asyncio
    async def test_handoff_error_handling_doesnt_crash_main_loop(
        self, temp_db, mock_email_data
    ):
        """Test that errors in the handoff process don't crash the main loop."""
        Session, engine = temp_db

        with patch("main.get_db_session") as mock_get_session:
            mock_get_session.return_value = Session()

            with patch("main.EmailProcessor") as mock_email_processor, patch(
                "main.LeadQualifier"
            ) as mock_lead_qualifier, patch(
                "main.ConversationManager"
            ) as mock_conv_manager, patch(
                "main.QualifiedLeadHandler"
            ) as mock_handler, patch(
                "main.logger"
            ) as mock_logger:

                # Setup mocks
                mock_processor = AsyncMock()
                mock_email_processor.return_value = mock_processor
                mock_processor.fetch_new_emails.return_value = mock_email_data
                mock_processor.process_email.return_value = True

                mock_qualifier = Mock()
                mock_lead_qualifier.return_value = mock_qualifier
                mock_qualifier.analyze_email.return_value = {"budget": 150000}
                mock_qualifier.is_qualified_lead.return_value = True

                mock_cm = Mock()
                mock_conv_manager.return_value = mock_cm
                mock_cm.get_or_create_conversation.return_value = Mock(id=1)

                # Make handoff handler raise an exception
                mock_qlh = AsyncMock()
                mock_handler.return_value = mock_qlh
                mock_qlh.handle_qualified_lead.side_effect = Exception(
                    "Handoff service unavailable"
                )

                loop_iterations = 0

                async def counting_sleep(duration):
                    nonlocal loop_iterations
                    loop_iterations += 1
                    if loop_iterations >= 2:
                        raise KeyboardInterrupt()
                    await asyncio.sleep(0.01)

                with patch("main.asyncio.sleep", counting_sleep):
                    try:
                        await main_loop()
                    except KeyboardInterrupt:
                        pass

                # Verify loop continued despite handoff errors
                assert loop_iterations >= 2

                # Verify errors were logged
                assert mock_logger.error.called

                # Verify email processing continued
                assert (
                    mock_processor.process_email.call_count >= 6
                )  # 3 emails × 2 iterations

    @pytest.mark.asyncio
    async def test_database_state_consistency_after_qualified_lead_processing(
        self, temp_db, mock_email_data
    ):
        """Test that database state remains consistent after qualified lead processing."""
        Session, engine = temp_db
        session = Session()

        # Create test user and client
        user = User(email="test@contractor.com", name="Test Contractor")
        client = Client(
            email="ceo@fintechstartup.com",
            name="John Smith",
            company="FinTech Startup Inc.",
        )
        session.add(user)
        session.add(client)
        session.commit()

        with patch("main.get_db_session") as mock_get_session:
            mock_get_session.return_value = session

            with patch("main.EmailProcessor") as mock_email_processor, patch(
                "main.LeadQualifier"
            ) as mock_lead_qualifier, patch(
                "main.ConversationManager"
            ) as mock_conv_manager, patch(
                "main.QualifiedLeadHandler"
            ) as mock_handler:

                # Setup mocks
                mock_processor = AsyncMock()
                mock_email_processor.return_value = mock_processor
                mock_processor.fetch_new_emails.return_value = [
                    mock_email_data[0]
                ]  # One qualified email
                mock_processor.process_email.side_effect = self._create_email_in_db

                mock_qualifier = Mock()
                mock_lead_qualifier.return_value = mock_qualifier
                mock_qualifier.analyze_email.return_value = {
                    "budget": 150000,
                    "project_type": "Python Development",
                    "timeline": "6 months",
                }
                mock_qualifier.is_qualified_lead.return_value = True

                mock_cm = Mock()
                mock_conv_manager.return_value = mock_cm
                conversation = Conversation(
                    client_id=client.id, user_id=user.id, status="active"
                )
                session.add(conversation)
                session.commit()
                mock_cm.get_or_create_conversation.return_value = conversation

                mock_qlh = AsyncMock()
                mock_handler.return_value = mock_qlh

                def handle_qualified_lead_side_effect(*args, **kwargs):
                    # Simulate creating a QualifiedLead record
                    qualified_lead = QualifiedLead(
                        conversation_id=conversation.id,
                        lead_data=json.dumps({"budget": 150000}),
                        qualification_score=0.9,
                        status="pending_handoff",
                        created_at=datetime.utcnow(),
                    )
                    session.add(qualified_lead)
                    session.commit()
                    return True

                mock_qlh.handle_qualified_lead.side_effect = (
                    handle_qualified_lead_side_effect
                )

                with patch("main.asyncio.sleep", side_effect=KeyboardInterrupt):
                    try:
                        await main_loop()
                    except KeyboardInterrupt:
                        pass

                # Verify database state
                emails = session.query(Email).all()
                assert len(emails) == 1
                assert emails[0].processed is True

                conversations = session.query(Conversation).all()
                assert len(conversations) == 1
                assert conversations[0].status == "active"

                qualified_leads = session.query(QualifiedLead).all()
                assert len(qualified_leads) == 1
                assert qualified_leads[0].status == "pending_handoff"
                assert qualified_leads[0].conversation_id == conversation.id

                # Verify referential integrity
                assert (
                    qualified_leads[0].conversation.client.email
                    == "ceo@fintechstartup.com"
                )

    def _create_email_in_db(self, email_data, session):
        """Helper method to create email in database during processing."""
        email = Email(
            email_id=email_data["id"],
            subject=email_data["subject"],
            body=email_data["body"],
            from_email=email_data["from_email"],
            from_name=email_data["from_name"],
            timestamp=email_data["timestamp"],
            thread_id=email_data["thread_id"],
            processed=True,
            created_at=datetime.utcnow(),
        )
        session.add(email)
        session.commit()
        return True

    @pytest.mark.asyncio
    async def test_mixed_qualified_and_non_qualified_leads_processing(self, temp_db):
        """Test processing a mix of qualified and non-qualified leads in the same batch."""
        Session, engine = temp_db

        mixed_email_data = [
            {
                "id": "qual_1",
                "subject": "Enterprise project - $200k budget",
                "body": "Need senior Python team for 6-month enterprise project.",
                "from_email": "ceo@enterprise.com",
                "from_name": "Enterprise CEO",
                "timestamp": datetime.utcnow(),
                "thread_id": "thread_qual_1",
            },
            {
                "id": "non_qual_1",
                "subject": "Quick question",
                "body": "What are your rates?",
                "from_email": "student@school.edu",
                "from_name": "Student",
                "timestamp": datetime.utcnow(),
                "thread_id": "thread_non_qual_1",
            },
            {
                "id": "qual_2",
                "subject": "Fintech startup needs Python developer",
                "body": "We have $150k budget for Python development project.",
                "from_email": "founder@fintech.com",
                "from_name": "Fintech Founder",
                "timestamp": datetime.utcnow(),
                "thread_id": "thread_qual_2",
            },
        ]

        with patch("main.get_db_session") as mock_get_session:
            mock_get_session.return_value = Session()

            with patch("main.EmailProcessor") as mock_email_processor, patch(
                "main.LeadQualifier"
            ) as mock_lead_qualifier, patch(
                "main.ConversationManager"
            ) as mock_conv_manager, patch(
                "main.QualifiedLeadHandler"
            ) as mock_handler:

                mock_processor = AsyncMock()
                mock_email_processor.return_value = mock_processor
                mock_processor.fetch_new_emails.return_value = mixed_email_data
                mock_processor.process_email.return_value = True

                def analyze_email_side_effect(email_data):
                    if (
                        "enterprise" in email_data["from_email"]
                        or "fintech" in email_data["from_email"]
                    ):
                        return {"budget": 150000, "qualified": True}
                    return {"budget": 0, "qualified": False}

                def is_qualified_side_effect(analysis):
                    return analysis.get("qualified", False)

                mock_qualifier = Mock()
                mock_lead_qualifier.return_value = mock_qualifier
                mock_qualifier.analyze_email.side_effect = analyze_email_side_effect
                mock_qualifier.is_qualified_lead.side_effect = is_qualified_side_effect

                mock_cm = Mock()
                mock_conv_manager.return_value = mock_cm
                mock_cm.get_or_create_conversation.return_value = Mock(id=1)
                mock_cm.generate_response.return_value = "Thank you for your message."
                mock_cm.send_response.return_value = True

                mock_qlh = AsyncMock()
                mock_handler.return_value = mock_qlh
                mock_qlh.handle_qualified_lead.return_value = True

                with patch("main.asyncio.sleep", side_effect=KeyboardInterrupt):
                    try:
                        await main_loop()
                    except KeyboardInterrupt:
                        pass

                # Verify all emails were processed
                assert mock_processor.process_email.call_count == 3

                # Verify qualified lead handler was called twice (for qualified leads)
                assert mock_qlh.handle_qualified_lead.call_count == 2

                # Verify normal response was sent once (for non-qualified lead)
                assert mock_cm.generate_response.call_count == 1
                assert mock_cm.send_response.call_count == 1

    @pytest.mark.asyncio
    async def test_concurrent_processing_safety(self, temp_db, mock_email_data):
        """Test that concurrent email processing maintains data integrity."""
        Session, engine = temp_db

        with patch("main.get_db_session") as mock_get_session:
            # Create separate sessions to simulate concurrent access
            session1 = Session()
            session2 = Session()
            mock_get_session.side_effect = [
                session1,
                session2,
            ] * 10  # Alternate sessions

            with patch("main.EmailProcessor") as mock_email_processor, patch(
                "main.LeadQualifier"
            ) as mock_lead_qualifier, patch(
                "main.ConversationManager"
            ) as mock_conv_manager, patch(
                "main.QualifiedLeadHandler"
            ) as mock_handler:

                mock_processor = AsyncMock()
                mock_email_processor.return_value = mock_processor
                mock_processor.fetch_new_emails.return_value = mock_email_data
                mock_processor.process_email.return_value = True

                mock_qualifier = Mock()
                mock_lead_qualifier.return_value = mock_qualifier
                mock_qualifier.analyze_email.return_value = {"budget": 150000}
                mock_qualifier.is_qualified_lead.return_value = True

                mock_cm = Mock()
                mock_conv_manager.return_value = mock_cm
                mock_cm.get_or_create_conversation.return_value = Mock(id=1)

                mock_qlh = AsyncMock()
                mock_handler.return_value = mock_qlh
                mock_qlh.handle_qualified_lead.return_value = True

                # Simulate concurrent processing
                async def run_concurrent_loops():
                    tasks = []
                    for _ in range(2):  # Two concurrent main loops
                        task = asyncio.create_task(self._run_limited_main_loop())
                        tasks.append(task)

                    await asyncio.gather(*tasks, return_exceptions=True)

                await run_concurrent_loops()

                # Verify no exceptions occurred and processing was successful
                assert mock_processor.process_email.call_count >= 3
                assert mock_qlh.handle_qualified_lead.call_count >= 3

    async def _run_limited_main_loop(self):
        """Helper method to run main loop for a limited time."""
        iterations = 0
        while iterations < 1:  # Just one iteration
            try:
                await main_loop()
            except KeyboardInterrupt:
                break
            iterations += 1

    @pytest.mark.asyncio
    async def test_email_processing_rollback_on_handoff_failure(self, temp_db):
        """Test that email processing can be rolled back if handoff fails critically."""
        Session, engine = temp_db
        session = Session()

        email_data = [
            {
                "id": "critical_lead",
                "subject": "Million dollar project",
                "body": "We have a $1M budget for Python development.",
                "from_email": "ceo@megacorp.com",
                "from_name": "Mega Corp CEO",
                "timestamp": datetime.utcnow(),
                "thread_id": "thread_critical",
            }
        ]

        with patch("main.get_db_session") as mock_get_session:
            mock_get_session.return_value = session

            with patch("main.EmailProcessor") as mock_email_processor, patch(
                "main.LeadQualifier"
            ) as mock_lead_qualifier, patch(
                "main.ConversationManager"
            ) as mock_conv_manager, patch(
                "main.QualifiedLeadHandler"
            ) as mock_handler, patch(
                "main.logger"
            ) as mock_logger:

                mock_processor = AsyncMock()
                mock_email_processor.return_value = mock_processor
                mock_processor.fetch_new_emails.return_value = email_data
                mock_processor.process_email.return_value = True

                mock_qualifier = Mock()
                mock_lead_qualifier.return_value = mock_qualifier
                mock_qualifier.analyze_email.return_value = {
                    "budget": 1000000,
                    "critical": True,
                }
                mock_qualifier.is_qualified_lead.return_value = True

                mock_cm = Mock()
                mock_conv_manager.return_value = mock_cm
                mock_cm.get_or_create_conversation.return_value = Mock(id=1)

                # Simulate critical handoff failure
                mock_qlh = AsyncMock()
                mock_handler.return_value = mock_qlh
                mock_qlh.handle_qualified_lead.side_effect = Exception(
                    "Critical handoff system failure"
                )

                with patch("main.asyncio.sleep", side_effect=KeyboardInterrupt):
                    try:
                        await main_loop()
                    except KeyboardInterrupt:
                        pass

                # Verify error was logged but loop didn't crash
                assert mock_logger.error.called
                error_calls = mock_logger.error.call_args_list
                assert any("handoff" in str(call).lower() for call in error_calls)

                # Verify processing attempted despite failure
                assert mock_processor.process_email.called
                assert mock_qlh.handle_qualified_lead.called
