from django.utils.text import slugify
import random
import string
import re


def generate_unique_slug(model_class, title, slug_field='slug'):
    """Generate unique slug for model"""
    slug = slugify(title)
    unique_slug = slug
    counter = 1

    while model_class.objects.filter(**{slug_field: unique_slug}).exists():
        unique_slug = f"{slug}-{counter}"
        counter += 1

    return unique_slug


def generate_random_code(length=8):
    """Generate random alphanumeric code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def format_text(text):
    """Auto-capitalize and format text"""
    if not text:
        return text

    # Capitalize first letter
    text = text.strip()
    if text:
        text = text[0].upper() + text[1:]

    # Fix common spacing issues
    text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
    text = re.sub(r'\s+([.,!?])', r'\1', text)  # Remove space before punctuation

    return text


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates using Haversine formula"""
    from math import radians, cos, sin, asin, sqrt

    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))

    # Radius of earth in kilometers
    r = 6371

    return c * r