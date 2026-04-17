# python manage.py seed_product_categories_for_business
#pastaj run    python manage.py seed_products

from django.core.management.base import BaseCommand
from businesses.models import Business
from posts.models import ProductCategory

DEFAULT_PRODUCT_CATEGORIES = [
    "Food",
    "Beverages",
    "Clothing",
    "Services",
]

class Command(BaseCommand):
    help = "Seed default product categories for each business"

    def handle(self, *args, **options):
        businesses = Business.objects.all()
        if not businesses.exists():
            self.stdout.write(self.style.WARNING("⚠️ No businesses found. Seed businesses first."))
            return

        for business in businesses:
            for cat_name in DEFAULT_PRODUCT_CATEGORIES:
                if ProductCategory.objects.filter(business=business, name=cat_name).exists():
                    self.stdout.write(self.style.WARNING(f"⚠️ Category '{cat_name}' already exists for '{business.business_name}'"))
                    continue
                ProductCategory.objects.create(
                    business=business,
                    name=cat_name
                )
                self.stdout.write(self.style.SUCCESS(f"✅ Created category '{cat_name}' for '{business.business_name}'"))

        self.stdout.write(self.style.SUCCESS("🎉 Product categories for businesses seeding completed!"))
