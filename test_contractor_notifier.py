# W1-D skip sweep — see docs/W1D_RECONCILIATION_MANIFEST.md
# Reason: Pair 7 dissolution; imports phantom lead_management package
import pytest
pytest.skip("W1-D: Pair 7 dissolution; imports phantom lead_management package", allow_module_level=True)

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
import os
import tempfile
from lead_management.contractor_notifier import (
    ContractorNotifier,
    ContractorEmailGenerator,
    ContractorLookup,
    NotificationError,
    TemplateRenderError,
    ContractorNotFoundError,
)
from lead_management.email_sender import EmailSender, EmailConfig


class TestContractorEmailGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = ContractorEmailGenerator()
        self.sample_lead = {
            "id": "L123456",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@email.com",
            "phone": "555-0123",
            "service_type": "Plumbing",
            "description": "Leaky faucet in kitchen",
            "urgency": "High",
            "address": "123 Main St, Anytown, ST 12345",
            "preferred_contact_time": "Morning",
            "budget_range": "$100-500",
            "created_at": datetime.now().isoformat(),
            "source": "Website Form",
        }

    def test_generate_subject_line_standard_lead(self):
        subject = self.generator.generate_subject_line(self.sample_lead)
        expected = "New Plumbing Lead - L123456 - High Priority"
        self.assertEqual(subject, expected)

    def test_generate_subject_line_missing_urgency(self):
        lead = self.sample_lead.copy()
        del lead["urgency"]
        subject = self.generator.generate_subject_line(lead)
        expected = "New Plumbing Lead - L123456 - Standard Priority"
        self.assertEqual(subject, expected)

    def test_generate_subject_line_missing_service_type(self):
        lead = self.sample_lead.copy()
        del lead["service_type"]
        subject = self.generator.generate_subject_line(lead)
        expected = "New Service Lead - L123456 - High Priority"
        self.assertEqual(subject, expected)

    def test_format_lead_summary_complete_data(self):
        summary = self.generator.format_lead_summary(self.sample_lead)

        self.assertIn("Lead ID: L123456", summary)
        self.assertIn("Customer: John Doe", summary)
        self.assertIn("Contact: john.doe@email.com, 555-0123", summary)
        self.assertIn("Service: Plumbing", summary)
        self.assertIn("Description: Leaky faucet in kitchen", summary)
        self.assertIn("Address: 123 Main St, Anytown, ST 12345", summary)
        self.assertIn("Urgency: High", summary)
        self.assertIn("Budget: $100-500", summary)
        self.assertIn("Preferred Contact: Morning", summary)
        self.assertIn("Source: Website Form", summary)

    def test_format_lead_summary_minimal_data(self):
        minimal_lead = {
            "id": "L123456",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@email.com",
        }

        summary = self.generator.format_lead_summary(minimal_lead)

        self.assertIn("Lead ID: L123456", summary)
        self.assertIn("Customer: John Doe", summary)
        self.assertIn("Contact: john.doe@email.com", summary)
        self.assertIn("Service: Not specified", summary)
        self.assertIn("Urgency: Standard", summary)

    def test_format_lead_summary_html_escaping(self):
        lead_with_html = self.sample_lead.copy()
        lead_with_html["description"] = '<script>alert("test")</script>Broken pipe'
        lead_with_html["first_name"] = "John<script>"

        summary = self.generator.format_lead_summary(lead_with_html)

        self.assertNotIn("<script>", summary)
        self.assertIn("&lt;script&gt;", summary)

    def test_format_lead_summary_long_description(self):
        lead_with_long_desc = self.sample_lead.copy()
        lead_with_long_desc["description"] = "A" * 1000

        summary = self.generator.format_lead_summary(lead_with_long_desc)

        # Should truncate long descriptions
        self.assertTrue(len(summary) < 2000)

    def test_generate_email_content_text_format(self):
        content = self.generator.generate_email_content(
            self.sample_lead, contractor_name="Mike's Plumbing", format_type="text"
        )

        self.assertIn("Dear Mike's Plumbing", content)
        self.assertIn("Lead ID: L123456", content)
        self.assertIn("John Doe", content)
        self.assertNotIn("<html>", content)
        self.assertNotIn("<div>", content)

    def test_generate_email_content_html_format(self):
        content = self.generator.generate_email_content(
            self.sample_lead, contractor_name="Mike's Plumbing", format_type="html"
        )

        self.assertIn("<html>", content)
        self.assertIn("<div>", content)
        self.assertIn("Mike's Plumbing", content)
        self.assertIn("L123456", content)

    def test_generate_email_content_invalid_format(self):
        with self.assertRaises(ValueError):
            self.generator.generate_email_content(
                self.sample_lead,
                contractor_name="Test Contractor",
                format_type="invalid",
            )

    def test_generate_email_content_missing_contractor_name(self):
        with self.assertRaises(ValueError):
            self.generator.generate_email_content(
                self.sample_lead, contractor_name="", format_type="text"
            )


