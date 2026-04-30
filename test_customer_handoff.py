# W1-D skip sweep — see docs/W1D_RECONCILIATION_MANIFEST.md
# Reason: escalation #1 (handoff orchestrator) and #5 (test location); imports phantom models.lead, models.contractor, messaging
import pytest
pytest.skip("W1-D: escalation #1 (handoff orchestrator) and #5 (test location); imports phantom models.lead, models.contractor, messaging", allow_module_level=True)

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

from messaging.customer_handoff import (
    HandoffMessageGenerator,
    ContractorIntroduction,
    TimelineManager,
    PersonalizationEngine,
)
from models.lead import Lead
from models.contractor import Contractor
from messaging.reply_generator import ReplyGenerator


class TestHandoffMessageGenerator:

    @pytest.fixture
    def sample_lead(self):
        return Lead(
            id="lead_123",
            name="John Smith",
            email="john.smith@email.com",
            phone="+1234567890",
            project_type="kitchen_remodel",
            budget_range="15000-25000",
            timeline="2-4_weeks",
            location="San Francisco, CA",
            description="Looking to remodel my kitchen with modern appliances",
            preferences={
                "style": "modern",
                "materials": ["granite", "stainless_steel"],
            },
        )

    @pytest.fixture
    def sample_contractor(self):
        return Contractor(
            id="contractor_456",
            name="Mike Johnson",
            company="Bay Area Remodeling",
            specialties=["kitchen", "bathroom", "flooring"],
            rating=4.8,
            years_experience=12,
            location="San Francisco Bay Area",
            phone="+1987654321",
            email="mike@bayarearemodeling.com",
            certifications=["Licensed", "Insured", "Bonded"],
            portfolio_url="https://bayarearemodeling.com/portfolio",
        )

    @pytest.fixture
    def handoff_generator(self):
        return HandoffMessageGenerator()

    def test_generate_basic_handoff_message(
        self, handoff_generator, sample_lead, sample_contractor
    ):
        message = handoff_generator.generate_handoff_message(
            sample_lead, sample_contractor
        )

        assert message is not None
        assert isinstance(message, str)
        assert len(message) > 0
        assert sample_lead.name in message
        assert sample_contractor.name in message
        assert sample_contractor.company in message

    def test_handoff_message_structure(
        self, handoff_generator, sample_lead, sample_contractor
    ):
        message = handoff_generator.generate_handoff_message(
            sample_lead, sample_contractor
        )

        # Check for essential components
        assert "introduction" in message.lower() or "introduce" in message.lower()
        assert "contact" in message.lower()
        assert "project" in message.lower()
        assert sample_contractor.phone in message or sample_contractor.email in message

    def test_handoff_message_with_timeline(
        self, handoff_generator, sample_lead, sample_contractor
    ):
        message = handoff_generator.generate_handoff_message(
            sample_lead, sample_contractor, include_timeline=True
        )

        assert "timeline" in message.lower() or "schedule" in message.lower()
        assert "weeks" in message.lower()

    def test_handoff_message_with_budget_context(
        self, handoff_generator, sample_lead, sample_contractor
    ):
        message = handoff_generator.generate_handoff_message(
            sample_lead, sample_contractor, include_budget_context=True
        )

        assert (
            "budget" in message.lower()
            or "cost" in message.lower()
            or "investment" in message.lower()
        )

    def test_handoff_message_personalization(
        self, handoff_generator, sample_lead, sample_contractor
    ):
        # Test with specific project details
        sample_lead.description = "I want a luxury kitchen with marble countertops"
        sample_lead.preferences["materials"] = ["marble", "hardwood"]

        message = handoff_generator.generate_handoff_message(
            sample_lead, sample_contractor
        )

        assert "kitchen" in message.lower()
        # Should reference materials or luxury aspects
        assert any(
            material in message.lower()
            for material in ["marble", "luxury", "countertop"]
        )


