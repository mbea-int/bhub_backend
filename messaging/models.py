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