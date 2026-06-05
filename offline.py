"""
RoadSoS Offline Fallback
========================
Rule-based response engine that works without the Anthropic API.
Ensures the chatbot degrades gracefully in low/no-network conditions.
"""

import re
from database import find_nearby_services, get_emergency_numbers, search_by_city

# Keyword → service_type mapping
INTENT_MAP = {
    r"hospital|trauma|clinic|doctor|medical|injury|hurt|bleeding|unconscious|accident": "hospital",
    r"ambulance|emri|ems|medical.van": "ambulance",
    r"police|pcr|station|law|fir|report": "police",
    r"tow|towing|breakdown|car.stuck|vehicle.stuck|recovery": "towing",
    r"puncture|tyre|flat.tyre|tire|pump": "puncture",
    r"rescue|fire|trapped": "rescue",
}

CITY_RE = re.compile(
    r"\b(chennai|hyderabad|mumbai|bengaluru|bangalore|delhi|kolkata|pune|"
    r"new york|london|sydney|singapore)\b", re.IGNORECASE
)

EMERGENCY_RE = re.compile(
    r"emergency.number|helpline|dial|call number|sos number", re.IGNORECASE
)


def detect_intent(text: str):
    text_l = text.lower()
    for pattern, stype in INTENT_MAP.items():
        if re.search(pattern, text_l):
            return stype
    return None


def offline_respond(message: str, lat=None, lon=None, country_code="IN"):
    """Return (reply_text, services_list) without using the Claude API."""
    services = []
    reply    = ""

    # Emergency number query
    if EMERGENCY_RE.search(message):
        nums = get_emergency_numbers(country_code)
        if nums:
            reply = (
                f"🚨 Emergency numbers for {nums.get('name', country_code)}:\n"
                f"• All Emergencies : {nums.get('emergency_number','112')}\n"
                f"• Ambulance       : {nums.get('ambulance_number','108')}\n"
                f"• Police          : {nums.get('police_number','100')}\n"
                f"• Fire            : {nums.get('fire_number','101')}"
            )
        else:
            reply = "📞 India: Ambulance 108 | Police 100 | Fire 101 | National Emergency 112"
        return reply, services

    service_type = detect_intent(message)
    city_match   = CITY_RE.search(message)

    if lat and lon:
        services = find_nearby_services(lat, lon, service_type=service_type,
                                        country_code=country_code, limit=5)
        if services:
            names = ", ".join(s["name"] for s in services[:3])
            reply = (
                f"📍 Found {len(services)} nearby "
                f"{'services' if not service_type else service_type+'s'}: "
                f"{names}. See details below."
            )
        else:
            reply = "⚠️ No services found within 60 km. Expanding search or try a city name."

    elif city_match:
        city     = city_match.group(0)
        services = search_by_city(city, service_type=service_type, country_code=None)
        if services:
            names = ", ".join(s["name"] for s in services[:3])
            reply = f"🏙️ Services in {city.title()}: {names}. See cards below."
        else:
            reply = f"No records found for {city.title()}. Try a different city."

    else:
        reply = (
            "🆘 I need your location to find nearby help.\n"
            "Please tap '📍 Share Location' or type your city name.\n\n"
            "📞 Immediate help:\n"
            "• National Emergency : 112\n"
            "• Ambulance          : 108\n"
            "• Police             : 100"
        )

    return reply, services
