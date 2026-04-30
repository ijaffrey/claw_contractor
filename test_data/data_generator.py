#!/usr/bin/env python3
"""
Test Data Generator
Generates realistic test data for the lead management system
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid


class TestDataGenerator:
    """Generates realistic test data for various system components"""

    def __init__(self, seed: int = None):
        if seed:
            random.seed(seed)

        self.contractor_types = [
            "General Contractor",
            "Plumber",
            "Electrician",
            "HVAC Technician",
            "Roofer",
            "Flooring Specialist",
            "Painter",
            "Landscaper",
            "Handyman",
        ]

        self.service_types = [
            "Kitchen Renovation",
            "Bathroom Remodel",
            "Plumbing Repair",
            "Electrical Work",
            "Roofing",
            "Flooring Installation",
            "Interior Painting",
            "Landscaping",
            "Home Repair",
        ]

        self.lead_sources = ["Google", "Referral", "Facebook", "Website", "Yelp"]
        self.names = [
            "John Smith",
            "Jane Doe",
            "Mike Johnson",
            "Sarah Wilson",
            "David Brown",
        ]
        self.cities = ["Austin", "Dallas", "Houston", "San Antonio", "Fort Worth"]

    def generate_lead_data(self, count: int = 10) -> List[Dict[str, Any]]:
        """Generate realistic lead data"""
        leads = []
        for i in range(count):
            lead = {
                "id": str(uuid.uuid4()),
                "name": random.choice(self.names),
                "email": f"test{i}@example.com",
                "phone": f"555-{random.randint(1000, 9999)}",
                "address": f"{random.randint(100, 9999)} Main St, {random.choice(self.cities)}, TX",
                "service_requested": random.choice(self.service_types),
                "budget_range": random.choice(
                    ["$1000-$5000", "$5000-$10000", "$10000-$20000", "$20000+"]
                ),
                "timeline": random.choice(
                    ["ASAP", "1-2 weeks", "1 month", "2-3 months"]
                ),
                "description": f"Need help with {random.choice(self.service_types).lower()}",
                "source": random.choice(self.lead_sources),
                "created_at": (
                    datetime.now() - timedelta(days=random.randint(0, 30))
                ).isoformat(),
                "status": random.choice(["new", "contacted", "qualified", "converted"]),
                "qualification_score": random.randint(0, 100),
            }
            leads.append(lead)
        return leads

    def generate_contractor_data(self, count: int = 5) -> List[Dict[str, Any]]:
        """Generate realistic contractor data"""
        contractors = []
        for i in range(count):
            contractor = {
                "id": str(uuid.uuid4()),
                "business_name": f"Quality Contractors {i+1}",
                "contact_name": random.choice(self.names),
                "email": f"contractor{i+1}@example.com",
                "phone": f"555-{random.randint(1000, 9999)}",
                "services": random.sample(self.service_types, random.randint(2, 4)),
                "service_areas": random.sample(self.cities, random.randint(1, 3)),
                "rating": round(random.uniform(3.5, 5.0), 1),
                "years_experience": random.randint(1, 25),
                "license_number": f"LIC{random.randint(1000, 9999)}",
                "insurance_verified": random.choice([True, False]),
                "created_at": (
                    datetime.now() - timedelta(days=random.randint(30, 365))
                ).isoformat(),
                "status": "active",
            }
            contractors.append(contractor)
        return contractors

    def generate_email_data(self, count: int = 20) -> List[Dict[str, Any]]:
        """Generate realistic email data for testing"""
        emails = []
        for i in range(count):
            service = random.choice(self.service_types)
            email = {
                "id": str(uuid.uuid4()),
                "thread_id": str(uuid.uuid4()),
                "sender": f"test{i}@example.com",
                "recipient": "leads@yourcompany.com",
                "subject": f"Quote Request for {service}",
                "body": f"Hi, I need a quote for {service.lower()}. Please contact me.",
                "timestamp": (
                    datetime.now() - timedelta(days=random.randint(0, 7))
                ).isoformat(),
                "labels": (
                    ["INBOX", "IMPORTANT"] if random.random() < 0.3 else ["INBOX"]
                ),
                "is_read": random.choice([True, False]),
            }
            emails.append(email)
        return emails

    def save_to_json(self, data: Any, filename: str) -> None:
        """Save generated data to JSON file"""
        with open(f"test_data/{filename}", "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"Generated test data saved to test_data/{filename}")

    def generate_all_test_data(self) -> Dict[str, Any]:
        """Generate all types of test data"""
        print("Generating comprehensive test data...")

        data = {
            "leads": self.generate_lead_data(25),
            "contractors": self.generate_contractor_data(8),
            "emails": self.generate_email_data(50),
            "generated_at": datetime.now().isoformat(),
            "version": "1.0",
        }

        self.save_to_json(data, "complete_test_data.json")

        # Save individual datasets
        self.save_to_json(data["leads"], "test_leads.json")
        self.save_to_json(data["contractors"], "test_contractors.json")
        self.save_to_json(data["emails"], "test_emails.json")

        return data


if __name__ == "__main__":
    generator = TestDataGenerator(seed=42)  # Reproducible data
    generator.generate_all_test_data()
    print("✅ Test data generation complete!")
