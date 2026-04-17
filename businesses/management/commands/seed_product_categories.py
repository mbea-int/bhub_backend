from django.core.management.base import BaseCommand
from businesses.models import BusinessCategory
from django.utils.text import slugify

#per ta runuar python manage.py seed_product_categories


DEFAULT_BUSINESS_CATEGORIES = [
    {"name": "Restaurant"},
    {"name": "Market"},
    {"name": "Clothing Store"},
    {"name": "Barbershop"},
    {"name": "Mosque"},
    {"name": "Islamic School"},
    {"name": "Bakery"},
    {"name": "Healthcare"},
]

class Command(BaseCommand):
    help = "Seed default business categories"

    def handle(self, *args, **options):
        for cat in DEFAULT_BUSINESS_CATEGORIES:
            slug = slugify(cat["name"])
            if BusinessCategory.objects.filter(slug=slug).exists():
                self.stdout.write(self.style.WARNING(f"⚠️ Category '{cat['name']}' already exists"))
                continue

            BusinessCategory.objects.create(name=cat["name"], slug=slug)
            self.stdout.write(self.style.SUCCESS(f"✅ Created category: {cat['name']}"))

        self.stdout.write(self.style.SUCCESS("🎉 Default business categories seeding completed!"))