class TestPersonalizationEngine:

    @pytest.fixture
    def personalization_engine(self):
        return PersonalizationEngine()

    @pytest.fixture
    def lead_kitchen_modern(self):
        return Lead(
            id="lead_kitchen",
            name="Sarah Wilson",
            project_type="kitchen_remodel",
            preferences={"style": "modern", "priority": "efficiency"},
            budget_range="20000-30000",
            description="Want a sleek, modern kitchen for entertaining",
        )

    @pytest.fixture
    def lead_bathroom_traditional(self):
        return Lead(
            id="lead_bathroom",
            name="Robert Brown",
            project_type="bathroom_remodel",
            preferences={"style": "traditional", "priority": "luxury"},
            budget_range="10000-15000",
            description="Classic bathroom renovation with vintage touches",
        )

    def test_personalize_by_project_type(
        self, personalization_engine, lead_kitchen_modern
    ):
        personalized_content = personalization_engine.personalize_content(
            "We specialize in {project_type} projects", lead_kitchen_modern
        )

        assert "kitchen" in personalized_content.lower()
        assert "remodel" in personalized_content.lower()

    def test_personalize_by_style_preferences(
        self, personalization_engine, lead_kitchen_modern
    ):
        personalized_content = personalization_engine.personalize_content(
            "Our {style} designs will perfectly match your vision", lead_kitchen_modern
        )

        assert "modern" in personalized_content.lower()

    def test_personalize_by_budget_range(
        self, personalization_engine, lead_kitchen_modern
    ):
        personalized_content = personalization_engine.personalize_content(
            "Within your budget range of {budget_range}", lead_kitchen_modern
        )

        assert "20000" in personalized_content or "20,000" in personalized_content
        assert "30000" in personalized_content or "30,000" in personalized_content

    def test_personalize_multiple_variables(
        self, personalization_engine, lead_bathroom_traditional
    ):
        template = "Hello {name}, we'd love to help with your {project_type} in a {style} style"
        personalized_content = personalization_engine.personalize_content(
            template, lead_bathroom_traditional
        )

        assert "Robert Brown" in personalized_content
        assert "bathroom" in personalized_content.lower()
        assert "traditional" in personalized_content.lower()

    def test_personalize_with_missing_data(self, personalization_engine):
        lead_incomplete = Lead(
            id="incomplete",
            name="Test User",
            project_type="kitchen_remodel",
            # Missing preferences and other fields
        )

        template = "Your {style} kitchen will be amazing"
        personalized_content = personalization_engine.personalize_content(
            template, lead_incomplete
        )

        # Should handle missing data gracefully
        assert personalized_content is not None
        assert len(personalized_content) > 0

    def test_extract_personalization_data(
        self, personalization_engine, lead_kitchen_modern
    ):
        data = personalization_engine.extract_personalization_data(lead_kitchen_modern)

        assert "name" in data
        assert "project_type" in data
        assert "style" in data
        assert "budget_range" in data
        assert data["name"] == "Sarah Wilson"
        assert data["style"] == "modern"


class TestContractorIntroduction:

    @pytest.fixture
    def contractor_intro(self):
        return ContractorIntroduction()

    @pytest.fixture
    def experienced_contractor(self):
        return Contractor(
            id="exp_contractor",
            name="Lisa Chen",
            company="Premium Renovations",
            years_experience=15,
            specialties=["luxury_kitchens", "custom_cabinetry"],
            certifications=["Licensed", "Insured", "NKBA Certified"],
            rating=4.9,
            completed_projects=200,
        )

    def test_format_basic_introduction(self, contractor_intro, experienced_contractor):
        introduction = contractor_intro.format_introduction(experienced_contractor)

        assert experienced_contractor.name in introduction
        assert experienced_contractor.company in introduction
        assert str(experienced_contractor.years_experience) in introduction

    def test_format_introduction_with_specialties(
        self, contractor_intro, experienced_contractor
    ):
        introduction = contractor_intro.format_introduction(
            experienced_contractor, include_specialties=True
        )

        assert "luxury" in introduction.lower() or "custom" in introduction.lower()
        assert "specializ" in introduction.lower() or "expert" in introduction.lower()

    def test_format_introduction_with_credentials(
        self, contractor_intro, experienced_contractor
    ):
        introduction = contractor_intro.format_introduction(
            experienced_contractor, include_credentials=True
        )

        assert "licensed" in introduction.lower()
        assert "insured" in introduction.lower()
        assert (
            "certified" in introduction.lower()
            or "certification" in introduction.lower()
        )

    def test_format_introduction_with_rating(
        self, contractor_intro, experienced_contractor
    ):
        introduction = contractor_intro.format_introduction(
            experienced_contractor, include_rating=True
        )

        assert "4.9" in introduction or "rating" in introduction.lower()
        assert "star" in introduction.lower() or "rated" in introduction.lower()

    def test_format_full_introduction(self, contractor_intro, experienced_contractor):
        introduction = contractor_intro.format_introduction(
            experienced_contractor,
            include_specialties=True,
            include_credentials=True,
            include_rating=True,
        )

        # Should include all components
        assert experienced_contractor.name in introduction
        assert experienced_contractor.company in introduction
        assert str(experienced_contractor.years_experience) in introduction
        assert "licensed" in introduction.lower()
        assert len(introduction) > 100  # Should be comprehensive

    def test_introduction_tone_professional(
        self, contractor_intro, experienced_contractor
    ):
        introduction = contractor_intro.format_introduction(
            experienced_contractor, tone="professional"
        )

        # Should avoid overly casual language
        assert "awesome" not in introduction.lower()
        assert "amazing" not in introduction.lower()
        assert len(introduction.split(".")) >= 2  # Multiple sentences

    def test_introduction_tone_friendly(self, contractor_intro, experienced_contractor):
        introduction = contractor_intro.format_introduction(
            experienced_contractor, tone="friendly"
        )

        assert introduction is not None
        assert len(introduction) > 0


