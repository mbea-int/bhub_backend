from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Max, Count, Case, When
from django.utils import timezone
from .models import Message
from .serializers import MessageSerializer, MessageCreateSerializer, ConversationSerializer
from users.models import User


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(
            Q(sender=user) | Q(receiver=user)
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer

    @action(detail=False, methods=['get'])
    def conversations(self, request):
        """Get list of conversations"""
        user = request.user

        # Get all conversation IDs
        conversations = Message.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).values('conversation_id').distinct()

        conversation_list = []

        for conv in conversations:
            conv_id = conv['conversation_id']

            # Get last message in conversation
            last_message = Message.objects.filter(conversation_id=conv_id).order_by('-created_at').first()

            # Get other user
            if last_message.sender == user:
                other_user = last_message.receiver
            else:
                other_user = last_message.sender

            # Count unread messages from other user
            unread_count = Message.objects.filter(
                conversation_id=conv_id,
                sender=other_user,
                receiver=user,
                is_read=False
            ).count()

            conversation_list.append({
                'conversation_id': conv_id,
                'other_user': other_user,
                'last_message': last_message,
                'unread_count': unread_count
            })

        # Sort by last message time
        conversation_list.sort(key=lambda x: x['last_message'].created_at, reverse=True)

        serializer = ConversationSerializer(conversation_list, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def conversation_with(self, request):
        """Get messages with a specific user"""
        other_user_id = request.query_params.get('user_id')

        if not other_user_id:
            return Response({'detail': 'user_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            other_user = User.objects.get(id=other_user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Generate conversation ID
        conversation_id = Message.get_conversation_id(request.user.id, other_user.id)

        # Get messages
        messages = Message.objects.filter(conversation_id=conversation_id).order_by('created_at')

        # Mark received messages as read
        Message.objects.filter(
            conversation_id=conversation_id,
            receiver=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())

        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get total unread message count"""
        count = Message.objects.filter(receiver=request.user, is_read=False).count()
        return Response({'unread_count': count})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all messages in a conversation as read"""
        conversation_id = request.data.get('conversation_id')
        if not conversation_id:
            return Response({'detail': 'conversation_id required'}, status=400)

        Message.objects.filter(
            conversation_id=conversation_id,
            receiver=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())

        return Response({'status': 'success'})

    @action(detail=True, methods=['delete'])
    def soft_delete(self, request, pk=None):
        """Soft delete a message"""
        message = self.get_object()
        if message.sender != request.user:
            return Response({'detail': 'Not allowed'}, status=403)

        message.is_deleted = True
        message.deleted_at = timezone.now()
        message.save()

        return Response({'status': 'deleted'})