"""
Conversation Manager Module
Handles multi-message qualification sequences for leads
"""

# Qualification sequence steps
QUALIFICATION_STEPS = {
    1: {
        'name': 'urgency',
        'description': 'Determine urgency level',
        'goal': 'Understand if this is emergency, soon, or planning ahead'
    },
    2: {
        'name': 'job_details',
        'description': 'Get job specifics',
        'goal': 'Collect more details about the problem/job'
    },
    3: {
        'name': 'location',
        'description': 'Get location/address',
        'goal': 'Get the service address'
    },
    4: {
        'name': 'photos',
        'description': 'Request photos',
        'goal': 'Ask customer to send photos of the issue'
    },
    5: {
        'name': 'availability',
        'description': 'Get availability windows',
        'goal': 'Understand what times/days work for the customer'
    },
    6: {
        'name': 'ready_for_contractor',
        'description': 'Send to contractor',
        'goal': 'Let customer know contractor will reach out directly'
    }
}


def get_step_info(step_number):
    """
    Get information about a qualification step

    Args:
        step_number: Step number (1-6)

    Returns:
        dict: Step information or None
    """
    return QUALIFICATION_STEPS.get(step_number)


def determine_next_step(lead, conversation_history, customer_reply):
    """
    Determine the next qualification step based on context

    Args:
        lead: Lead record from database
        conversation_history: List of conversation messages
        customer_reply: Latest reply from customer

    Returns:
        int: Next step number (or same step if info not collected)
    """
    current_step = lead.get('qualification_step', 1)

    # Step 1: Urgency
    if current_step == 1:
        # Check if customer mentioned urgency in their reply
        reply_lower = customer_reply.lower()
        urgency_keywords = {
            'emergency': ['emergency', 'urgent', 'asap', 'immediately', 'flooding', 'burst'],
            'soon': ['soon', 'today', 'tomorrow', 'this week', 'quickly', 'fast'],
            'planning': ['planning', 'estimate', 'quote', 'when you can', 'no rush', 'flexible']
        }

        # If they mentioned urgency, move to step 2
        for category, keywords in urgency_keywords.items():
            if any(keyword in reply_lower for keyword in keywords):
                return 2

        # Otherwise stay on step 1 and ask again
        return 1

    # Step 2: Job details
    elif current_step == 2:
        # If they provided details (response > 20 chars), move forward
        if len(customer_reply.strip()) > 20:
            return 3
        return 2

    # Step 3: Location
    elif current_step == 3:
        # Look for address indicators
        reply_lower = customer_reply.lower()
        address_indicators = ['street', 'st', 'ave', 'avenue', 'road', 'rd', 'drive', 'dr', 'lane', 'ln', 'boulevard', 'blvd']

        if any(indicator in reply_lower for indicator in address_indicators) or len(customer_reply.strip()) > 15:
            return 4
        return 3

    # Step 4: Photos
    elif current_step == 4:
        # Move to step 5 after asking for photos
        # (we'll assume they'll send photos or say they can't)
        return 5

    # Step 5: Availability
    elif current_step == 5:
        # If they mentioned times/days, move to final step
        reply_lower = customer_reply.lower()
        time_indicators = [
            'morning', 'afternoon', 'evening', 'monday', 'tuesday', 'wednesday', 'thursday',
            'friday', 'saturday', 'sunday', 'weekday', 'weekend', 'am', 'pm',
            'today', 'tomorrow', 'week', 'anytime', 'flexible'
        ]

        if any(indicator in reply_lower for indicator in time_indicators) or len(customer_reply.strip()) > 10:
            return 6
        return 5

    # Step 6: Ready for contractor
    elif current_step == 6:
        # Stay at step 6 - this is the final step
        return 6

    return current_step


def should_advance_step(current_step, customer_reply):
    """
    Simple helper to determine if we should advance based on reply content

    Args:
        current_step: Current qualification step
        customer_reply: Customer's message

    Returns:
        bool: True if we should advance to next step
    """
    # If reply is substantive (> 15 chars), usually advance
    if len(customer_reply.strip()) > 15:
        return True

    # For very short replies, stay on current step
    return False


def format_conversation_context(lead, conversation_history):
    """
    Format conversation history for the AI

    Args:
        lead: Lead record
        conversation_history: List of conversation messages

    Returns:
        str: Formatted conversation context
    """
    if not conversation_history:
        return "This is the first message in the conversation."

    context = "CONVERSATION HISTORY:\n"
    for msg in conversation_history:
        role = msg['role'].upper()
        message = msg['message']
        context += f"\n{role}: {message}\n"

    return context


def get_qualification_summary(lead, conversation_history):
    """
    Generate a summary of what we've learned so far

    Args:
        lead: Lead record
        conversation_history: List of conversation messages

    Returns:
        dict: Summary of collected information
    """
    summary = {
        'customer_name': lead.get('customer_name', 'Unknown'),
        'job_type': lead.get('job_type', 'Unknown'),
        'urgency': lead.get('urgency', 'Unknown'),
        'location': lead.get('location', 'Not provided'),
        'phone': lead.get('phone', 'Not provided'),
        'current_step': lead.get('qualification_step', 1),
        'total_messages': len(conversation_history)
    }

    return summary
