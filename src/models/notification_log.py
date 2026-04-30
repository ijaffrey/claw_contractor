from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum

from ..database.base import Base


class NotificationTypeEnum(enum.Enum):
    CONTRACTOR = "contractor"
    CUSTOMER = "customer"


class DeliveryStatusEnum(enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    notification_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

    lead_id = Column(
        UUID(as_uuid=True),
        ForeignKey("leads.lead_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    notification_type = Column(Enum(NotificationTypeEnum), nullable=False, index=True)

    recipient_email = Column(String(255), nullable=False, index=True)

    subject = Column(String(500), nullable=False)

    content = Column(Text, nullable=False)

    sent_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True
    )

    delivery_status = Column(
        Enum(DeliveryStatusEnum),
        nullable=False,
        default=DeliveryStatusEnum.PENDING,
        index=True,
    )

    error_message = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    lead = relationship("Lead", back_populates="notification_logs")

    def __repr__(self):
        return f"<NotificationLog(id={self.notification_id}, type={self.notification_type.value}, status={self.delivery_status.value})>"

    @property
    def is_delivered(self):
        """Check if notification was successfully delivered"""
        return self.delivery_status in [
            DeliveryStatusEnum.SENT,
            DeliveryStatusEnum.DELIVERED,
        ]

    @property
    def has_failed(self):
        """Check if notification delivery failed"""
        return self.delivery_status in [
            DeliveryStatusEnum.FAILED,
            DeliveryStatusEnum.BOUNCED,
        ]

    def mark_as_sent(self):
        """Mark notification as sent"""
        self.delivery_status = DeliveryStatusEnum.SENT
        self.sent_at = datetime.utcnow()
        self.error_message = None

    def mark_as_delivered(self):
        """Mark notification as delivered"""
        self.delivery_status = DeliveryStatusEnum.DELIVERED
        self.error_message = None

    def mark_as_failed(self, error_message: str):
        """Mark notification as failed with error message"""
        self.delivery_status = DeliveryStatusEnum.FAILED
        self.error_message = error_message

    def mark_as_bounced(self, error_message: str = None):
        """Mark notification as bounced"""
        self.delivery_status = DeliveryStatusEnum.BOUNCED
        if error_message:
            self.error_message = error_message
