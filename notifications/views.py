from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'detail': 'Notification marked as read'})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'detail': f'{updated} notifications marked as read'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get unread notification count"""
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})

    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """Delete all notifications"""
        deleted = Notification.objects.filter(user=request.user).delete()
        return Response({'detail': f'{deleted[0]} notifications deleted'})

    @action(detail=True, methods=['delete'])
    def delete(self, request, pk=None):
        """Delete a single notification"""
        notification = self.get_object()
        notification.delete()
        return Response({'detail': 'Notification deleted'}, status=status.HTTP_204_NO_CONTENT)