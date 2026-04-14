import re


def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number.
    Accepts formats: +7XXXXXXXXXX, 8XXXXXXXXXX, +380XXXXXXXXX, etc.
    """
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
    
    pattern = r'^[\+]?[1-9]\d{9,14}$'
    return bool(re.match(pattern, cleaned))


def clean_phone_number(phone: str) -> str:
    """Clean and format phone number."""
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
    return cleaned


def validate_price(price_str: str) -> tuple[bool, float | None]:
    """
    Validate price string.
    Returns (is_valid, price_value)
    """
    try:
        price = float(price_str.replace(',', '.').replace(' ', ''))
        return price > 0, price
    except ValueError:
        return False, None
