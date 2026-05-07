from rest_framework import serializers
from .models import DailyReport, KPI, Insight


class DailyReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyReport
        fields = '__all__'


class KPISerializer(serializers.ModelSerializer):
    class Meta:
        model = KPI
        fields = ['id', 'name_ar', 'key', 'value', 'unit', 'target', 'timestamp']


class InsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Insight
        fields = '__all__'
