"""
Photo Analyzer Module
Uses Claude Vision to analyze photos from homeowner inquiries
"""

from anthropic import Anthropic
from config import Config
import base64
from typing import Dict, Optional


# Trade-specific analysis prompts
ANALYSIS_PROMPTS = {
    'plumbing': """Analyze this photo from a plumbing service inquiry. Identify and describe:
1. EQUIPMENT: If this shows a water heater, boiler, or similar equipment — identify the brand, model, capacity (gallons), fuel type (gas/electric), and estimate age from the serial number format if the label is visible.
2. FIXTURES: If this shows a toilet, faucet, sink, or shower — identify the brand, model/style, handle type, and any visible model numbers.
3. PIPE MATERIAL: If pipes are visible — identify the material (copper, PEX, CPVC, galvanized, cast iron, PVC).
4. DAMAGE: If there is visible damage — describe what you see: location, extent, severity. Be factual, not diagnostic.
5. PARTS: If you can identify the likely part needed for repair (e.g., a specific faucet cartridge, fill valve, wax ring), note it.

Format as a brief summary paragraph (under 80 words) suitable for including in a lead report to a plumber. Start with the most important finding. Be specific on brand/model when visible, honest when you can't tell.""",

    'roofing': """Analyze this photo from a roofing service inquiry. Identify and describe:
1. ROOF MATERIAL: Asphalt 3-tab, architectural shingle, metal standing seam, flat TPO/EPDM, clay tile, slate, wood shake.
2. DAMAGE: Missing shingles (count approximate area), lifted flashing, exposed underlayment, debris impact, sagging areas. Note location on roof if determinable.
3. INTERIOR DAMAGE: If this is an interior shot — describe water stain size, ceiling condition (paint bubbling, sagging drywall, active drip).
4. AGE INDICATORS: Curling shingles, granule loss, moss/algae growth, weathering patterns.

Format as a brief summary paragraph (under 80 words) suitable for including in a lead report to a roofer. Be specific on damage extent. Note anything relevant for insurance documentation.""",

    'electrical': """Analyze this photo from an electrical service inquiry. Identify and describe:
1. PANEL: If this shows an electrical panel — identify brand (Square D, Siemens, GE, Eaton, Murray), estimate amperage, count open breaker slots, note any visible corrosion or damage. FLAG if this is a known-problem panel: Federal Pacific Stab-Lok, Zinsco, or Pushmatic.
2. OUTLET/SWITCH: If this shows an outlet or switch — describe any discoloration, scorching, melting, cracking. Note if it appears to be a standard, GFCI, or AFCI outlet.
3. WIRING: If wiring is visible — note type (Romex NM, conduit, knob-and-tube, aluminum) and condition.
4. FIXTURES: If this shows a fixture to be replaced or installed — describe type, mounting, and location.

Format as a brief summary paragraph (under 80 words) suitable for including in a lead report to an electrician. Flag any safety concerns prominently.""",

    'general_contractor': """Analyze this photo from a general contractor inquiry. Identify and describe:
1. SPACE: Room type, approximate dimensions if determinable, layout style, number of windows/doors visible.
2. CURRENT CONDITION: Age and quality of existing finishes (cabinets, counters, flooring, fixtures). Builder-grade vs custom. General condition.
3. STRUCTURAL: Any visible structural elements (load-bearing walls likely, beam pockets, posts). Note if walls appear to be exterior vs interior.
4. DAMAGE: If fire/water damage — describe extent and affected areas. What's destroyed vs salvageable.

Format as a brief summary paragraph (under 80 words) suitable for including in a lead report to a general contractor. Focus on scope-relevant details."""
}


def analyze_photo(image_data: bytes, trade_type: str, content_type: str = 'image/jpeg') -> Optional[str]:
    """
    Analyze a photo using Claude Vision.

    Args:
        image_data: Raw image bytes
        trade_type: Type of trade (plumbing, roofing, electrical, general_contractor)
        content_type: MIME type of the image (image/jpeg, image/png, image/heic)

    Returns:
        str: Analysis summary suitable for lead report, or None if analysis fails
    """
    config = Config()
    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

    # Get trade-specific prompt
    analysis_prompt = ANALYSIS_PROMPTS.get(trade_type)
    if not analysis_prompt:
        # Fallback to generic analysis
        analysis_prompt = """Analyze this photo from a home service inquiry. Describe what you see in a brief paragraph (under 80 words) suitable for a contractor's lead report. Focus on identifying equipment, materials, damage, or project scope details."""

    try:
        # Convert image to base64
        image_base64 = base64.standard_b64encode(image_data).decode('utf-8')

        # Map MIME types for Claude
        mime_type_map = {
            'image/jpeg': 'image/jpeg',
            'image/jpg': 'image/jpeg',
            'image/png': 'image/png',
            'image/heic': 'image/jpeg',  # HEIC gets converted to JPEG in preprocessing
            'image/webp': 'image/webp'
        }
        claude_mime_type = mime_type_map.get(content_type.lower(), 'image/jpeg')

        # Call Claude Vision API
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": claude_mime_type,
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": analysis_prompt
                    }
                ]
            }]
        )

        # Extract the analysis text
        analysis = response.content[0].text.strip()
        return analysis

    except Exception as e:
        print(f"Photo analysis error: {e}")
        return None


def analyze_multiple_photos(photos: list, trade_type: str) -> Optional[str]:
    """
    Analyze multiple photos and return a combined summary.

    Args:
        photos: List of dicts with 'data' (bytes) and 'content_type' (str)
        trade_type: Type of trade

    Returns:
        str: Combined analysis summary, or None if all analyses fail
    """
    analyses = []

    for i, photo in enumerate(photos[:5]):  # Limit to 5 photos max
        analysis = analyze_photo(
            photo['data'],
            trade_type,
            photo.get('content_type', 'image/jpeg')
        )
        if analysis:
            if len(photos) > 1:
                analyses.append(f"Photo {i+1}: {analysis}")
            else:
                analyses.append(analysis)

    if not analyses:
        return None

    # Combine analyses
    if len(analyses) == 1:
        return analyses[0]
    else:
        return "\n\n".join(analyses)


def format_lead_summary_with_photos(lead_data: Dict, photo_analysis: Optional[str]) -> str:
    """
    Format a lead summary that includes photo analysis.

    Args:
        lead_data: Lead information dictionary
        photo_analysis: Photo analysis text from analyze_photo()

    Returns:
        str: Formatted summary for contractor
    """
    summary_parts = []

    # Basic lead info
    if lead_data.get('urgency'):
        summary_parts.append(f"Urgency: {lead_data['urgency']}")
    if lead_data.get('job_details'):
        summary_parts.append(f"Issue: {lead_data['job_details']}")
    if lead_data.get('location'):
        summary_parts.append(f"Location: {lead_data['location']}")
    if lead_data.get('availability'):
        summary_parts.append(f"Availability: {lead_data['availability']}")

    # Add photo analysis if available
    if photo_analysis:
        summary_parts.append(f"\n📷 Photo Analysis:\n{photo_analysis}")

    return "\n".join(summary_parts)
