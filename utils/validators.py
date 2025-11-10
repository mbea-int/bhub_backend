from django.core.exceptions import ValidationError
import re


def validate_phone_number(value):
    """Validate Albanian phone number format"""
    pattern = r'^\+355\d{9}$|^0\d{9}$'
    if not re.match(pattern, value):
        raise ValidationError('Invalid phone number format. Use +355XXXXXXXXX or 0XXXXXXXXX')


def validate_business_hours(value):
    """Validate business hours JSON structure"""
    if not isinstance(value, dict):
        raise ValidationError('Business hours must be a JSON object')

    valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

    for day, hours in value.items():
        if day.lower() not in valid_days:
            raise ValidationError(f'Invalid day: {day}')

        # Validate time format (HH:MM-HH:MM)
        pattern = r'^\d{2}:\d{2}-\d{2}:\d{2}$'
        if not re.match(pattern, hours):
            raise ValidationError(f'Invalid time format for {day}. Use HH:MM-HH:MM')


def validate_image_url(value):
    """Validate image URL"""
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    if not any(value.lower().endswith(ext) for ext in valid_extensions):
        raise ValidationError('Invalid image format. Use JPG, PNG, or WebP')