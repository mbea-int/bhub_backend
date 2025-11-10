from rest_framework import serializers
from .models import Message
from users.serializers import UserListSerializer


class MessageSerializer(serializers.ModelSerializer):
    sender = UserListSerializer(read_only=True)
    receiver = UserListSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'conversation_id', 'content', 'is_read', 'read_at', 'created_at']
        read_only_fields = ['id', 'sender', 'conversation_id', 'is_read', 'read_at', 'created_at']


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['receiver', 'content']

    def create(self, validated_data):
        sender = self.context['request'].user
        receiver = validated_data['receiver']

        # Generate conversation ID
        conversation_id = Message.get_conversation_id(sender.id, receiver.id)

        return Message.objects.create(
            sender=sender,
            receiver=receiver,
            conversation_id=conversation_id,
            content=validated_data['content']
        )


class ConversationSerializer(serializers.Serializer):
    """Serializer for conversation list"""
    other_user = UserListSerializer()
    last_message = MessageSerializer()
    unread_count = serializers.IntegerField()