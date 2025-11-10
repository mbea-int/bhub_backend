# businesses/management/commands/seed_businesses.py
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from users.models import User
from businesses.models import Business, BusinessCategory
from . import fake_businesses
from decimal import Decimal

class Command(BaseCommand):
    """
    per ta runuar
    python manage.py seed_businesses
    """
    help = "Seed fake businesses into the database"

    def handle(self, *args, **options):
        for data in fake_businesses.fake_businesses:
            user_email = data.get("user_email")
            category_slug = data.get("category")

            # Gjej user-in përkatës
            try:
                user = User.objects.get(email=user_email)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ User not found: {user_email}"))
                continue

            # Gjej kategorinë përkatëse
            try:
                category = BusinessCategory.objects.get(slug=category_slug)
            except BusinessCategory.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ Category not found: {category_slug}"))
                continue

            # Kontrollo nëse ekziston
            if Business.objects.filter(slug=data["slug"]).exists():
                self.stdout.write(self.style.WARNING(f"⚠️ Business already exists: {data['business_name']}"))
                continue

            try:
                # Përgatit fushat që duhen
                business = Business.objects.create(
                    user=user,
                    business_name=data["business_name"],
                    slug=data["slug"],
                    description=data["description"],
                    category=category,
                    logo=data.get("logo"),
                    phone=data.get("phone", ""),
                    email=data.get("email", ""),
                    address=data.get("address", ""),
                    city=data.get("city", ""),
                    country=data.get("country", "Albania"),
                    latitude=data.get("latitude"),
                    longitude=data.get("longitude"),
                    business_hours=data.get("business_hours"),
                    is_verified=data.get("is_verified", False),
                    is_premium=data.get("is_premium", False),
                    is_halal_certified=data.get("is_halal_certified", False),
                    social_instagram=data.get("social_instagram"),
                    social_facebook=data.get("social_facebook"),
                    average_rating=Decimal(str(data.get("average_rating", 0))),
                    total_reviews=data.get("total_reviews", 0),
                    total_followers=data.get("total_followers", 0),
                    total_subscribers=data.get("total_subscribers", 0),
                    is_primary=data.get("is_primary", False),
                )

                self.stdout.write(self.style.SUCCESS(f"✅ Created business: {business.business_name} ({user_email})"))

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"❌ Integrity error for {data['business_name']}: {e}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Failed to create {data['business_name']}: {e}"))
