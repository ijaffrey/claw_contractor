from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
import logging

from app.models.lead import Lead, LeadStatus
from app.models.user import User, UserRole
from app.models.notification import Notification, NotificationType
from app.services.notification_service import NotificationService
from app.services.ai_service import AIService
from app.extensions import db

logger = logging.getLogger(__name__)

qualification_bp = Blueprint('qualification', __name__, url_prefix='/api/qualification')

@qualification_bp.route('/leads/<int:lead_id>/qualify', methods=['POST'])
@jwt_required()
def qualify_lead(lead_id):
    """Qualify a lead with detailed assessment"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user or current_user.role not in [UserRole.ADMIN, UserRole.SALES_REP]:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        lead = Lead.query.get_or_404(lead_id)
        
        if lead.status not in [LeadStatus.NEW, LeadStatus.IN_PROGRESS]:
            return jsonify({'error': 'Lead cannot be qualified in current status'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        # Validate required fields
        required_fields = ['qualified', 'qualification_notes']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Update lead with qualification details
        lead.qualified = data['qualified']
        lead.qualification_notes = data['qualification_notes']
        lead.qualification_date = datetime.now(timezone.utc)
        lead.qualified_by_id = current_user_id
        
        # Update additional qualification fields if provided
        if 'budget_range' in data:
            lead.budget_range = data['budget_range']
        if 'timeline' in data:
            lead.timeline = data['timeline']
        if 'decision_maker' in data:
            lead.decision_maker = data['decision_maker']
        if 'project_scope' in data:
            lead.project_scope = data['project_scope']
        if 'priority_level' in data:
            lead.priority_level = data['priority_level']
        
        # Set next status based on qualification
        if data['qualified']:
            lead.status = LeadStatus.QUALIFIED
        else:
            lead.status = LeadStatus.UNQUALIFIED
        
        lead.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        # Log qualification action
        logger.info(f"Lead {lead_id} qualified by user {current_user_id} - Result: {'QUALIFIED' if data['qualified'] else 'UNQUALIFIED'}")
        
        return jsonify({
            'message': 'Lead qualified successfully',
            'lead': {
                'id': lead.id,
                'status': lead.status.value,
                'qualified': lead.qualified,
                'qualification_date': lead.qualification_date.isoformat() if lead.qualification_date else None,
                'qualification_notes': lead.qualification_notes,
                'qualified_by': {
                    'id': current_user.id,
                    'name': current_user.full_name,
                    'email': current_user.email
                }
            }
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error qualifying lead {lead_id}: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error qualifying lead {lead_id}: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@qualification_bp.route('/leads/<int:lead_id>/complete', methods=['POST'])
@jwt_required()
def complete_qualification(lead_id):
    """Complete qualification process with final handoff workflow"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user or current_user.role not in [UserRole.ADMIN, UserRole.SALES_REP]:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        lead = Lead.query.get_or_404(lead_id)
        
        if lead.status not in [LeadStatus.QUALIFIED, LeadStatus.UNQUALIFIED]:
            return jsonify({'error': 'Lead must be qualified or unqualified before completion'}), 400
        
        data = request.get_json() or {}
        
        notification_service = NotificationService()
        ai_service = AIService()
        
        notifications_sent = []
        
        # Generate lead summary using AI
        lead_summary = ai_service.generate_lead_summary(lead)
        lead.summary = lead_summary
        
        if lead.qualified:
            # Handle qualified lead path
            
            # 1. Find available contractors for notification
            contractors = User.query.filter_by(
                role=UserRole.CONTRACTOR,
                is_active=True
            ).all()
            
            # 2. Send contractor notifications
            for contractor in contractors:
                try:
                    notification_result = notification_service.send_contractor_notification(
                        contractor_id=contractor.id,
                        lead_id=lead.id,
                        lead_summary=lead_summary,
                        priority_level=getattr(lead, 'priority_level', 'medium')
                    )
                    
                    if notification_result.get('success'):
                        # Log notification in database
                        notification = Notification(
                            user_id=contractor.id,
                            type=NotificationType.LEAD_ASSIGNMENT,
                            title=f"New Qualified Lead: {lead.project_type or 'Project'}",
                            message=f"Lead #{lead.id} has been qualified and assigned. Budget: {lead.budget_range or 'TBD'}",
                            data={
                                'lead_id': lead.id,
                                'lead_summary': lead_summary,
                                'priority': getattr(lead, 'priority_level', 'medium'),
                                'timeline': getattr(lead, 'timeline', None)
                            },
                            sent_at=datetime.now(timezone.utc)
                        )
                        db.session.add(notification)
                        
                        notifications_sent.append({
                            'contractor_id': contractor.id,
                            'contractor_name': contractor.full_name,
                            'type': 'contractor_notification',
                            'status': 'sent',
                            'timestamp': datetime.now(timezone.utc).isoformat()
                        })
                        
                        logger.info(f"Contractor notification sent to {contractor.email} for lead {lead_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to send contractor notification to {contractor.email}: {str(e)}")
                    notifications_sent.append({
                        'contractor_id': contractor.id,
                        'contractor_name': contractor.full_name,
                        'type': 'contractor_notification',
                        'status': 'failed',
                        'error': str(e),
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    })
            
            # 3. Send customer handoff message (qualified path)
            try:
                customer_message = data.get('customer_message') or (
                    f"Great news! Your project inquiry has been qualified and we've notified our "
                    f"contractor network. You should expect to hear from qualified professionals "
                    f"within 24-48 hours. Lead ID: #{lead.id}"
                )
                
                handoff_result = notification_service.send_customer_handoff(
                    lead_id=lead.id,
                    customer_email=lead.email,
                    customer_name=lead.first_name,
                    message=customer_message,
                    qualified=True
                )
                
                if handoff_result.get('success'):
                    # Log customer notification
                    customer_notification = Notification(
                        user_id=None,  # Customer notifications don't have user_id
                        type=NotificationType.CUSTOMER_UPDATE,
                        title="Project Qualified - Contractors Notified",
                        message=customer_message,
                        data={
                            'lead_id': lead.id,
                            'customer_email': lead.email,
                            'qualified': True
                        },
                        sent_at=datetime.now(timezone.utc)
                    )
                    db.session.add(customer_notification)
                    
                    notifications_sent.append({
                        'recipient': lead.email,
                        'type': 'customer_handoff',
                        'status': 'sent',
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    })
                    
            except Exception as e:
                logger.error(f"Failed to send customer handoff for qualified lead {lead_id}: {str(e)}")
                notifications_sent.append({
                    'recipient': lead.email,
                    'type': 'customer_handoff',
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
        
        else:
            # Handle unqualified lead path
            
            # Send customer handoff message (unqualified path)
            try:
                customer_message = data.get('customer_message') or (
                    f"Thank you for your project inquiry. After review, we're unable to match "
                    f"your project with our current contractor network. We appreciate your interest "
                    f"and encourage you to reach out in the future. Lead ID: #{lead.id}"
                )
                
                handoff_result = notification_service.send_customer_handoff(
                    lead_id=lead.id,
                    customer_email=lead.email,
                    customer_name=lead.first_name,
                    message=customer_message,
                    qualified=False
                )
                
                if handoff_result.get('success'):
                    # Log customer notification
                    customer_notification = Notification(
                        user_id=None,
                        type=NotificationType.CUSTOMER_UPDATE,
                        title="Project Review Complete",
                        message=customer_message,
                        data={
                            'lead_id': lead.id,
                            'customer_email': lead.email,
                            'qualified': False
                        },
                        sent_at=datetime.now(timezone.utc)
                    )
                    db.session.add(customer_notification)
                    
                    notifications_sent.append({
                        'recipient': lead.email,
                        'type': 'customer_handoff',
                        'status': 'sent',
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    })
                    
            except Exception as e:
                logger.error(f"Failed to send customer handoff for unqualified lead {lead_id}: {str(e)}")
                notifications_sent.append({
                    'recipient': lead.email,
                    'type': 'customer_handoff',
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
        
        # 4. Update lead status to completed
        lead.status = LeadStatus.COMPLETED
        lead.completion_date = datetime.now(timezone.utc)
        lead.completed_by_id = current_user_id
        lead.updated_at = datetime.now(timezone.utc)
        
        # Save completion notes if provided
        if 'completion_notes' in data:
            lead.completion_notes = data['completion_notes']
        
        db.session.commit()
        
        logger.info(f"Lead {lead_id} completed by user {current_user_id} - "
                   f"Qualified: {lead.qualified}, Notifications sent: {len(notifications_sent)}")
        
        return jsonify({
            'message': 'Lead qualification completed successfully',
            'lead': {
                'id': lead.id,
                'status': lead.status.value,
                'qualified': lead.qualified,
                'completion_date': lead.completion_date.isoformat(),
                'summary': lead.summary,
                'completed_by': {
                    'id': current_user.id,
                    'name': current_user.full_name,
                    'email': current_user.email
                }
            },
            'notifications': {
                'total_sent': len([n for n in notifications_sent if n.get('status') == 'sent']),
                'total_failed': len([n for n in notifications_sent if n.get('status') == 'failed']),
                'details': notifications_sent
            }
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error completing qualification for lead {lead_id}: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error completing qualification for lead {lead_id}: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@qualification_bp.route('/leads/<int:lead_id>/status', methods=['GET'])
@jwt_required()
def get_qualification_status(lead_id):
    """Get detailed qualification status for a lead"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        lead = Lead.query.get_or_404(lead_id)
        
        # Build qualification status response
        qualification_status = {
            'lead_id': lead.id,
            'status': lead.status.value,
            'qualified': lead.qualified,
            'qualification_date': lead.qualification_date.isoformat() if lead.qualification_date else None,
            'completion_date': lead.completion_date.isoformat() if lead.completion_date else None,
            'qualification_notes': lead.qualification_notes,
            'completion_notes': getattr(lead, 'completion_notes', None),
            'summary': lead.summary
        }
        
        # Add qualification details if available
        if hasattr(lead, 'qualified_by_id') and lead.qualified_by_id:
            qualified_by = User.query.get(lead.qualified_by_id)
            if qualified_by:
                qualification_status['qualified_by'] = {
                    'id': qualified_by.id,
                    'name': qualified_by.full_name,
                    'email': qualified_by.email
                }
        
        if hasattr(lead, 'completed_by_id') and lead.completed_by_id:
            completed_by = User.query.get(lead.completed_by_id)
            if completed_by:
                qualification_status['completed_by'] = {
                    'id': completed_by.id,
                    'name': completed_by.full_name,
                    'email': completed_by.email
                }
        
        # Get related notifications
        notifications = Notification.query.filter(
            Notification.data.contains({'lead_id': lead_id})
        ).order_by(Notification.sent_at.desc()).all()
        
        qualification_status['notifications'] = [{
            'id': notif.id,
            'type': notif.type.value,
            'title': notif.title,
            'message': notif.message,
            'sent_at': notif.sent_at.isoformat() if notif.sent_at else None,
            'user_id': notif.user_id
        } for notif in notifications]
        
        return jsonify(qualification_status), 200
        
    except Exception as e:
        logger.error(f"Error getting qualification status for lead {lead_id}: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@qualification_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_qualification_stats():
    """Get qualification statistics"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user or current_user.role not in [UserRole.ADMIN, UserRole.SALES_REP]:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        # Calculate qualification statistics
        total_leads = Lead.query.count()
        qualified_leads = Lead.query.filter_by(qualified=True).count()
        unqualified_leads = Lead.query.filter_by(qualified=False).count()
        completed_leads = Lead.query.filter_by(status=LeadStatus.COMPLETED).count()
        
        # Get recent qualification activity
        recent_qualifications = Lead.query.filter(
            Lead.qualification_date.isnot(None)
        ).order_by(Lead.qualification_date.desc()).limit(10).all()
        
        stats = {
            'totals': {
                'total_leads': total_leads,
                'qualified_leads': qualified_leads,
                'unqualified_leads': unqualified_leads,
                'completed_leads': completed_leads,
                'pending_qualification': Lead.query.filter(
                    Lead.status.in_([LeadStatus.NEW, LeadStatus.IN_PROGRESS])
                ).count()
            },
            'rates': {
                'qualification_rate': (qualified_leads / total_leads * 100) if total_leads > 0 else 0,
                'completion_rate': (completed_leads / total_leads * 100) if total_leads > 0 else 0
            },
            'recent_activity': [{
                'id': lead.id,
                'qualified': lead.qualified,
                'qualification_date': lead.qualification_date.isoformat(),
                'customer_name': f"{lead.first_name} {lead.last_name}",
                'project_type': lead.project_type
            } for lead in recent_qualifications]
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting qualification stats: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500