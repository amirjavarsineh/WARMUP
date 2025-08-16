import phonenumbers
from phonenumbers import geocoder, carrier, timezone


def analyze_phone_number(phone_number):
    """
    Analyzes a phone number and returns information about its country, carrier, and timezone.

    Args:
        phone_number (str): The phone number to analyze (include country code)

    Returns:
        dict: Dictionary containing country, carrier, and timezone information
    """
    try:
        # Parse the phone number
        parsed_number = phonenumbers.parse(phone_number, None)

        # Get country information
        country = geocoder.description_for_number(parsed_number, "en")

        # Get carrier information (if available)
        try:
            service_provider = carrier.name_for_number(parsed_number, "en")
        except:
            service_provider = "Unknown"

        # Get timezone information
        time_zones = timezone.time_zones_for_number(parsed_number)

        return {
            "valid": True,
            "number": phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
            "country": country,
            "carrier": service_provider,
            "timezone": time_zones[0] if time_zones else "Unknown",
            "country_code": parsed_number.country_code
        }
    except phonenumbers.phonenumberutil.NumberParseException:
        return {"valid": False, "error": "Invalid phone number format"}


def main():
    print("Phone Number Country Detector")
    print("Enter phone numbers in international format (e.g., +14155552671, +442079460000)")
    print("Type 'exit' to quit\n")

    while True:
        phone_input = input("Enter phone number: ").strip()
        if phone_input.lower() == 'exit':
            break

        result = analyze_phone_number(phone_input)

        if result['valid']:
            print("\nPhone Number Analysis:")
            print(f"Number: {result['number']}")
            print(f"Country: {result['country']}")
            print(f"Country Code: +{result['country_code']}")
            print(f"Carrier: {result['carrier']}")
            print(f"Timezone: {result['timezone']}\n")
        else:
            print("Error: Invalid phone number format. Please include country code.\n")


if __name__ == "__main__":
    main()