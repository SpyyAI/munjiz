from rest_framework import serializers
from .models import Branch, Staff, Counter, Kiosk, DigitalScreen


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'


class StaffSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Staff
        fields = ['id', 'employee_id', 'name_ar', 'role', 'role_display', 'counter',
                  'status', 'status_display', 'avg_service_time_min', 'performance_score',
                  'customers_served_today', 'experience_years']


class CounterSerializer(serializers.ModelSerializer):
    assigned_staff_name = serializers.CharField(source='assigned_staff.name_ar', read_only=True)

    class Meta:
        model = Counter
        fields = ['id', 'number', 'counter_type', 'is_active', 'assigned_staff_name']


class KioskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kiosk
        fields = ['id', 'kiosk_id', 'location_ar', 'status', 'services_supported', 'usage_today']


class DigitalScreenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DigitalScreen
        fields = ['id', 'screen_id', 'location_ar', 'current_content', 'content_options', 'is_active']
