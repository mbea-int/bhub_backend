import uuid
from django.db import models
from users.models import User


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    conversation_id = models.UUIDField(db_index=True)
    content = models.TextField()

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(upload_to='message_attachments/', blank=True, null=True)
    attachment_type = models.CharField(max_length=20, blank=True, choices=[
        ('image', 'Image'),
        ('file', 'File'),
        ('audio', 'Audio'),
    ])
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)

    # For business inquiries
    related_business = models.ForeignKey('businesses.Business', on_delete=models.SET_NULL, null=True, blank=True)
    related_post = models.ForeignKey('posts.Post', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation_id', 'created_at']),
            models.Index(fields=['sender', 'receiver']),
        ]

    def __str__(self):
        return f"Message from {self.sender.email} to {self.receiver.email}"

    @staticmethod
    def get_conversation_id(user1_id, user2_id):
        """Generate consistent conversation ID for two users"""
        import hashlib
        sorted_ids = sorted([str(user1_id), str(user2_id)])
        conversation_string = f"{sorted_ids[0]}-{sorted_ids[1]}"
        return uuid.UUID(hashlib.md5(conversation_string.encode()).hexdigest())