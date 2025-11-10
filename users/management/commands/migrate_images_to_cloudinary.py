from django.core.management.base import BaseCommand
from users.models import User
from core.services.cloudinary_service import CloudinaryService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migrate existing user profile images to Cloudinary'

    def handle(self, *args, **options):
        users_with_images = User.objects.exclude(
            profile_image__isnull=True
        ).exclude(
            profile_image__exact=''
        ).exclude(
            profile_image__contains='cloudinary'
        )

        self.stdout.write(f"Found {users_with_images.count()} users with non-Cloudinary images")

        success_count = 0
        error_count = 0

        for user in users_with_images:
            try:
                if user.profile_image and not user.profile_image.startswith('http'):
                    # Upload to Cloudinary
                    result = CloudinaryService.upload_user_profile_image(
                        user.profile_image,
                        user.email
                    )

                    if result:
                        user.profile_image = result['secure_url']
                        user.save()
                        success_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ Migrated image for {user.email}"
                            )
                        )
                    else:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f"✗ Failed to migrate image for {user.email}"
                            )
                        )
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Error migrating image for {user.email}: {str(e)}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nMigration complete: {success_count} successful, {error_count} errors"
            )
        )