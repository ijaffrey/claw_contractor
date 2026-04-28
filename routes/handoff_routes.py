from flask import Blueprint, request, jsonify
from src.services.handoff_service import HandoffService
from src.services.auth_service import AuthService
from src.models.lead import Lead
from src.utils.validators import validate_uuid
from src.utils.response_formatter import format_success_response, format_error_response
from src.utils.logger import get_logger
from functools import wraps
import traceback

logger = get_logger(__name__)

handoff_bp = Blueprint("handoff", __name__, url_prefix="/api/leads")


def require_auth(f):
    """Decorator to require authentication for routes"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return (
                format_error_response("Missing or invalid authorization header", 401),
                401,
            )

        token = auth_header.split(" ")[1]
        user = AuthService.verify_token(token)
        if not user:
            return format_error_response("Invalid or expired token", 401), 401

        request.current_user = user
        return f(*args, **kwargs)

    return decorated_function


@handoff_bp.route("/<lead_id>/process-handoff", methods=["POST"])
@require_auth
def process_handoff(lead_id):
    """
    Process handoff workflow for a lead

    Triggers qualification check, sends notifications, and updates lead status.

    Args:
        lead_id (str): UUID of the lead to process handoff for

    Returns:
        JSON response with handoff processing results
    """
    try:
        # Validate lead ID format
        if not validate_uuid(lead_id):
            logger.warning(f"Invalid lead ID format: {lead_id}")
            return format_error_response("Invalid lead ID format", 400), 400

        # Get request data
        data = request.get_json() or {}

        # Extract optional parameters
        force_handoff = data.get("force_handoff", False)
        handoff_notes = data.get("notes", "")
        assigned_to = data.get("assigned_to")
        priority = data.get("priority", "normal")

        # Validate priority if provided
        valid_priorities = ["low", "normal", "high", "urgent"]
        if priority not in valid_priorities:
            logger.warning(f"Invalid priority value: {priority}")
            return (
                format_error_response(
                    f'Invalid priority. Must be one of: {", ".join(valid_priorities)}',
                    400,
                ),
                400,
            )

        # Validate assigned_to if provided
        if assigned_to and not validate_uuid(assigned_to):
            logger.warning(f"Invalid assigned_to ID format: {assigned_to}")
            return format_error_response("Invalid assigned_to ID format", 400), 400

        # Check if lead exists
        lead = Lead.get_by_id(lead_id)
        if not lead:
            logger.warning(f"Lead not found: {lead_id}")
            return format_error_response("Lead not found", 404), 404

        # Check if lead is already handed off
        if lead.status == "handed_off" and not force_handoff:
            logger.info(f"Lead {lead_id} already handed off")
            return (
                format_error_response(
                    "Lead has already been handed off. Use force_handoff=true to override.",
                    409,
                ),
                409,
            )

        # Process handoff
        logger.info(
            f"Processing handoff for lead {lead_id} by user {request.current_user.id}"
        )

        handoff_service = HandoffService()
        result = handoff_service.process_handoff(
            lead_id=lead_id,
            user_id=request.current_user.id,
            force_handoff=force_handoff,
            notes=handoff_notes,
            assigned_to=assigned_to,
            priority=priority,
        )

        if not result.success:
            logger.error(
                f"Handoff processing failed for lead {lead_id}: {result.error}"
            )
            return (
                format_error_response(result.error, result.status_code or 422),
                result.status_code or 422,
            )

        # Format success response
        response_data = {
            "lead_id": lead_id,
            "handoff_status": result.handoff_status,
            "qualification_result": result.qualification_result,
            "notifications_sent": result.notifications_sent,
            "updated_at": result.updated_at.isoformat() if result.updated_at else None,
            "assigned_to": result.assigned_to,
            "priority": result.priority,
            "next_actions": result.next_actions or [],
        }

        logger.info(f"Handoff processed successfully for lead {lead_id}")
        return (
            format_success_response(
                data=response_data, message="Handoff processed successfully"
            ),
            200,
        )

    except ValueError as e:
        logger.warning(
            f"Validation error processing handoff for lead {lead_id}: {str(e)}"
        )
        return format_error_response(f"Validation error: {str(e)}", 400), 400

    except PermissionError as e:
        logger.warning(
            f"Permission denied processing handoff for lead {lead_id}: {str(e)}"
        )
        return format_error_response(f"Permission denied: {str(e)}", 403), 403

    except Exception as e:
        logger.error(
            f"Unexpected error processing handoff for lead {lead_id}: {str(e)}"
        )
        logger.error(traceback.format_exc())
        return (
            format_error_response(
                "An unexpected error occurred while processing handoff", 500
            ),
            500,
        )


@handoff_bp.route("/<lead_id>/handoff-status", methods=["GET"])
@require_auth
def get_handoff_status(lead_id):
    """
    Get current handoff status for a lead

    Args:
        lead_id (str): UUID of the lead

    Returns:
        JSON response with handoff status information
    """
    try:
        # Validate lead ID format
        if not validate_uuid(lead_id):
            logger.warning(f"Invalid lead ID format: {lead_id}")
            return format_error_response("Invalid lead ID format", 400), 400

        # Check if lead exists
        lead = Lead.get_by_id(lead_id)
        if not lead:
            logger.warning(f"Lead not found: {lead_id}")
            return format_error_response("Lead not found", 404), 404

        # Get handoff status
        handoff_service = HandoffService()
        status_info = handoff_service.get_handoff_status(lead_id)

        response_data = {
            "lead_id": lead_id,
            "status": status_info.get("status"),
            "handed_off_at": status_info.get("handed_off_at"),
            "handed_off_by": status_info.get("handed_off_by"),
            "assigned_to": status_info.get("assigned_to"),
            "qualification_score": status_info.get("qualification_score"),
            "priority": status_info.get("priority"),
            "notes": status_info.get("notes"),
            "notification_history": status_info.get("notification_history", []),
        }

        return (
            format_success_response(
                data=response_data, message="Handoff status retrieved successfully"
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error retrieving handoff status for lead {lead_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return (
            format_error_response(
                "An unexpected error occurred while retrieving handoff status", 500
            ),
            500,
        )


@handoff_bp.route("/<lead_id>/retry-handoff", methods=["POST"])
@require_auth
def retry_handoff(lead_id):
    """
    Retry failed handoff process for a lead

    Args:
        lead_id (str): UUID of the lead to retry handoff for

    Returns:
        JSON response with retry results
    """
    try:
        # Validate lead ID format
        if not validate_uuid(lead_id):
            logger.warning(f"Invalid lead ID format: {lead_id}")
            return format_error_response("Invalid lead ID format", 400), 400

        # Check if lead exists
        lead = Lead.get_by_id(lead_id)
        if not lead:
            logger.warning(f"Lead not found: {lead_id}")
            return format_error_response("Lead not found", 404), 404

        # Check if lead has a failed handoff that can be retried
        if lead.handoff_status != "failed":
            logger.warning(f"Lead {lead_id} does not have a failed handoff to retry")
            return (
                format_error_response(
                    "Lead does not have a failed handoff to retry", 400
                ),
                400,
            )

        # Retry handoff
        logger.info(
            f"Retrying handoff for lead {lead_id} by user {request.current_user.id}"
        )

        handoff_service = HandoffService()
        result = handoff_service.retry_handoff(
            lead_id=lead_id, user_id=request.current_user.id
        )

        if not result.success:
            logger.error(f"Handoff retry failed for lead {lead_id}: {result.error}")
            return (
                format_error_response(result.error, result.status_code or 422),
                result.status_code or 422,
            )

        # Format success response
        response_data = {
            "lead_id": lead_id,
            "handoff_status": result.handoff_status,
            "retry_count": result.retry_count,
            "notifications_sent": result.notifications_sent,
            "updated_at": result.updated_at.isoformat() if result.updated_at else None,
        }

        logger.info(f"Handoff retry processed successfully for lead {lead_id}")
        return (
            format_success_response(
                data=response_data, message="Handoff retry processed successfully"
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error retrying handoff for lead {lead_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return (
            format_error_response(
                "An unexpected error occurred while retrying handoff", 500
            ),
            500,
        )


@handoff_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return format_error_response("Endpoint not found", 404), 404


@handoff_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return format_error_response("Method not allowed", 405), 405


@handoff_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return format_error_response("Internal server error", 500), 500
