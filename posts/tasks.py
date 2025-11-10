from celery import shared_task
from django.utils import timezone
from .models import PostDailyLimit

@shared_task
def reset_daily_post_limits():
    """Reset all daily post limits at midnight"""
    yesterday = timezone.now().date() - timezone.timedelta(days=1)
    deleted = PostDailyLimit.objects.filter(date__lt=yesterday).delete()
    return f"Deleted {deleted[0]} old post limits"

@shared_task
def process_image_compression(image_url):
    """Compress and create thumbnail for uploaded image"""
    # TODO: Implement image compression using Pillow or Cloudinary API
    pass