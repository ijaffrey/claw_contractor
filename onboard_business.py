"""
Business Onboarding Script
Interactive CLI tool to onboard new businesses to OpenClaw Trade Assistant
"""

import database as db
import sys


def get_input(prompt, required=True, default=None):
    """
    Get user input with validation

    Args:
        prompt: Question to ask user
        required: Whether this field is required
        default: Default value if user presses enter

    Returns:
        str: User input
    """
    while True:
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            if not user_input:
                return default
            return user_input
        else:
            user_input = input(f"{prompt}: ").strip()
            if user_input or not required:
                return user_input if user_input else None
            else:
                print("  ⚠ This field is required. Please enter a value.")


def validate_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone):
    """Basic phone validation"""
    import re
    # Remove common formatting characters
    cleaned = re.sub(r'[^0-9]', '', phone)
    # Should have 10-11 digits (with or without country code)
    return len(cleaned) >= 10


def confirm_details(business_data):
    """
    Show business details and ask for confirmation

    Args:
        business_data: Dict with all business info

    Returns:
        bool: True if confirmed
    """
    print("\n" + "=" * 60)
    print("BUSINESS PROFILE SUMMARY")
    print("=" * 60)
    print(f"Business Name:  {business_data['name']}")
    print(f"Trade Type:     {business_data['trade_type']}")
    print(f"Owner Name:     {business_data.get('owner_name', 'Not provided')}")
    print(f"Email:          {business_data['email']}")
    print(f"Phone:          {business_data.get('phone', 'Not provided')}")
    print(f"Service Area:   {business_data.get('service_area', 'Not provided')}")
    print(f"\nBrand Voice:")
    print(f"{business_data['brand_voice']}")
    print("=" * 60)

    response = input("\nIs this information correct? (yes/no): ").strip().lower()
    return response in ['yes', 'y']


def main():
    """Interactive business onboarding flow"""
    print("\n" + "=" * 60)
    print("🦞 OpenClaw Trade Assistant - Business Onboarding")
    print("=" * 60)
    print("This wizard will help you onboard a new business.")
    print("You'll be asked a series of questions about the business.")
    print("=" * 60 + "\n")

    # Check database connection
    print("Checking database connection...")
    try:
        db.test_connection()
        print()
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("Please check your SUPABASE_URL and SUPABASE_KEY in .env")
        sys.exit(1)

    # Collect business information
    print("─" * 60)
    print("STEP 1: Basic Information")
    print("─" * 60)

    business_name = get_input("Business name (e.g., 'Smith's Plumbing')", required=True)

    print("\nCommon trade types: plumbing, electrical, hvac, general contractor")
    trade_type = get_input("Trade type", required=True)

    owner_name = get_input("Owner/Contact name", required=False)

    # Email with validation
    while True:
        email = get_input("Business email", required=True)
        if validate_email(email):
            break
        else:
            print("  ⚠ Please enter a valid email address (e.g., contact@business.com)")

    # Phone with validation
    while True:
        phone = get_input("Business phone (e.g., '555-123-4567')", required=False)
        if not phone or validate_phone(phone):
            break
        else:
            print("  ⚠ Please enter a valid phone number (at least 10 digits)")

    service_area = get_input("Service area (e.g., 'Boston Metro Area')", required=False)

    # Brand voice
    print("\n" + "─" * 60)
    print("STEP 2: Brand Voice")
    print("─" * 60)
    print("Describe how this business communicates with customers.")
    print("This helps the AI match the business's personality and tone.")
    print("\nExamples:")
    print("  • 'Friendly, professional, and family-oriented'")
    print("  • 'Direct, efficient, and no-nonsense'")
    print("  • 'Warm, helpful, and community-focused'")
    print()

    brand_voice = get_input(
        "Brand voice description",
        required=True
    )

    # Prepare business data
    business_data = {
        'name': business_name,
        'trade_type': trade_type.lower(),
        'brand_voice': brand_voice,
        'email': email
    }

    # Add optional fields
    if owner_name:
        business_data['owner_name'] = owner_name
    if phone:
        business_data['phone'] = phone
    if service_area:
        business_data['service_area'] = service_area

    # Confirm before saving
    if not confirm_details(business_data):
        print("\n⊗ Onboarding cancelled. No changes made.")
        sys.exit(0)

    # Save to database
    print("\n💾 Saving business profile to database...")

    try:
        saved_business = db.insert_business(business_data)

        if saved_business:
            print("\n" + "=" * 60)
            print("✅ BUSINESS ONBOARDED SUCCESSFULLY!")
            print("=" * 60)
            print(f"Business ID:   {saved_business['id']}")
            print(f"Business Name: {saved_business['name']}")
            print(f"Email:         {saved_business['email']}")
            print(f"Created:       {saved_business['created_at']}")
            print("=" * 60)

            print("\n📋 Next Steps:")
            print("1. Configure Gmail forwarding or monitoring for this business")
            print("2. Update GMAIL_USER_EMAIL in .env if needed")
            print("3. Run 'python3 main.py' to start processing leads")
            print("4. Send a test email to verify the setup")
            print()

            # Ask if they want to onboard another business
            another = input("Onboard another business? (yes/no): ").strip().lower()
            if another in ['yes', 'y']:
                print("\n" + "=" * 60 + "\n")
                main()  # Recursive call for another business
            else:
                print("\n✓ Onboarding complete!\n")

        else:
            print("\n✗ Failed to save business profile")
            print("Check database connection and try again")
            sys.exit(1)

    except Exception as e:
        print(f"\n✗ Error saving business: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⊗ Onboarding cancelled by user\n")
        sys.exit(0)
