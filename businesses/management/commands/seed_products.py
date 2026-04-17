# python manage.py seed_products
import uuid
from django.core.management.base import BaseCommand
from decimal import Decimal
from posts.models import Post, ProductCategory
from businesses.models import Business
import random

FAKE_PRODUCTS = [
    {"name": "Product A", "description": "Description for product A", "price": 10.50,
     "image_url": "https://via.placeholder.com/150"},
    {"name": "Product B", "description": "Description for product B", "price": 20.00,
     "image_url": "https://via.placeholder.com/150"},
    {"name": "Product C", "description": "Description for product C", "price": 15.75,
     "image_url": "https://via.placeholder.com/150"},
]

NUM_PRODUCTS_PER_CATEGORY = 3  # sa produkte të krijohen për çdo kategori


class Command(BaseCommand):
    help = "Seed demo products for each business and its product categories"

    def handle(self, *args, **options):
        businesses = Business.objects.all()
        if not businesses.exists():
            self.stdout.write(self.style.WARNING("⚠️ No businesses found. Seed businesses first."))
            return

        for business in businesses:
            categories = ProductCategory.objects.filter(business=business, is_active=True)
            if not categories.exists():
                self.stdout.write(self.style.WARNING(
                    f"⚠️ No product categories found for business '{business.business_name}'. Seed product categories first."))
                continue

            for category in categories:
                for _ in range(NUM_PRODUCTS_PER_CATEGORY):
                    product_data = random.choice(FAKE_PRODUCTS)
                    product_name = f"{product_data['name']} ({category.name})"

                    # Kontrollo nëse produkti ekziston
                    if Post.objects.filter(business=business, product_name=product_name,
                                           product_category=category).exists():
                        self.stdout.write(self.style.WARNING(
                            f"⚠️ Product '{product_name}' already exists for business '{business.business_name}'"))
                        continue

                    Post.objects.create(
                        business=business,
                        business_category=business.category,
                        product_category=category,
                        product_name=product_name,
                        description=product_data["description"],
                        price=Decimal(str(product_data["price"])),
                        image_url=product_data["image_url"],
                        is_available=True
                    )
                    self.stdout.write(self.style.SUCCESS(
                        f"✅ Created product '{product_name}' for business '{business.business_name}'"))

        self.stdout.write(self.style.SUCCESS("🎉 Product seeding completed!"))