class TestContractorLookup(unittest.TestCase):
    def setUp(self):
        # Create temporary contractor database
        self.temp_dir = tempfile.mkdtemp()
        self.db_file = os.path.join(self.temp_dir, "contractors.json")

        self.contractor_data = {
            "contractors": [
                {
                    "id": "C001",
                    "name": "Mike's Plumbing",
                    "email": "mike@mikesplumbing.com",
                    "phone": "555-1000",
                    "services": ["Plumbing", "Water Heater Repair"],
                    "coverage_areas": ["12345", "12346"],
                    "rating": 4.8,
                    "active": True,
                },
                {
                    "id": "C002",
                    "name": "ElectriCorp",
                    "email": "contact@electricorp.com",
                    "phone": "555-2000",
                    "services": ["Electrical"],
                    "coverage_areas": ["12345", "12347"],
                    "rating": 4.6,
                    "active": True,
                },
                {
                    "id": "C003",
                    "name": "Inactive Contractor",
                    "email": "inactive@test.com",
                    "phone": "555-3000",
                    "services": ["Plumbing"],
                    "coverage_areas": ["12345"],
                    "rating": 4.0,
                    "active": False,
                },
            ]
        }

        with open(self.db_file, "w") as f:
            json.dump(self.contractor_data, f)

        self.lookup = ContractorLookup(self.db_file)

    def tearDown(self):
        if os.path.exists(self.db_file):
            os.unlink(self.db_file)
        os.rmdir(self.temp_dir)

    def test_find_contractors_by_service_and_area(self):
        contractors = self.lookup.find_contractors("Plumbing", "12345")

        self.assertEqual(len(contractors), 1)
        self.assertEqual(contractors[0]["name"], "Mike's Plumbing")
        self.assertTrue(contractors[0]["active"])

    def test_find_contractors_no_matches(self):
        contractors = self.lookup.find_contractors("HVAC", "12345")
        self.assertEqual(len(contractors), 0)

    def test_find_contractors_wrong_area(self):
        contractors = self.lookup.find_contractors("Plumbing", "99999")
        self.assertEqual(len(contractors), 0)

    def test_find_contractors_excludes_inactive(self):
        contractors = self.lookup.find_contractors("Plumbing", "12345")
        contractor_names = [c["name"] for c in contractors]

        self.assertIn("Mike's Plumbing", contractor_names)
        self.assertNotIn("Inactive Contractor", contractor_names)

    def test_find_contractors_sorted_by_rating(self):
        # Add another active plumbing contractor with lower rating
        self.contractor_data["contractors"].append(
            {
                "id": "C004",
                "name": "Budget Plumbing",
                "email": "budget@plumbing.com",
                "phone": "555-4000",
                "services": ["Plumbing"],
                "coverage_areas": ["12345"],
                "rating": 4.2,
                "active": True,
            }
        )

        with open(self.db_file, "w") as f:
            json.dump(self.contractor_data, f)

        lookup = ContractorLookup(self.db_file)
        contractors = lookup.find_contractors("Plumbing", "12345")

        self.assertEqual(len(contractors), 2)
        self.assertEqual(
            contractors[0]["name"], "Mike's Plumbing"
        )  # Higher rating first
        self.assertEqual(contractors[1]["name"], "Budget Plumbing")

    def test_get_contractor_by_id_success(self):
        contractor = self.lookup.get_contractor_by_id("C001")

        self.assertIsNotNone(contractor)
        self.assertEqual(contractor["name"], "Mike's Plumbing")

    def test_get_contractor_by_id_not_found(self):
        with self.assertRaises(ContractorNotFoundError):
            self.lookup.get_contractor_by_id("INVALID")

    def test_extract_zip_code_from_full_address(self):
        address = "123 Main St, Anytown, ST 12345"
        zip_code = self.lookup.extract_zip_code(address)
        self.assertEqual(zip_code, "12345")

    def test_extract_zip_code_from_zip_only(self):
        address = "12345"
        zip_code = self.lookup.extract_zip_code(address)
        self.assertEqual(zip_code, "12345")

    def test_extract_zip_code_invalid_format(self):
        zip_code = self.lookup.extract_zip_code("Invalid Address")
        self.assertIsNone(zip_code)

    def test_database_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            ContractorLookup("nonexistent_file.json")

    def test_invalid_json_format(self):
        invalid_file = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_file, "w") as f:
            f.write("invalid json content")

        with self.assertRaises(json.JSONDecodeError):
            ContractorLookup(invalid_file)


