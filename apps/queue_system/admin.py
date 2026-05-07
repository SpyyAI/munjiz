from django.contrib import admin
from .models import QueueEntry, QueueSnapshot, SLAConfig


@admin.register(QueueEntry)
class QueueEntryAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'service_type', 'status', 'priority', 'wait_start')
    list_filter = ('status', 'service_type', 'is_simple')


@admin.register(QueueSnapshot)
class QueueSnapshotAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'total_waiting', 'avg_wait_minutes', 'sla_compliance_percent')
    list_filter = ('branch',)


@admin.register(SLAConfig)
class SLAConfigAdmin(admin.ModelAdmin):
    list_display = ('segment', 'max_wait_minutes', 'penalty_sar', 'satisfaction_target')
    list_filter = ('segment', 'branch')