class TestTimelineManager:

    @pytest.fixture
    def timeline_manager(self):
        return TimelineManager()

    def test_generate_timeline_message_immediate(self, timeline_manager):
        message = timeline_manager.generate_timeline_message("immediate")

        assert "immediate" in message.lower() or "urgent" in message.lower()
        assert "contact" in message.lower()

    def test_generate_timeline_message_standard(self, timeline_manager):
        message = timeline_manager.generate_timeline_message("2-4_weeks")

        assert "week" in message.lower()
        assert "2" in message and "4" in message

    def test_generate_timeline_message_flexible(self, timeline_manager):
        message = timeline_manager.generate_timeline_message("flexible")

        assert "flexible" in message.lower() or "convenient" in message.lower()

    def test_calculate_project_timeline(self, timeline_manager):
        # Test kitchen remodel timeline
        timeline = timeline_manager.calculate_project_timeline(
            "kitchen_remodel", "standard"
        )

        assert timeline is not None
        assert "weeks" in timeline.lower() or "days" in timeline.lower()

    def test_format_timeline_expectations(self, timeline_manager):
        expectations = timeline_manager.format_timeline_expectations(
            project_type="bathroom_remodel",
            requested_timeline="3-6_weeks",
            contractor_availability="2_weeks",
        )

        assert expectations is not None
        assert "bathroom" in expectations.lower()
        assert "week" in expectations.lower()

    def test_timeline_with_constraints(self, timeline_manager):
        constrained_timeline = timeline_manager.generate_timeline_message(
            "1_week", constraints=["permit_required", "material_delivery"]
        )

        assert "permit" in constrained_timeline.lower()
        assert "material" in constrained_timeline.lower()

    def test_realistic_timeline_adjustment(self, timeline_manager):
        adjusted_message = timeline_manager.adjust_timeline_reality(
            requested="1_week",
            realistic="3-4_weeks",
            project_type="full_kitchen_remodel",
        )

        assert (
            "realistic" in adjusted_message.lower()
            or "typically" in adjusted_message.lower()
        )
        assert "week" in adjusted_message.lower()


