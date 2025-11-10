from rest_framework import serializers
from .models import Report
from users.serializers import UserListSerializer


class ReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['reported_type', 'reported_id', 'reason', 'description']

    def validate(self, attrs):
        # Check if user has already reported this entity
        request = self.context['request']
        existing = Report.objects.filter(
            reporter=request.user,
            reported_type=attrs['reported_type'],
            reported_id=attrs['reported_id']
        ).exists()

        if existing:
            raise serializers.ValidationError("You have already reported this")

        return attrs

    def create(self, validated_data):
        request = self.context['request']
        return Report.objects.create(reporter=request.user, **validated_data)


class ReportDetailSerializer(serializers.ModelSerializer):
    reporter = UserListSerializer(read_only=True)
    resolved_by = UserListSerializer(read_only=True)

    class Meta:
        model = Report
        fields = [
            'id', 'reporter', 'reported_type', 'reported_id', 'reason',
            'description', 'status', 'admin_note', 'resolved_by',
            'resolved_at', 'created_at'
        ]
        read_only_fields = ['id', 'reporter', 'resolved_by', 'resolved_at', 'created_at']