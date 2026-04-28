from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from src.database.base import Base


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    notification_type = Column(String(50), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    message_content = Column(Text, nullable=True)

    # Relationships
    lead = relationship("Lead", back_populates="notification_logs")

    # Indexes for efficient querying
    __table_args__ = (
        Index("idx_notification_type", "notification_type"),
        Index("idx_recipient_email", "recipient_email"),
        Index("idx_lead_id", "lead_id"),
        Index("idx_status", "status"),
        Index("idx_timestamp", "timestamp"),
        Index("idx_notification_type_status", "notification_type", "status"),
        Index("idx_recipient_email_timestamp", "recipient_email", "timestamp"),
        Index("idx_lead_id_timestamp", "lead_id", "timestamp"),
    )

    def __repr__(self):
        return f"<NotificationLog(id={self.id}, type='{self.notification_type}', recipient='{self.recipient_email}', status='{self.status}')>"

    def to_dict(self):
        return {
            "id": self.id,
            "notification_type": self.notification_type,
            "recipient_email": self.recipient_email,
            "lead_id": self.lead_id,
            "status": self.status,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "message_content": self.message_content,
        }
