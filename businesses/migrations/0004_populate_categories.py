from django.db import migrations


def populate_categories(apps, schema_editor):
    BusinessCategory = apps.get_model('businesses', 'BusinessCategory')

    categories = [
        {'name': 'Restaurant', 'slug': 'restaurant', 'icon': 'restaurant'},
        {'name': 'Market', 'slug': 'market', 'icon': 'store'},
        {'name': 'Clothing Store', 'slug': 'clothing-store', 'icon': 'checkroom'},
        {'name': 'Barbershop', 'slug': 'barbershop', 'icon': 'content_cut'},
        {'name': 'Mosque', 'slug': 'mosque', 'icon': 'mosque'},
        {'name': 'Islamic School', 'slug': 'islamic-school', 'icon': 'school'},
        {'name': 'Bakery', 'slug': 'bakery', 'icon': 'bakery_dining'},
        {'name': 'Butcher Shop', 'slug': 'butcher-shop', 'icon': 'storefront'},
        {'name': 'Travel Agency', 'slug': 'travel-agency', 'icon': 'flight'},
        {'name': 'Healthcare', 'slug': 'healthcare', 'icon': 'local_hospital'},
    ]

    for cat in categories:
        BusinessCategory.objects.create(**cat)


def reverse_populate(apps, schema_editor):
    BusinessCategory = apps.get_model('businesses', 'BusinessCategory')
    BusinessCategory.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('businesses', '0003_businesscategory_business_is_primary_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_categories, reverse_populate),
    ]