class TestContractorNotifier(unittest.TestCase):
    def setUp(self):
        self.mock_email_sender = Mock(spec=EmailSender)
        self.mock_contractor_lookup = Mock(spec=ContractorLookup)
        self.mock_email_generator = Mock(spec=ContractorEmailGenerator)

        self.notifier = ContractorNotifier(
            email_sender=self.mock_email_sender,
            contractor_lookup=self.mock_contractor_lookup,
            email_generator=self.mock_email_generator,
        )

        self.sample_lead = {
            "id": "L123456",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@email.com",
            "phone": "555-0123",
            "service_type": "Plumbing",
            "description": "Leaky faucet",
            "address": "123 Main St, Anytown, ST 12345",
            "urgency": "High",
        }

        self.sample_contractors = [
            {
                "id": "C001",
                "name": "Mike's Plumbing",
                "email": "mike@mikesplumbing.com",
                "services": ["Plumbing"],
                "active": True,
            },
            {
                "id": "C002",
                "name": "Joe's Plumbing",
                "email": "joe@joesplumbing.com",
                "services": ["Plumbing"],
                "active": True,
            },
        ]

    def test_notify_contractors_success(self):
        # Setup mocks
        self.mock_contractor_lookup.extract_zip_code.return_value = "12345"
        self.mock_contractor_lookup.find_contractors.return_value = (
            self.sample_contractors
        )
        self.mock_email_generator.generate_subject_line.return_value = "New Lead"
        self.mock_email_generator.generate_email_content.return_value = "Email content"
        self.mock_email_sender.send_email.return_value = True

        result = self.notifier.notify_contractors(self.sample_lead)

        self.assertEqual(result["total_contractors"], 2)
        self.assertEqual(result["successful_notifications"], 2)
        self.assertEqual(result["failed_notifications"], 0)
        self.assertEqual(len(result["notification_details"]), 2)

        # Verify method calls
        self.mock_contractor_lookup.find_contractors.assert_called_once_with(
            "Plumbing", "12345"
        )
        self.assertEqual(self.mock_email_sender.send_email.call_count, 2)

    def test_notify_contractors_no_contractors_found(self):
        self.mock_contractor_lookup.extract_zip_code.return_value = "12345"
        self.mock_contractor_lookup.find_contractors.return_value = []

        result = self.notifier.notify_contractors(self.sample_lead)

        self.assertEqual(result["total_contractors"], 0)
        self.assertEqual(result["successful_notifications"], 0)
        self.assertEqual(result["failed_notifications"], 0)
        self.assertEqual(len(result["notification_details"]), 0)

    def test_notify_contractors_partial_failure(self):
        self.mock_contractor_lookup.extract_zip_code.return_value = "12345"
        self.mock_contractor_lookup.find_contractors.return_value = (
            self.sample_contractors
        )
        self.mock_email_generator.generate_subject_line.return_value = "New Lead"
        self.mock_email_generator.generate_email_content.return_value = "Email content"

        # First email succeeds, second fails
        self.mock_email_sender.send_email.side_effect = [True, False]

        result = self.notifier.notify_contractors(self.sample_lead)

        self.assertEqual(result["total_contractors"], 2)
        self.assertEqual(result["successful_notifications"], 1)
        self.assertEqual(result["failed_notifications"], 1)

        # Check notification details
        details = result["notification_details"]
        self.assertTrue(details[0]["success"])
        self.assertFalse(details[1]["success"])

    def test_notify_contractors_email_generation_failure(self):
        self.mock_contractor_lookup.extract_zip_code.return_value = "12345"
        self.mock_contractor_lookup.find_contractors.return_value = (
            self.sample_contractors
        )
        self.mock_email_generator.generate_subject_line.side_effect = Exception(
            "Template error"
        )

        result = self.notifier.notify_contractors(self.sample_lead)

        self.assertEqual(result["successful_notifications"], 0)
        self.assertEqual(result["failed_notifications"], 2)

        for detail in result["notification_details"]:
            self.assertFalse(detail["success"])
            self.assertIn("Template error", detail["error"])

    def test_notify_contractors_invalid_address(self):
        lead_with_invalid_address = self.sample_lead.copy()
        lead_with_invalid_address["address"] = "Invalid Address"

        self.mock_contractor_lookup.extract_zip_code.return_value = None

        with self.assertRaises(NotificationError):
            self.notifier.notify_contractors(lead_with_invalid_address)

    def test_notify_contractors_missing_service_type(self):
        lead_without_service = self.sample_lead.copy()
        del lead_without_service["service_type"]

        with self.assertRaises(NotificationError):
            self.notifier.notify_contractors(lead_without_service)

    def test_notify_contractors_rate_limiting(self):
        # Test with many contractors to check rate limiting
        many_contractors = [
            {
                "id": f"C{i:03d}",
                "name": f"Contractor {i}",
                "email": f"contractor{i}@test.com",
                "services": ["Plumbing"],
                "active": True,
            }
            for i in range(1, 11)  # 10 contractors
        ]

        self.mock_contractor_lookup.extract_zip_code.return_value = "12345"
        self.mock_contractor_lookup.find_contractors.return_value = many_contractors
        self.mock_email_generator.generate_subject_line.return_value = "New Lead"
        self.mock_email_generator.generate_email_content.return_value = "Email content"
        self.mock_email_sender.send_email.return_value = True

        with patch("time.sleep") as mock_sleep:
            result = self.notifier.notify_contractors(
                self.sample_lead, max_contractors=5
            )

            self.assertEqual(result["total_contractors"], 5)  # Should limit to 5
            self.assertEqual(self.mock_email_sender.send_email.call_count, 5)
            # Should have rate limiting delays
            self.assertTrue(
                mock_sleep.call_count >= 4
            )  # At least 4 delays between 5 emails

    def test_notify_single_contractor_success(self):
        contractor = self.sample_contractors[0]

        self.mock_email_generator.generate_subject_line.return_value = "New Lead"
        self.mock_email_generator.generate_email_content.return_value = "Email content"
        self.mock_email_sender.send_email.return_value = True

        result = self.notifier.notify_single_contractor(
            self.sample_lead, contractor["id"]
        )

        self.assertTrue(result["success"])
        self.assertIsNone(result.get("error"))

    def test_notify_single_contractor_not_found(self):
        self.mock_contractor_lookup.get_contractor_by_id.side_effect = (
            ContractorNotFoundError("Not found")
        )

        result = self.notifier.notify_single_contractor(self.sample_lead, "INVALID")

        self.assertFalse(result["success"])
        self.assertIn("Not found", result["error"])

    def test_notify_single_contractor_email_failure(self):
        contractor = self.sample_contractors[0]

        self.mock_contractor_lookup.get_contractor_by_id.return_value = contractor
        self.mock_email_generator.generate_subject_line.return_value = "New Lead"
        self.mock_email_generator.generate_email_content.return_value = "Email content"
        self.mock_email_sender.send_email.return_value = False

        result = self.notifier.notify_single_contractor(
            self.sample_lead, contractor["id"]
        )

        self.assertFalse(result["success"])
        self.assertIn("Failed to send email", result["error"])