class TestHandoffReplyIntegration:

    @pytest.fixture
    def reply_generator(self):
        return Mock(spec=ReplyGenerator)

    @pytest.fixture
    def handoff_generator(self):
        return HandoffMessageGenerator()

    @pytest.fixture
    def integration_setup(self, handoff_generator, reply_generator):
        return {
            "handoff_generator": handoff_generator,
            "reply_generator": reply_generator,
        }

    @patch("messaging.reply_generator.ReplyGenerator")
    def test_handoff_triggers_reply_generation(
        self, mock_reply_gen, sample_lead, sample_contractor
    ):
        mock_reply_gen.return_value.generate_followup.return_value = (
            "Follow-up message generated"
        )

        handoff_gen = HandoffMessageGenerator(
            reply_generator=mock_reply_gen.return_value
        )

        result = handoff_gen.generate_handoff_with_followup(
            sample_lead, sample_contractor
        )

        assert "handoff_message" in result
        assert "followup_message" in result
        mock_reply_gen.return_value.generate_followup.assert_called_once()

    def test_handoff_message_context_passing(
        self, integration_setup, sample_lead, sample_contractor
    ):
        handoff_gen = integration_setup["handoff_generator"]
        reply_gen = integration_setup["reply_generator"]

        # Mock reply generator to capture context
        reply_gen.generate_reply.return_value = "Test reply"

        context = {
            "lead_id": sample_lead.id,
            "contractor_id": sample_contractor.id,
            "handoff_timestamp": datetime.now().isoformat(),
        }

        result = handoff_gen.generate_handoff_message(
            sample_lead, sample_contractor, context=context
        )

        assert result is not None

    @patch("messaging.customer_handoff.TimelineManager")
    def test_timeline_integration_with_replies(
        self, mock_timeline_manager, sample_lead, sample_contractor
    ):
        mock_timeline_manager.return_value.generate_timeline_message.return_value = (
            "Timeline: 2-3 weeks"
        )

        handoff_gen = HandoffMessageGenerator(
            timeline_manager=mock_timeline_manager.return_value
        )

        message = handoff_gen.generate_handoff_message(
            sample_lead, sample_contractor, include_timeline=True
        )

        mock_timeline_manager.return_value.generate_timeline_message.assert_called()
        assert message is not None

    def test_error_handling_in_integration(
        self, integration_setup, sample_lead, sample_contractor
    ):
        handoff_gen = integration_setup["handoff_generator"]
        reply_gen = integration_setup["reply_generator"]

        # Simulate reply generator failure
        reply_gen.generate_reply.side_effect = Exception("Reply generation failed")

        # Should handle the error gracefully
        try:
            result = handoff_gen.generate_handoff_message(
                sample_lead, sample_contractor
            )
            assert result is not None  # Should still generate handoff message
        except Exception as e:
            pytest.fail(
                f"Handoff generation should handle reply generator failures: {e}"
            )

    def test_handoff_message_validation(
        self, handoff_generator, sample_lead, sample_contractor
    ):
        message = handoff_generator.generate_handoff_message(
            sample_lead, sample_contractor
        )

        # Validate message structure and content
        assert len(message) >= 50  # Minimum length
        assert len(message) <= 2000  # Maximum length for readability
        assert message.count("\n") <= 10  # Not too many line breaks

        # Check for required elements
        required_elements = [
            sample_lead.name,
            sample_contractor.name,
            sample_contractor.company,
        ]

        for element in required_elements:
            assert element in message, f"Missing required element: {element}"

    def test_handoff_message_formatting(
        self, handoff_generator, sample_lead, sample_contractor
    ):
        message = handoff_generator.generate_handoff_message(
            sample_lead, sample_contractor
        )

        # Check basic formatting
        assert not message.startswith(" ")  # No leading whitespace
        assert not message.endswith(" ")  # No trailing whitespace
        assert "\n\n\n" not in message  # No excessive line breaks

        # Check for proper sentence structure
        sentences = [
            s.strip() for s in message.replace("\n", ". ").split(". ") if s.strip()
        ]
        assert len(sentences) >= 2  # At least 2 sentences

        for sentence in sentences:
            if sentence:  # Non-empty sentence
                assert sentence[0].isupper()  # Starts with capital letter


class TestHandoffMessageEdgeCases:

    @pytest.fixture
    def handoff_generator(self):
        return HandoffMessageGenerator()

    def test_handoff_with_minimal_lead_data(self, handoff_generator):
        minimal_lead = Lead(id="minimal", name="John Doe", project_type="general")

        minimal_contractor = Contractor(
            id="minimal_contractor", name="Jane Smith", company="Smith Construction"
        )

        message = handoff_generator.generate_handoff_message(
            minimal_lead, minimal_contractor
        )

        assert message is not None
        assert "John Doe" in message
        assert "Jane Smith" in message
        assert "Smith Construction" in message

    def test_handoff_with_special_characters_in_names(self, handoff_generator):
        special_lead = Lead(
            id="special",
            name="José María O'Connor-Smith",
            project_type="kitchen_remodel",
        )

        special_contractor = Contractor(
            id="special_contractor",
            name="François & Associates",
            company="L'Artisan Builders",
        )

        message = handoff_generator.generate_handoff_message(
            special_lead, special_contractor
        )

        assert "José María O'Connor-Smith" in message
        assert "François" in message or "L'Artisan" in message

    def test_handoff_with_long_descriptions(self, handoff_generator):
        verbose_lead = Lead(
            id="verbose",
            name="Detail Oriented Client",
            project_type="full_home_renovation",
            description="I want to completely renovate my 1950s ranch home including kitchen, all bathrooms, flooring throughout, new windows, updated electrical and plumbing, and modern HVAC system with smart home integration",
        )

        contractor = Contractor(
            id="contractor",
            name="Full Service Renovator",
            company="Complete Home Solutions",
        )

        message = handoff_generator.generate_handoff_message(verbose_lead, contractor)

        assert message is not None
        assert len(message) < 3000  # Should not be excessively long

    def test_handoff_message_consistency(
        self, handoff_generator, sample_lead, sample_contractor
    ):
        # Generate multiple messages to test consistency
        messages = []
        for _ in range(5):
            message = handoff_generator.generate_handoff_message(
                sample_lead, sample_contractor
            )
            messages.append(message)

        # All messages should contain core elements
        for message in messages:
            assert sample_lead.name in message
            assert sample_contractor.name in message
            assert sample_contractor.company in message

        # Messages should vary (not identical)
        assert len(set(messages)) > 1, "Messages should have some variation"
