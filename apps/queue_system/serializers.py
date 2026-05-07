from rest_framework import serializers
from .models import QueueEntry, QueueSnapshot, SLAConfig


class QueueSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueueSnapshot
        fields = '__all__'


class SLAConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SLAConfig
        fields = '__all__'


class QueueEntrySerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name_ar', read_only=True)

    class Meta:
        model = QueueEntry
        fields = ['id', 'ticket_number', 'service_type', 'is_simple', 'priority',
                  'status', 'wait_start', 'serve_start', 'completed_at',
                  'redirected_to_kiosk', 'customer_name']
