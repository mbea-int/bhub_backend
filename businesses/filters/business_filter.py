from django_filters import rest_framework as filters
from businesses.models import Business


class BusinessFilter(filters.FilterSet):
    """
    Custom filters për Business model që pranon slug për kategori
    """
    category = filters.CharFilter(
        field_name='category__slug',
        lookup_expr='exact',
        help_text='Filter by category slug'
    )

    city = filters.CharFilter(
        field_name='city',
        lookup_expr='icontains',
        help_text='Filter by city (case insensitive)'
    )

    min_rating = filters.NumberFilter(
        field_name='average_rating',
        lookup_expr='gte',
        help_text='Minimum rating'
    )

    max_rating = filters.NumberFilter(
        field_name='average_rating',
        lookup_expr='lte',
        help_text='Maximum rating'
    )

    class Meta:
        model = Business
        fields = {
            'is_verified': ['exact'],
            'is_premium': ['exact'],
            'is_halal_certified': ['exact'],
            # 'is_active': ['exact'],
        }