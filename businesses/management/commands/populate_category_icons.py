# businesses/management/commands/populate_category_icons.py
# Ekzekuto me: python manage.py populate_category_icons

from django.core.management.base import BaseCommand
from businesses.models import BusinessCategory


class Command(BaseCommand):
    help = 'Populate icons for existing business categories'

    def handle(self, *args, **options):
        # Mapping i kategorive me ikonat e tyre
        category_icon_mapping = {
            # Food & Dining (shqip/anglisht)
            'restorante': 'restaurant_rounded',
            'restaurant': 'restaurant_rounded',
            'kafene': 'local_cafe_rounded',
            'cafe': 'local_cafe_rounded',
            'coffee shop': 'local_cafe_rounded',
            'furre': 'bakery_dining_rounded',
            'bakery': 'bakery_dining_rounded',
            'piceri': 'local_pizza_rounded',
            'pizza': 'local_pizza_rounded',
            'fast food': 'lunch_dining_rounded',

            # Shopping
            'market': 'store_rounded',
            'dyqan': 'store_rounded',
            'supermarket': 'shopping_cart_rounded',
            'butik': 'checkroom_rounded',
            'clothing store': 'checkroom_rounded',
            'rroba': 'checkroom_rounded',
            'kasap': 'storefront_rounded',
            'butcher': 'storefront_rounded',
            'mish': 'storefront_rounded',

            # Services
            'berber': 'content_cut_rounded',
            'barbershop': 'content_cut_rounded',
            'salon': 'face_rounded',
            'beauty salon': 'face_rounded',
            'spa': 'spa_rounded',
            'pastrim': 'cleaning_services_rounded',
            'cleaning': 'cleaning_services_rounded',
            'riparim': 'build_rounded',
            'repair': 'build_rounded',
            'ndërtim': 'build_rounded',
            'construction': 'build_rounded',

            # Healthcare
            'spital': 'local_hospital_rounded',
            'hospital': 'local_hospital_rounded',
            'klinikë': 'local_hospital_rounded',
            'clinic': 'local_hospital_rounded',
            'farmaci': 'local_pharmacy_rounded',
            'pharmacy': 'local_pharmacy_rounded',
            'mjekësi': 'medical_services_rounded',
            'medical': 'medical_services_rounded',
            'dhëmbë': 'medical_services_rounded',
            'dental': 'medical_services_rounded',
            'psikolog': 'psychology_rounded',
            'psychology': 'psychology_rounded',

            # Education & Religion
            'shkollë': 'school_rounded',
            'school': 'school_rounded',
            'arsim': 'school_rounded',
            'education': 'school_rounded',
            'xhami': 'mosque_rounded',
            'mosque': 'mosque_rounded',
            'mejtep': 'mosque_rounded',
            'islamic school': 'mosque_rounded',
            'librari': 'menu_book_rounded',
            'library': 'menu_book_rounded',
            'libra': 'menu_book_rounded',
            'books': 'menu_book_rounded',

            # Travel & Hospitality
            'agjenci udhëtimi': 'flight_rounded',
            'travel agency': 'flight_rounded',
            'travel': 'flight_rounded',
            'hotel': 'hotel_rounded',
            'bujtinë': 'hotel_rounded',
            'apartament': 'apartment_rounded',
            'apartment': 'apartment_rounded',
            'pasuri të paluajtshme': 'apartment_rounded',
            'real estate': 'apartment_rounded',
            'makinë': 'directions_car_rounded',
            'car': 'directions_car_rounded',
            'auto': 'directions_car_rounded',
            'taksi': 'local_taxi_rounded',
            'taxi': 'local_taxi_rounded',

            # Fitness & Sports
            'palestër': 'fitness_center_rounded',
            'gym': 'fitness_center_rounded',
            'fitness': 'fitness_center_rounded',
            'sport': 'sports_soccer_rounded',
            'sports': 'sports_soccer_rounded',
            'notim': 'pool_rounded',
            'swimming': 'pool_rounded',

            # Technology
            'kompjuter': 'computer_rounded',
            'computer': 'computer_rounded',
            'teknologji': 'computer_rounded',
            'technology': 'computer_rounded',
            'telefon': 'phone_android_rounded',
            'phone': 'phone_android_rounded',
            'mobile': 'phone_android_rounded',
            'elektronikë': 'phone_android_rounded',
            'electronics': 'phone_android_rounded',
            'fotografi': 'camera_rounded',
            'photography': 'camera_rounded',

            # Entertainment
            'kinema': 'movie_rounded',
            'cinema': 'movie_rounded',
            'movie': 'movie_rounded',
            'teatër': 'theater_comedy_rounded',
            'theater': 'theater_comedy_rounded',
            'muzikë': 'music_note_rounded',
            'music': 'music_note_rounded',
        }

        updated_count = 0
        not_found_categories = []

        # Përditëso kategoritë ekzistuese
        for category in BusinessCategory.objects.all():
            name_lower = category.name.lower()
            icon = None

            # Kërko match të plotë
            if name_lower in category_icon_mapping:
                icon = category_icon_mapping[name_lower]
            else:
                # Kërko nëse emri përmban fjalë kyçe
                for key, value in category_icon_mapping.items():
                    if key in name_lower or name_lower in key:
                        icon = value
                        break

            if icon:
                category.icon = icon
                category.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Updated "{category.name}" with icon: {icon}')
                )
            else:
                # Vendos default icon
                category.icon = 'business_rounded'
                category.save()
                not_found_categories.append(category.name)
                self.stdout.write(
                    self.style.WARNING(f'⚠ Set default icon for: "{category.name}"')
                )

        self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully updated {updated_count} categories'))

        if not_found_categories:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠ {len(not_found_categories)} categories set to default icon:'
                )
            )
            for name in not_found_categories:
                self.stdout.write(f'  - {name}')
            self.stdout.write(
                self.style.NOTICE(
                    '\nYou can manually update these in Django admin with appropriate icons.'
                )
            )


