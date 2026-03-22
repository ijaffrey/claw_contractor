import re
from typing import Dict, Any, List, Optional
from datetime import datetime


def normalize_lead(flat_lead: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts a flat lead dictionary to the nested structure expected by qualified_lead_detector.
    
    Args:
        flat_lead: Dictionary with flat structure from lead_parser.py
        
    Returns:
        Dictionary with nested structure for qualified_lead_detector.py
    """
    if not isinstance(flat_lead, dict):
        raise ValueError("Input must be a dictionary")
    
    # Extract and parse location information
    location_info = parse_location_string(flat_lead.get('location', ''))
    
    # Map urgency from job_type and urgency fields
    urgency_level = map_urgency(
        flat_lead.get('job_type', ''),
        flat_lead.get('urgency', '')
    )
    
    # Format photos from attachments
    photos = format_photos(flat_lead.get('attachments', []))
    
    # Build normalized lead structure
    normalized_lead = {
        'contact_info': {
            'name': flat_lead.get('customer_name', '').strip() or 'Unknown',
            'email': flat_lead.get('customer_email', '').strip() or None,
            'phone': _clean_phone_number(flat_lead.get('phone', ''))
        },
        'location': {
            'address': location_info.get('address', ''),
            'city': location_info.get('city', ''),
            'zip_code': location_info.get('zip_code', '')
        },
        'problem_description': flat_lead.get('description', '').strip() or '',
        'photos': photos,
        'urgency': urgency_level,
        'source': flat_lead.get('source', 'unknown'),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return normalized_lead


def parse_location_string(location_str: str) -> Dict[str, str]:
    """
    Parses a location string to extract address, city, and zip code.
    
    Handles various formats:
    - "123 Main St, Anytown, CA 12345"
    - "456 Oak Ave, Some City 67890"
    - "789 Pine St, Another Town, 54321"
    - "City, State ZIP"
    
    Args:
        location_str: Raw location string
        
    Returns:
        Dictionary with parsed location components
    """
    if not location_str or not isinstance(location_str, str):
        return {'address': '', 'city': '', 'zip_code': ''}
    
    location_str = location_str.strip()
    
    # Initialize result
    result = {'address': '', 'city': '', 'zip_code': ''}
    
    # Extract ZIP code first (5 digits, optionally followed by dash and 4 digits)
    zip_pattern = r'\b(\d{5}(?:-\d{4})?)\b'
    zip_match = re.search(zip_pattern, location_str)
    if zip_match:
        result['zip_code'] = zip_match.group(1)
        location_str = location_str.replace(zip_match.group(0), '').strip()
    
    # Split remaining string by commas
    parts = [part.strip() for part in location_str.split(',') if part.strip()]
    
    if len(parts) >= 2:
        # First part is likely address, last part is likely city/state
        result['address'] = parts[0]
        result['city'] = parts[-1]
    elif len(parts) == 1:
        # Single part - could be city or address
        if any(word in parts[0].lower() for word in ['st', 'ave', 'rd', 'blvd', 'dr', 'ct', 'ln']):
            result['address'] = parts[0]
        else:
            result['city'] = parts[0]
    
    # Clean up city field - remove state abbreviations
    if result['city']:
        # Remove common state abbreviations from end
        state_pattern = r'\s+[A-Z]{2}\s*$'
        result['city'] = re.sub(state_pattern, '', result['city']).strip()
    
    return result


def map_urgency(job_type: str, urgency: str) -> str:
    """
    Maps job_type and urgency keywords to standardized urgency levels.
    
    Args:
        job_type: Type of job/service requested
        urgency: Urgency keywords or phrases
        
    Returns:
        Standardized urgency level: 'emergency', 'high', 'medium', or 'low'
    """
    # Combine both fields for analysis
    combined_text = f"{job_type or ''} {urgency or ''}".lower().strip()
    
    if not combined_text:
        return 'medium'  # Default urgency
    
    # Emergency keywords
    emergency_keywords = [
        'emergency', 'urgent', 'asap', 'immediately', 'now', 'flooding',
        'leak', 'burst', 'broken pipe', 'water damage', 'no heat',
        'no hot water', 'gas leak', 'electrical emergency'
    ]
    
    # High priority keywords
    high_keywords = [
        'high priority', 'soon', 'today', 'this week', 'important',
        'repair', 'fix', 'broken', 'not working', 'problem'
    ]
    
    # Low priority keywords
    low_keywords = [
        'estimate', 'quote', 'consultation', 'when convenient',
        'no rush', 'maintenance', 'routine', 'inspection',
        'next month', 'sometime'
    ]
    
    # Check for emergency
    if any(keyword in combined_text for keyword in emergency_keywords):
        return 'emergency'
    
    # Check for high priority
    if any(keyword in combined_text for keyword in high_keywords):
        return 'high'
    
    # Check for low priority
    if any(keyword in combined_text for keyword in low_keywords):
        return 'low'
    
    # Default to medium if no clear indicators
    return 'medium'


def format_photos(attachments: List[Any]) -> List[Dict[str, Any]]:
    """
    Converts attachments to standardized photos list format.
    
    Args:
        attachments: List of attachment objects/dictionaries
        
    Returns:
        List of photo dictionaries with url and timestamp
    """
    if not attachments or not isinstance(attachments, list):
        return []
    
    photos = []
    current_time = datetime.utcnow().isoformat()
    
    for attachment in attachments:
        if not attachment:
            continue
            
        photo_entry = {
            'url': '',
            'timestamp': current_time,
            'filename': '',
            'size': None,
            'type': ''
        }
        
        if isinstance(attachment, dict):
            photo_entry['url'] = attachment.get('url', '') or attachment.get('path', '')
            photo_entry['filename'] = attachment.get('filename', '') or attachment.get('name', '')
            photo_entry['size'] = attachment.get('size')
            photo_entry['type'] = attachment.get('type', '') or attachment.get('mime_type', '')
            
            # Use attachment timestamp if available
            if attachment.get('timestamp'):
                photo_entry['timestamp'] = attachment['timestamp']
                
        elif isinstance(attachment, str):
            # String could be URL or file path
            photo_entry['url'] = attachment
            photo_entry['filename'] = attachment.split('/')[-1] if '/' in attachment else attachment
        
        # Only add if we have a valid URL/path
        if photo_entry['url']:
            # Determine type from filename if not provided
            if not photo_entry['type'] and photo_entry['filename']:
                extension = photo_entry['filename'].lower().split('.')[-1]
                if extension in ['jpg', 'jpeg']:
                    photo_entry['type'] = 'image/jpeg'
                elif extension == 'png':
                    photo_entry['type'] = 'image/png'
                elif extension == 'gif':
                    photo_entry['type'] = 'image/gif'
                elif extension == 'pdf':
                    photo_entry['type'] = 'application/pdf'
            
            photos.append(photo_entry)
    
    return photos


def _clean_phone_number(phone: str) -> Optional[str]:
    """
    Cleans and validates a phone number string.
    
    Args:
        phone: Raw phone number string
        
    Returns:
        Cleaned phone number or None if invalid
    """
    if not phone or not isinstance(phone, str):
        return None
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Must have at least 10 digits
    if len(digits_only) < 10:
        return None
    
    # Handle US numbers (10 or 11 digits)
    if len(digits_only) == 11 and digits_only[0] == '1':
        digits_only = digits_only[1:]  # Remove country code
    elif len(digits_only) == 10:
        pass  # Already correct length
    else:
        # For other lengths, just return the original cleaned version
        pass
    
    # Format as (XXX) XXX-XXXX for 10-digit numbers
    if len(digits_only) == 10:
        return f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
    
    return digits_only