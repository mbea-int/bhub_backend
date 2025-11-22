# Django management command: management/commands/fix_business_slugs.py

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from businesses.models import Business


class Command(BaseCommand):
    help = 'Fix missing slugs for existing businesses'

    def handle(self, *args, **options):
        businesses_without_slug = Business.objects.filter(
            slug__isnull=True
        ) | Business.objects.filter(slug='')

        count = 0
        for business in businesses_without_slug:
            base_slug = slugify(business.business_name)
            slug = base_slug
            counter = 1

            while Business.objects.filter(slug=slug).exclude(pk=business.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            business.slug = slug
            business.save()
            count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'Fixed slug for "{business.business_name}" -> {slug}'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully fixed {count} business slugs')
        )