import django_filters
from businesses.models import BusinessCategory

class BusinessCategoryFilter(django_filters.FilterSet):
    # Filtron kategoritë sipas karakteristikave të bizneseve të lidhura
    city = django_filters.CharFilter(
        field_name="businesses__city",
        lookup_expr="iexact"
    )
    is_verified = django_filters.BooleanFilter(
        field_name="businesses__is_verified"
    )
    is_premium = django_filters.BooleanFilter(
        field_name="businesses__is_premium"
    )
    is_halal_certified = django_filters.BooleanFilter(
        field_name="businesses__is_halal_certified"
    )

    class Meta:
        model = BusinessCategory
        # KËTO janë të vetmet fusha që ekzistojnë në model
        fields = ['name', 'slug', 'is_active']
