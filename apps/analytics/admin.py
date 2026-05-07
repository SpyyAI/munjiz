from django.contrib import admin
from .models import DailyReport, KPI, Insight


@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    list_display = ('branch', 'date', 'customers_served', 'sla_compliance_percent', 'satisfaction_score')
    list_filter = ('branch', 'date')


@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'key', 'value', 'unit', 'timestamp')
    list_filter = ('branch', 'key')


@admin.register(Insight)
class InsightAdmin(admin.ModelAdmin):
    list_display = ('title_ar', 'severity', 'is_resolved', 'created_at')
    list_filter = ('severity', 'is_resolved')
