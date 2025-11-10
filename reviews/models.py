import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from businesses.models import Business
from users.models import User
from posts.models import Post


class Inquiry(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('contacted', 'Contacted'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='inquiries')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_inquiries')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_inquiries')

    buyer_name = models.CharField(max_length=255)
    buyer_phone = models.CharField(max_length=20)
    buyer_address = models.TextField(blank=True, null=True)
    message = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_reviewed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inquiries'
        ordering = ['-created_at']

    def __str__(self):
        return f"Inquiry for {self.post.product_name} by {self.buyer.email}"

    def mark_contacted(self):
        """Mark inquiry as contacted - enables review"""
        self.status = 'contacted'
        self.save()


class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    inquiry = models.ForeignKey(Inquiry, on_delete=models.SET_NULL, null=True, blank=True, related_name='review')

    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, null=True)
    images = models.JSONField(blank=True, null=True)  # Array of image URLs

    is_approved = models.BooleanField(default=True)
    admin_note = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reviews'
        unique_together = ['business', 'user', 'inquiry']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rating} stars for {self.business.business_name} by {self.user.email}"

    def save(self, *args, **kwargs):
        # Validate comment requirement for low ratings
        if self.rating <= 3 and not self.comment:
            raise ValueError("Comment is required for ratings 3 or below")

        super().save(*args, **kwargs)

        # Update business average rating
        self.business.calculate_average_rating()

        # Mark inquiry as reviewed
        if self.inquiry:
            self.inquiry.is_reviewed = True
            self.inquiry.save()