class TestIntegrationWithEmailSender(unittest.TestCase):
    def setUp(self):
        # Create a real email sender with mock SMTP
        self.email_config = EmailConfig(
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="password",
            use_tls=True,
        )

    @patch("smtplib.SMTP")
    def test_end_to_end_notification_success(self, mock_smtp_class):
        # Setup mock SMTP
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp
        mock_smtp.starttls.return_value = None
        mock_smtp.login.return_value = None
        mock_smtp.send_message.return_value = {}

        # Create real EmailSender
        email_sender = EmailSender(self.email_config)

        # Create temporary contractor database
        temp_dir = tempfile.mkdtemp()
        db_file = os.path.join(temp_dir, "contractors.json")

        contractor_data = {
            "contractors": [
                {
                    "id": "C001",
                    "name": "Test Contractor",
                    "email": "contractor@test.com",
                    "services": ["Plumbing"],
                    "coverage_areas": ["12345"],
                    "rating": 4.5,
                    "active": True,
                }
            ]
        }

        with open(db_file, "w") as f:
            json.dump(contractor_data, f)

        try:
            # Create real components
            contractor_lookup = ContractorLookup(db_file)
            email_generator = ContractorEmailGenerator()

            notifier = ContractorNotifier(
                email_sender=email_sender,
                contractor_lookup=contractor_lookup,
                email_generator=email_generator,
            )

            # Test notification
            lead = {
                "id": "L123456",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@test.com",
                "service_type": "Plumbing",
                "address": "123 Main St, Test, ST 12345",
                "description": "Test job",
                "urgency": "High",
            }

            result = notifier.notify_contractors(lead)

            # Verify results
            self.assertEqual(result["total_contractors"], 1)
            self.assertEqual(result["successful_notifications"], 1)
            self.assertEqual(result["failed_notifications"], 0)

            # Verify SMTP was called
            mock_smtp.starttls.assert_called_once()
            mock_smtp.login.assert_called_once_with("test@test.com", "password")
            mock_smtp.send_message.assert_called_once()

        finally:
            os.unlink(db_file)
            os.rmdir(temp_dir)

    @patch("smtplib.SMTP")
    def test_end_to_end_notification_smtp_failure(self, mock_smtp_class):
        # Setup mock SMTP to fail
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp
        mock_smtp.send_message.side_effect = Exception("SMTP Error")

        email_sender = EmailSender(self.email_config)

        # Create temporary contractor database
        temp_dir = tempfile.mkdtemp()
        db_file = os.path.join(temp_dir, "contractors.json")

        contractor_data = {
            "contractors": [
                {
                    "id": "C001",
                    "name": "Test Contractor",
                    "email": "contractor@test.com",
                    "services": ["Plumbing"],
                    "coverage_areas": ["12345"],
                    "rating": 4.5,
                    "active": True,
                }
            ]
        }

        with open(db_file, "w") as f:
            json.dump(contractor_data, f)

        try:
            contractor_lookup = ContractorLookup(db_file)
            email_generator = ContractorEmailGenerator()

            notifier = ContractorNotifier(
                email_sender=email_sender,
                contractor_lookup=contractor_lookup,
                email_generator=email_generator,
            )

            lead = {
                "id": "L123456",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@test.com",
                "service_type": "Plumbing",
                "address": "123 Main St, Test, ST 12345",
                "description": "Test job",
            }

            result = notifier.notify_contractors(lead)

            # Should handle SMTP failure gracefully
            self.assertEqual(result["total_contractors"], 1)
            self.assertEqual(result["successful_notifications"], 0)
            self.assertEqual(result["failed_notifications"], 1)
            self.assertIn("SMTP Error", result["notification_details"][0]["error"])

        finally:
            os.unlink(db_file)
            os.rmdir(temp_dir)