# OSE përdor një data migration të thjeshtë
# businesses/migrations/0xxx_populate_category_icons.py

from django.db import migrations


def populate_icons(apps, schema_editor):
    BusinessCategory = apps.get_model('businesses', 'BusinessCategory')

    # Lista e kategorive me ikonat e tyre
    updates = [
        ('restaurant', 'restaurant_rounded'),
        ('cafe', 'local_cafe_rounded'),
        ('bakery', 'bakery_dining_rounded'),
        ('market', 'store_rounded'),
        ('clothing-store', 'checkroom_rounded'),
        ('barbershop', 'content_cut_rounded'),
        ('salon', 'face_rounded'),
        ('mosque', 'mosque_rounded'),
        ('school', 'school_rounded'),
        ('travel-agency', 'flight_rounded'),
        ('hospital', 'local_hospital_rounded'),
        ('pharmacy', 'local_pharmacy_rounded'),
        ('hotel', 'hotel_rounded'),
        ('gym', 'fitness_center_rounded'),
    ]

    for slug, icon in updates:
        try:
            category = BusinessCategory.objects.get(slug=slug)
            category.icon = icon
            category.save()
            print(f'✓ Updated {slug} with {icon}')
        except BusinessCategory.DoesNotExist:
            print(f'⚠ Category with slug "{slug}" not found')


def reverse_icons(apps, schema_editor):
    BusinessCategory = apps.get_model('businesses', 'BusinessCategory')
    BusinessCategory.objects.all().update(icon='business_rounded')


class Migration(migrations.Migration):
    dependencies = [
        ('businesses', '0XXX_previous_migration'),  # Ndryshoje me numrin e saktë
    ]

    operations = [
        migrations.RunPython(populate_icons, reverse_icons),
    ]