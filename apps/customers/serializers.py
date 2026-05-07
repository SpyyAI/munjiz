from rest_framework import serializers
from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    segment_display = serializers.CharField(source='get_segment_display', read_only=True)
    churn_risk_display = serializers.CharField(source='get_churn_risk_display', read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'customer_id', 'name_ar', 'alias', 'segment', 'segment_display',
                  'phone', 'annual_value_sar', 'avg_monthly_transactions', 'preferred_services',
                  'visits_last_6m', 'wait_tolerance_min', 'satisfaction_score', 'nps_score',
                  'churn_risk', 'churn_risk_display', 'preferred_channel', 'customer_since', 'notes']
