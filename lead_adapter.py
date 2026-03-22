import re
from datetime import datetime
from typing import Dict, List, Any, Optional


def normalize_lead(flat_lead_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert flat lead dictionary to nested qualified lead detector format.
    
    Args:
        flat_lead_dict: Flat dictionary from lead parser
        
    Returns:
        Nested dictionary structure for qualified lead detector
    """
    normalized_lead = {
        'contact_info': _extract_contact_info(flat_lead_dict),
        'location': _extract_location_info(flat_lead_dict),
        'problem_description': flat_lead_dict.get('description', ''),
        'photos': _normalize_attachments(flat_lead_dict.get('attachments', [])),
        'urgency': _determine_urgency(flat_lead_dict),
        'source': flat_lead_dict.get('source', 'unknown'),
        'job_type': flat_lead_dict.get('job_type', 'general')
    }
    
    return normalized_lead


def _extract_contact_info(flat_lead_dict: Dict[str, Any]) -> Dict[str, str]:
    """Extract and normalize contact information."""
    return {
        'name': flat_lead_dict.get('customer_name', '').strip(),
        'email': flat_lead_dict.get('customer_email', '').strip().lower(),
        'phone': _normalize_phone(flat_lead_dict.get('phone', ''))
    }


def _normalize_phone(phone: str) -> str:
    """Normalize phone number format."""
    if not phone:
        return ''
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Handle different phone number lengths
    if len(digits_only) == 10:
        return f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
    elif len(digits_only) == 11 and digits_only.startswith('1'):
        return f"({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}"
    else:
        return phone  # Return original if can't normalize


def _extract_location_info(flat_lead_dict: Dict[str, Any]) -> Dict[str, str]:
    """Extract and parse location information."""
    location_string = flat_lead_dict.get('location', '').strip()
    
    if not location_string:
        return {
            'address': '',
            'city': '',
            'zip_code': ''
        }
    
    city = _parse_city_from_location(location_string)
    zip_code = _extract_zip_code(location_string)
    
    return {
        'address': location_string,
        'city': city,
        'zip_code': zip_code
    }


def _parse_city_from_location(location_string: str) -> str:
    """Parse city from location string."""
    if not location_string:
        return ''
    
    # Common state abbreviations
    state_abbreviations = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
    }
    
    # Look for pattern: City, ST or City ST or City, State
    patterns = [
        r'([^,]+),\s*([A-Z]{2})\b',  # City, ST
        r'([^,]+)\s+([A-Z]{2})\b',   # City ST
        r'([^,]+),\s*([A-Za-z\s]+)\b'  # City, State
    ]
    
    for pattern in patterns:
        match = re.search(pattern, location_string)
        if match:
            potential_city = match.group(1).strip()
            state_part = match.group(2).strip().upper()
            
            # Check if it's a valid state abbreviation or full state name
            if state_part in state_abbreviations or len(state_part) > 2:
                return potential_city
    
    # Fallback: try to extract city from comma-separated parts
    parts = location_string.split(',')
    if len(parts) >= 2:
        # Assume the part before the last comma might be the city
        potential_city = parts[-2].strip()
        if potential_city and not re.search(r'\d{5}', potential_city):  # Not a ZIP code
            return potential_city
    
    return ''


def _extract_zip_code(location_string: str) -> str:
    """Extract ZIP code from location string."""
    # Look for 5-digit ZIP code or ZIP+4 format
    zip_match = re.search(r'\b(\d{5}(?:-\d{4})?)\b', location_string)
    return zip_match.group(1) if zip_match else ''


def _normalize_attachments(attachments: List[Any]) -> List[Dict[str, str]]:
    """Convert attachments to photos format."""
    photos = []
    current_timestamp = datetime.utcnow().isoformat()
    
    for attachment in attachments:
        if isinstance(attachment, str):
            # Simple string URL
            photos.append({
                'url': attachment,
                'timestamp': current_timestamp
            })
        elif isinstance(attachment, dict):
            # Dictionary format
            photos.append({
                'url': attachment.get('url', attachment.get('path', '')),
                'timestamp': attachment.get('timestamp', current_timestamp)
            })
    
    return photos


def _determine_urgency(flat_lead_dict: Dict[str, Any]) -> str:
    """Determine urgency level based on job type and description keywords."""
    description = flat_lead_dict.get('description', '').lower()
    job_type = flat_lead_dict.get('job_type', '').lower()
    
    # Emergency keywords
    emergency_keywords = [
        'burst', 'flooding', 'flood', 'emergency', 'urgent', 'immediately',
        'asap', 'right now', 'help', 'disaster', 'overflow', 'gushing',
        'no water', 'no heat', 'gas leak', 'electrical emergency'
    ]
    
    # High priority keywords
    high_keywords = [
        'leak', 'leaking', 'broken', 'not working', 'stopped working',
        'no hot water', 'clogged', 'blocked', 'backed up', 'overflowing',
        'toilet won\'t flush', 'faucet broken', 'pipe burst'
    ]
    
    # Medium priority keywords
    medium_keywords = [
        'repair', 'fix', 'replace', 'install', 'slow drain', 'low pressure',
        'running toilet', 'dripping', 'loose', 'noisy', 'weird sound'
    ]
    
    # Low priority keywords
    low_keywords = [
        'maintenance', 'inspection', 'check', 'estimate', 'quote',
        'cleaning', 'routine', 'scheduled', 'upgrade', 'improvement'
    ]
    
    # Combine description and job_type for keyword matching
    text_to_check = f"{description} {job_type}"
    
    # Check for emergency keywords first
    if any(keyword in text_to_check for keyword in emergency_keywords):
        return 'emergency'
    
    # Check for high priority keywords
    if any(keyword in text_to_check for keyword in high_keywords):
        return 'high'
    
    # Check for low priority keywords
    if any(keyword in text_to_check for keyword in low_keywords):
        return 'low'
    
    # Check for medium priority keywords or default to medium
    if any(keyword in text_to_check for keyword in medium_keywords):
        return 'medium'
    
    # Default urgency based on job type
    if job_type:
        if 'emergency' in job_type or 'urgent' in job_type:
            return 'emergency'
        elif 'maintenance' in job_type or 'inspection' in job_type:
            return 'low'
    
    # Default to medium if no clear indicators
    return 'medium'