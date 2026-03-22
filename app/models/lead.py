from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import enum
from datetime import datetime

Base = declarative_base()

class LeadStatus(enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    COMPLETED = "completed"

class LeadSource(enum.Enum):
    WEBSITE = "website"
    REFERRAL = "referral"
    SOCIAL_MEDIA = "social_media"
    EMAIL_CAMPAIGN = "email_campaign"
    COLD_CALL = "cold_call"
    TRADE_SHOW = "trade_show"
    ADVERTISEMENT = "advertisement"
    OTHER = "other"

class Lead(Base):
    __tablename__ = 'leads'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False, index=True)
    last_name = Column(String(100), nullable=False, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(20))
    company = Column(String(255))
    job_title = Column(String(255))
    status = Column(Enum(LeadStatus), default=LeadStatus.NEW, nullable=False, index=True)
    source = Column(Enum(LeadSource), nullable=True)
    value = Column(Integer, default=0)  # Expected deal value in cents
    probability = Column(Integer, default=0)  # Probability percentage (0-100)
    notes = Column(Text)
    assigned_to = Column(Integer, ForeignKey('users.id'), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_contacted = Column(DateTime(timezone=True))
    expected_close_date = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    assigned_user = relationship("User", back_populates="leads")
    activities = relationship("LeadActivity", back_populates="lead", cascade="all, delete-orphan")
    notification_logs = relationship("NotificationLog", back_populates="lead", cascade="all, delete-orphan")
    attachments = relationship("LeadAttachment", back_populates="lead", cascade="all, delete-orphan")

    # Valid status transitions mapping
    _STATUS_TRANSITIONS = {
        LeadStatus.NEW: [LeadStatus.CONTACTED, LeadStatus.QUALIFIED, LeadStatus.CLOSED_LOST],
        LeadStatus.CONTACTED: [LeadStatus.QUALIFIED, LeadStatus.CLOSED_LOST, LeadStatus.NEW],
        LeadStatus.QUALIFIED: [LeadStatus.PROPOSAL, LeadStatus.CLOSED_LOST, LeadStatus.CONTACTED],
        LeadStatus.PROPOSAL: [LeadStatus.NEGOTIATION, LeadStatus.CLOSED_LOST, LeadStatus.QUALIFIED],
        LeadStatus.NEGOTIATION: [LeadStatus.CLOSED_WON, LeadStatus.CLOSED_LOST, LeadStatus.PROPOSAL],
        LeadStatus.CLOSED_WON: [LeadStatus.COMPLETED],
        LeadStatus.CLOSED_LOST: [LeadStatus.NEW, LeadStatus.CONTACTED],
        LeadStatus.COMPLETED: []  # Terminal state
    }

    def __repr__(self):
        return f"<Lead(id={self.id}, email='{self.email}', status='{self.status.value}')>"

    @property
    def full_name(self):
        """Return the full name of the lead."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def display_name(self):
        """Return display name with company if available."""
        name = self.full_name
        if self.company:
            name += f" ({self.company})"
        return name

    @property
    def weighted_value(self):
        """Calculate weighted value based on probability."""
        if self.value and self.probability:
            return (self.value * self.probability) / 100
        return 0

    def can_transition_to(self, new_status):
        """Check if the lead can transition to the given status."""
        if not isinstance(new_status, LeadStatus):
            return False
        
        allowed_transitions = self._STATUS_TRANSITIONS.get(self.status, [])
        return new_status in allowed_transitions

    def transition_to(self, new_status, user_id=None, notes=None):
        """
        Transition the lead to a new status if valid.
        
        Args:
            new_status: The target LeadStatus
            user_id: ID of the user making the transition
            notes: Optional notes about the transition
            
        Returns:
            bool: True if transition was successful, False otherwise
            
        Raises:
            ValueError: If the transition is not valid
        """
        if not self.can_transition_to(new_status):
            raise ValueError(f"Cannot transition from {self.status.value} to {new_status.value}")
        
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        # Create activity log for status change
        if hasattr(self, '_sa_instance_state') and self._sa_instance_state.session:
            from .lead_activity import LeadActivity, ActivityType
            activity = LeadActivity(
                lead_id=self.id,
                activity_type=ActivityType.STATUS_CHANGE,
                description=f"Status changed from {old_status.value} to {new_status.value}",
                notes=notes,
                created_by=user_id
            )
            self._sa_instance_state.session.add(activity)
        
        return True

    def is_closed(self):
        """Check if the lead is in a closed state."""
        return self.status in [LeadStatus.CLOSED_WON, LeadStatus.CLOSED_LOST, LeadStatus.COMPLETED]

    def is_active_opportunity(self):
        """Check if the lead is an active sales opportunity."""
        return self.status in [
            LeadStatus.QUALIFIED, 
            LeadStatus.PROPOSAL, 
            LeadStatus.NEGOTIATION
        ] and self.is_active

    def get_stage_duration(self):
        """Get the duration in current stage in days."""
        if not self.updated_at:
            return 0
        
        delta = datetime.utcnow() - self.updated_at.replace(tzinfo=None)
        return delta.days

    def get_total_age(self):
        """Get the total age of the lead in days."""
        if not self.created_at:
            return 0
            
        delta = datetime.utcnow() - self.created_at.replace(tzinfo=None)
        return delta.days

    def update_last_contacted(self):
        """Update the last contacted timestamp to now."""
        self.last_contacted = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self):
        """Convert lead to dictionary representation."""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'company': self.company,
            'job_title': self.job_title,
            'status': self.status.value,
            'source': self.source.value if self.source else None,
            'value': self.value,
            'probability': self.probability,
            'weighted_value': self.weighted_value,
            'notes': self.notes,
            'assigned_to': self.assigned_to,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_contacted': self.last_contacted.isoformat() if self.last_contacted else None,
            'expected_close_date': self.expected_close_date.isoformat() if self.expected_close_date else None,
            'is_active': self.is_active,
            'stage_duration': self.get_stage_duration(),
            'total_age': self.get_total_age()
        }

    @classmethod
    def get_status_counts(cls, session, user_id=None):
        """Get count of leads by status."""
        query = session.query(cls.status, func.count(cls.id).label('count'))
        
        if user_id:
            query = query.filter(cls.assigned_to == user_id)
            
        query = query.filter(cls.is_active == True)
        return dict(query.group_by(cls.status).all())

    @classmethod
    def get_pipeline_value(cls, session, user_id=None):
        """Calculate total pipeline value."""
        query = session.query(func.sum(cls.value))
        
        if user_id:
            query = query.filter(cls.assigned_to == user_id)
            
        query = query.filter(
            cls.is_active == True,
            cls.status.in_([
                LeadStatus.QUALIFIED,
                LeadStatus.PROPOSAL,
                LeadStatus.NEGOTIATION
            ])
        )
        
        result = query.scalar()
        return result or 0