class TestTemplateRendering(unittest.TestCase):
    def setUp(self):
        self.generator = ContractorEmailGenerator()

    def test_text_template_rendering(self):
        lead = {
            "id": "L123",
            "first_name": "John",
            "last_name": "Doe",
            "service_type": "Plumbing",
            "urgency": "High",
        }

        content = self.generator.generate_email_content(
            lead, contractor_name="Test Contractor", format_type="text"
        )

        # Check template structure
        lines = content.split("\n")
        self.assertTrue(any("Dear Test Contractor" in line for line in lines))
        self.assertTrue(any("L123" in line for line in lines))
        self.assertTrue(any("John Doe" in line for line in lines))

    def test_html_template_rendering(self):
        lead = {
            "id": "L123",
            "first_name": "John",
            "last_name": "Doe",
            "service_type": "Plumbing",
            "urgency": "High",
        }

        content = self.generator.generate_email_content(
            lead, contractor_name="Test Contractor", format_type="html"
        )

        # Check HTML structure
        self.assertIn("<html>", content)
        self.assertIn("<head>", content)
        self.assertIn("<body>", content)
        self.assertIn("Test Contractor", content)
        self.assertIn("L123", content)

    def test_template_special_characters(self):
        lead = {
            "id": "L123",
            "first_name": "José",
            "last_name": "García",
            "description": "Broken pipe & water damage",
            "service_type": "Plumbing",
        }

        content = self.generator.generate_email_content(
            lead, contractor_name="Mike's Plumbing & Repair", format_type="html"
        )

        # Should handle special characters properly
        self.assertIn("José García", content)
        self.assertIn("Mike&#x27;s Plumbing &amp; Repair", content)
        self.assertIn("pipe &amp; water", content)

    def test_template_empty_fields(self):
        lead = {"id": "L123", "first_name": "John", "last_name": "Doe"}

        content = self.generator.generate_email_content(
            lead, contractor_name="Test Contractor", format_type="text"
        )

        # Should handle missing fields gracefully
        self.assertIn("Service: Not specified", content)
        self.assertIn("Urgency: Standard", content)


if __name__ == "__main__":
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestContractorEmailGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestContractorLookup))
    suite.addTests(loader.loadTestsFromTestCase(TestContractorNotifier))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationWithEmailSender))
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateRendering))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
