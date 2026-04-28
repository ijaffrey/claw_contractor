#!/usr/bin/env python3
"""
Demo script to show photo_analyzer.py outputs for each trade type.
Uses sample images to demonstrate Claude Vision analysis.
"""

import photo_analyzer
import requests
from io import BytesIO

# Sample images for demonstration (publicly available examples)
SAMPLE_IMAGES = {
    "plumbing": {
        "url": "https://images.unsplash.com/photo-1607472586893-edb57bdc0e39?w=800",  # Water heater
        "description": "Water heater with visible label",
    },
    "roofing": {
        "url": "https://images.unsplash.com/photo-1632778149955-e80f8ceca2e7?w=800",  # Roof damage
        "description": "Roof with missing/damaged shingles",
    },
    "electrical": {
        "url": "https://images.unsplash.com/photo-1621905251918-48416bd8575a?w=800",  # Electrical panel
        "description": "Electrical service panel",
    },
    "general_contractor": {
        "url": "https://images.unsplash.com/photo-1556911220-bff31c812dba?w=800",  # Kitchen
        "description": "Kitchen space for remodel",
    },
}


def download_image(url):
    """Download image from URL and return bytes"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None


def demo_trade_analysis(trade_type, image_info):
    """Demonstrate photo analysis for a specific trade"""
    print(f"\n{'='*80}")
    print(f"TRADE: {trade_type.upper()}")
    print(f"Sample Image: {image_info['description']}")
    print(f"{'='*80}")

    # Download image
    print(f"Downloading sample image from: {image_info['url'][:60]}...")
    image_data = download_image(image_info["url"])

    if not image_data:
        print("❌ Failed to download image")
        return

    print(f"✓ Downloaded {len(image_data)} bytes")

    # Analyze photo
    print(f"\nAnalyzing with Claude Vision ({trade_type} prompt)...")
    analysis = photo_analyzer.analyze_photo(
        image_data=image_data, trade_type=trade_type, content_type="image/jpeg"
    )

    if analysis:
        print(f"\n📷 ANALYSIS OUTPUT:\n")
        print(f"{analysis}\n")
        print(f"Word count: {len(analysis.split())} words")
        print(f"✓ Analysis complete")
    else:
        print("❌ Analysis failed")


def main():
    print("\n" + "=" * 80)
    print("PHOTO ANALYZER DEMONSTRATION")
    print("Showing Claude Vision analysis for each trade type")
    print("=" * 80)

    for trade_type, image_info in SAMPLE_IMAGES.items():
        demo_trade_analysis(trade_type, image_info)

    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Review analysis outputs for accuracy and tone")
    print("2. Verify outputs stay under 80 words")
    print("3. Confirm factual (not diagnostic) approach")
    print("4. Once approved, wire into main.py email processing")


if __name__ == "__main__":
    main()
