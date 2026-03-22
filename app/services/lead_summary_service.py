from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from app.models.lead import Lead
from app.models.customer import Customer
from app.models.qualification_response import QualificationResponse
from app.models.photo_upload import PhotoUpload
from app.models.qualification_question import QualificationQuestion
from app.utils.file_storage import FileStorageManager
from app.database import get_db_session

logger = logging.getLogger(__name__)


class LeadSummaryService:
    """Service for generating comprehensive lead summaries."""
    
    def __init__(self):
        self.file_storage = FileStorageManager()
    
    def generate_lead_summary(self, lead_id: int) -> Dict[str, Any]:
        """
        Generate a comprehensive lead summary including customer info,
        qualification responses, photos, and status.
        
        Args:
            lead_id: The ID of the lead to summarize
            
        Returns:
            Dictionary containing formatted lead summary
            
        Raises:
            ValueError: If lead not found
            Exception: For database or processing errors
        """
        try:
            with get_db_session() as db:
                # Get lead with related data
                lead = self._get_lead_with_relations(db, lead_id)
                if not lead:
                    raise ValueError(f"Lead with ID {lead_id} not found")
                
                # Build comprehensive summary
                summary = {
                    "lead_id": lead.id,
                    "generated_at": datetime.utcnow().isoformat(),
                    "customer_info": self._format_customer_info(lead.customer),
                    "lead_details": self._format_lead_details(lead),
                    "qualification_data": self._format_qualification_data(db, lead),
                    "photo_gallery": self._format_photo_gallery(db, lead),
                    "timeline": self._format_timeline(lead),
                    "summary_stats": self._calculate_summary_stats(db, lead)
                }
                
                logger.info(f"Generated comprehensive summary for lead {lead_id}")
                return summary
                
        except Exception as e:
            logger.error(f"Error generating lead summary for {lead_id}: {str(e)}")
            raise
    
    def _get_lead_with_relations(self, db, lead_id: int) -> Optional[Lead]:
        """Get lead with all related data."""
        return db.query(Lead)\
                 .filter(Lead.id == lead_id)\
                 .first()
    
    def _format_customer_info(self, customer: Customer) -> Dict[str, Any]:
        """Format customer information section."""
        if not customer:
            return {}
        
        return {
            "customer_id": customer.id,
            "name": f"{customer.first_name} {customer.last_name}".strip(),
            "email": customer.email,
            "phone": customer.phone,
            "address": {
                "street": customer.address,
                "city": customer.city,
                "state": customer.state,
                "zip_code": customer.zip_code,
                "formatted": self._format_address(customer)
            },
            "customer_since": customer.created_at.isoformat() if customer.created_at else None,
            "total_leads": customer.leads.count() if hasattr(customer, 'leads') else 0
        }
    
    def _format_address(self, customer: Customer) -> str:
        """Format customer address as single string."""
        address_parts = [
            customer.address,
            customer.city,
            f"{customer.state} {customer.zip_code}".strip()
        ]
        return ", ".join(filter(None, address_parts))
    
    def _format_lead_details(self, lead: Lead) -> Dict[str, Any]:
        """Format lead-specific details."""
        return {
            "status": lead.status,
            "source": lead.source,
            "service_type": lead.service_type,
            "priority": lead.priority,
            "assigned_to": lead.assigned_to,
            "estimated_value": float(lead.estimated_value) if lead.estimated_value else None,
            "project_description": lead.description,
            "preferred_contact_time": lead.preferred_contact_time,
            "urgency_level": lead.urgency_level,
            "created_at": lead.created_at.isoformat() if lead.created_at else None,
            "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
            "follow_up_date": lead.follow_up_date.isoformat() if lead.follow_up_date else None
        }
    
    def _format_qualification_data(self, db, lead: Lead) -> Dict[str, Any]:
        """Format qualification responses and status."""
        try:
            # Get all qualification responses for this lead
            responses = db.query(QualificationResponse)\
                         .filter(QualificationResponse.lead_id == lead.id)\
                         .all()
            
            if not responses:
                return {
                    "status": "not_started",
                    "completion_percentage": 0,
                    "responses": [],
                    "qualified": False,
                    "score": 0
                }
            
            # Get all questions for context
            question_ids = [r.question_id for r in responses]
            questions_map = {}
            if question_ids:
                questions = db.query(QualificationQuestion)\
                             .filter(QualificationQuestion.id.in_(question_ids))\
                             .all()
                questions_map = {q.id: q for q in questions}
            
            # Format responses with question context
            formatted_responses = []
            total_score = 0
            max_possible_score = 0
            
            for response in responses:
                question = questions_map.get(response.question_id)
                if question:
                    response_data = {
                        "question_id": question.id,
                        "question_text": question.question_text,
                        "question_type": question.question_type,
                        "category": question.category,
                        "response_value": response.response_value,
                        "response_text": response.response_text,
                        "score": response.score or 0,
                        "max_score": question.max_score or 0,
                        "weight": question.weight or 1.0,
                        "answered_at": response.created_at.isoformat() if response.created_at else None
                    }
                    formatted_responses.append(response_data)
                    
                    if response.score:
                        total_score += response.score * (question.weight or 1.0)
                    if question.max_score:
                        max_possible_score += question.max_score * (question.weight or 1.0)
            
            # Calculate qualification metrics
            completion_percentage = self._calculate_completion_percentage(db, lead.id)
            qualification_score = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
            is_qualified = qualification_score >= 70  # 70% threshold
            
            return {
                "status": "completed" if completion_percentage == 100 else "in_progress",
                "completion_percentage": completion_percentage,
                "responses": sorted(formatted_responses, key=lambda x: x["question_id"]),
                "qualified": is_qualified,
                "score": round(qualification_score, 2),
                "total_points": total_score,
                "max_possible_points": max_possible_score,
                "response_count": len(responses)
            }
            
        except Exception as e:
            logger.error(f"Error formatting qualification data: {str(e)}")
            return {
                "status": "error",
                "completion_percentage": 0,
                "responses": [],
                "qualified": False,
                "score": 0,
                "error": str(e)
            }
    
    def _calculate_completion_percentage(self, db, lead_id: int) -> float:
        """Calculate what percentage of qualification questions have been answered."""
        try:
            # Count total available questions
            total_questions = db.query(QualificationQuestion)\
                               .filter(QualificationQuestion.is_active == True)\
                               .count()
            
            if total_questions == 0:
                return 0.0
            
            # Count answered questions for this lead
            answered_questions = db.query(QualificationResponse)\
                                  .filter(QualificationResponse.lead_id == lead_id)\
                                  .count()
            
            return round((answered_questions / total_questions) * 100, 2)
            
        except Exception as e:
            logger.error(f"Error calculating completion percentage: {str(e)}")
            return 0.0
    
    def _format_photo_gallery(self, db, lead: Lead) -> Dict[str, Any]:
        """Format uploaded photos with URLs and metadata."""
        try:
            photos = db.query(PhotoUpload)\
                      .filter(PhotoUpload.lead_id == lead.id)\
                      .order_by(PhotoUpload.created_at)\
                      .all()
            
            if not photos:
                return {
                    "total_photos": 0,
                    "photos": []
                }
            
            formatted_photos = []
            for photo in photos:
                try:
                    # Generate signed URL for photo access
                    photo_url = self.file_storage.get_signed_url(photo.file_path)
                    
                    photo_data = {
                        "id": photo.id,
                        "filename": photo.filename,
                        "url": photo_url,
                        "thumbnail_url": self._get_thumbnail_url(photo),
                        "file_size": photo.file_size,
                        "file_type": photo.file_type,
                        "description": photo.description,
                        "category": photo.category,
                        "uploaded_at": photo.created_at.isoformat() if photo.created_at else None,
                        "dimensions": {
                            "width": photo.width,
                            "height": photo.height
                        } if photo.width and photo.height else None
                    }
                    formatted_photos.append(photo_data)
                    
                except Exception as e:
                    logger.warning(f"Error processing photo {photo.id}: {str(e)}")
                    continue
            
            return {
                "total_photos": len(formatted_photos),
                "photos": formatted_photos,
                "categories": list(set(p.get("category") for p in formatted_photos if p.get("category")))
            }
            
        except Exception as e:
            logger.error(f"Error formatting photo gallery: {str(e)}")
            return {
                "total_photos": 0,
                "photos": [],
                "error": str(e)
            }
    
    def _get_thumbnail_url(self, photo: PhotoUpload) -> Optional[str]:
        """Get thumbnail URL if available."""
        if photo.thumbnail_path:
            try:
                return self.file_storage.get_signed_url(photo.thumbnail_path)
            except Exception as e:
                logger.warning(f"Error getting thumbnail URL: {str(e)}")
        return None
    
    def _format_timeline(self, lead: Lead) -> List[Dict[str, Any]]:
        """Create timeline of lead activities."""
        timeline_events = []
        
        # Lead creation
        if lead.created_at:
            timeline_events.append({
                "event_type": "lead_created",
                "timestamp": lead.created_at.isoformat(),
                "description": "Lead created",
                "details": {
                    "source": lead.source,
                    "service_type": lead.service_type
                }
            })
        
        # Status changes (would need status history table in real implementation)
        if lead.updated_at and lead.updated_at != lead.created_at:
            timeline_events.append({
                "event_type": "lead_updated",
                "timestamp": lead.updated_at.isoformat(),
                "description": "Lead information updated",
                "details": {
                    "current_status": lead.status
                }
            })
        
        # Add qualification and photo events (would need actual activity tracking)
        # This is simplified - in production you'd track all activities
        
        return sorted(timeline_events, key=lambda x: x["timestamp"], reverse=True)
    
    def _calculate_summary_stats(self, db, lead: Lead) -> Dict[str, Any]:
        """Calculate summary statistics."""
        try:
            # Count responses
            response_count = db.query(QualificationResponse)\
                              .filter(QualificationResponse.lead_id == lead.id)\
                              .count()
            
            # Count photos
            photo_count = db.query(PhotoUpload)\
                           .filter(PhotoUpload.lead_id == lead.id)\
                           .count()
            
            # Calculate days since creation
            days_active = 0
            if lead.created_at:
                days_active = (datetime.utcnow() - lead.created_at).days
            
            return {
                "qualification_responses": response_count,
                "photos_uploaded": photo_count,
                "days_since_creation": days_active,
                "estimated_value": float(lead.estimated_value) if lead.estimated_value else 0,
                "priority_level": lead.priority,
                "completion_status": self._get_completion_status(lead, response_count, photo_count)
            }
            
        except Exception as e:
            logger.error(f"Error calculating summary stats: {str(e)}")
            return {
                "qualification_responses": 0,
                "photos_uploaded": 0,
                "days_since_creation": 0,
                "estimated_value": 0,
                "completion_status": "unknown"
            }
    
    def _get_completion_status(self, lead: Lead, response_count: int, photo_count: int) -> str:
        """Determine overall completion status."""
        if lead.status == "closed_won" or lead.status == "closed_lost":
            return "closed"
        elif response_count > 0 and photo_count > 0:
            return "well_documented"
        elif response_count > 0:
            return "partially_qualified"
        elif photo_count > 0:
            return "photos_only"
        else:
            return "minimal_info"
    
    def export_lead_summary(self, lead_id: int, format_type: str = "json") -> Dict[str, Any]:
        """
        Export lead summary in specified format.
        
        Args:
            lead_id: The ID of the lead to export
            format_type: Export format ('json', 'pdf', 'csv')
            
        Returns:
            Dictionary with export data and metadata
        """
        summary = self.generate_lead_summary(lead_id)
        
        export_data = {
            "summary": summary,
            "export_format": format_type,
            "exported_at": datetime.utcnow().isoformat(),
            "export_id": f"lead_{lead_id}_{int(datetime.utcnow().timestamp())}"
        }
        
        if format_type == "pdf":
            # In production, you'd generate actual PDF
            export_data["pdf_url"] = f"/api/leads/{lead_id}/summary/pdf"
        elif format_type == "csv":
            # In production, you'd generate actual CSV
            export_data["csv_url"] = f"/api/leads/{lead_id}/summary/csv"
        
        return export_data