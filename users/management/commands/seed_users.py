from django.core.management.base import BaseCommand
from django.db import IntegrityError
from users.models import User
from . import fake_users

class Command(BaseCommand):
    """
    per te runuar kete komande shkruaj
    python manage.py seed_users
    """
    help = "Seed fake users into the database"

    def handle(self, *args, **options):
        for user_data in fake_users.fake_users:
            email = user_data["email"]
            full_name = user_data["full_name"]
            password = user_data["password"]

            # Fshij password përpara përdorimit te create_user (pasi është i veçantë)
            extra_fields = {k: v for k, v in user_data.items() if k not in ["email", "full_name", "password"]}

            try:
                # Nëse është superuser
                if extra_fields.get("is_superuser"):
                    if not User.objects.filter(email=email).exists():
                        user = User.objects.create_superuser(
                            email=email,
                            full_name=full_name,
                            password=password,
                            **extra_fields
                        )
                        self.stdout.write(self.style.SUCCESS(f"✅ Created superuser: {email}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"⚠️ User {email} already exists"))

                # Nëse është përdorues normal
                else:
                    if not User.objects.filter(email=email).exists():
                        user = User.objects.create_user(
                            email=email,
                            full_name=full_name,
                            password=password,
                            **extra_fields
                        )
                        self.stdout.write(self.style.SUCCESS(f"✅ Created user: {email}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"⚠️ User {email} already exists"))

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"❌ Integrity error for {email}: {e}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Failed to create {email}: {e}"))
