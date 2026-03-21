from datetime import datetime
import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from src.database.base import Base


class NotificationType(enum.Enum):
    contractor_notification = "contractor_notification"
    customer_handoff = "customer_handoff"
    status_update = "status_update"


class NotificationStatus(enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    notification_type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    recipient_email = Column(String(255), nullable=False, index=True)
    subject = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    status = Column(SQLEnum(NotificationStatus), nullable=False, default=NotificationStatus.pending, index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    lead = relationship("Lead", back_populates="notification_logs")

    def __repr__(self):
        return f"<NotificationLog(id={self.id}, lead_id={self.lead_id}, type={self.notification_type.value}, status={self.status.value})>"

    def mark_as_sent(self):
        """Mark the notification as successfully sent."""
        self.status = NotificationStatus.sent
        self.sent_at = datetime.utcnow()
        self.error_message = None

    def mark_as_failed(self, error_message: str):
        """Mark the notification as failed with error message."""
        self.status = NotificationStatus.failed
        self.error_message = error_message
        self.sent_at = None