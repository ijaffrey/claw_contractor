import json, sys, os

sys.path.insert(0, "/tmp/claw_contractor")
from sqlalchemy import Column, Integer, String, Float, Boolean, Text
from database import Base, get_db_session, create_database_engine


class Contractor(Base):
    __tablename__ = "contractors"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    company_name = Column(String(255))
    contact_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    specialties = Column(Text)
    service_areas = Column(Text)
    rating = Column(Float, default=5.0)
    active = Column(Boolean, default=True)
    notification_preferences = Column(Text)


engine = create_database_engine()
Base.metadata.create_all(bind=engine)

with get_db_session() as session:
    existing = (
        session.query(Contractor).filter(Contractor.email == "ian@skipp.ai").first()
    )
    if existing:
        print("Already exists — skipping")
    else:
        session.add(
            Contractor(
                company_name="Mikes Plumbing",
                contact_name="Mike",
                email="ian@skipp.ai",
                phone="718-555-0100",
                specialties=json.dumps(
                    ["plumbing", "emergency plumbing", "pipe repair"]
                ),
                service_areas=json.dumps(["Brooklyn", "Queens", "Manhattan", "NY"]),
                rating=5.0,
                active=True,
                notification_preferences=json.dumps(
                    {"minimum_lead_score": 60, "email_notifications": True}
                ),
            )
        )
        session.commit()
        print("Seeded Mikes Plumbing — ian@skipp.ai")
