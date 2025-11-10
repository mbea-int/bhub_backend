from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.utils import timezone
from .models import Report
from .serializers import ReportCreateSerializer, ReportDetailSerializer
from utils.permissions import IsAdminUser


class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            # Admins see all reports
            return Report.objects.all()
        # Regular users only see their own reports
        return Report.objects.filter(reporter=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return ReportCreateSerializer
        return ReportDetailSerializer

    @method_decorator(ratelimit(key='user', rate='10/1d', method='POST'))
    def create(self, request, *args, **kwargs):
        """Create report (rate limited to 10 per day)"""
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def review(self, request, pk=None):
        """Mark report as under review (admin only)"""
        report = self.get_object()
        report.status = 'reviewing'
        report.save()
        return Response({'detail': 'Report marked as under review'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def resolve(self, request, pk=None):
        """Resolve report (admin only)"""
        report = self.get_object()
        admin_note = request.data.get('admin_note', '')

        report.status = 'resolved'
        report.admin_note = admin_note
        report.resolved_by = request.user
        report.resolved_at = timezone.now()
        report.save()

        return Response({'detail': 'Report resolved'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def dismiss(self, request, pk=None):
        """Dismiss report (admin only)"""
        report = self.get_object()
        admin_note = request.data.get('admin_note', '')

        report.status = 'dismissed'
        report.admin_note = admin_note
        report.resolved_by = request.user
        report.resolved_at = timezone.now()
        report.save()

        return Response({'detail': 'Report dismissed'})

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def pending(self, request):
        """Get pending reports (admin only)"""
        reports = Report.objects.filter(status='pending')
        serializer = self.get_serializer(reports, many=True)
        return Response(serializer.data)