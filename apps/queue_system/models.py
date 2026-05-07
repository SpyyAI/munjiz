from django.db import models
import uuid


class QueueEntry(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'منتظر'),
        ('serving', 'يخدم'),
        ('completed', 'مكتمل'),
        ('redirected', 'محول'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey('customers.Customer', on_delete=models.SET_NULL, null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', on_delete=models.CASCADE)
    service_type = models.CharField(max_length=50)
    is_simple = models.BooleanField(default=False)
    ticket_number = models.IntegerField()
    priority = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    wait_start = models.DateTimeField(auto_now_add=True)
    serve_start = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    assigned_counter = models.ForeignKey('branch.Counter', on_delete=models.SET_NULL, null=True, blank=True)
    redirected_to_kiosk = models.BooleanField(default=False)

    class Meta:
        ordering = ['-priority', 'wait_start']


class QueueSnapshot(models.Model):
    branch = models.ForeignKey('branch.Branch', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    total_waiting = models.IntegerField()
    total_serving = models.IntegerField()
    avg_wait_minutes = models.FloatField()
    max_wait_minutes = models.FloatField()
    sla_compliance_percent = models.FloatField()
    kiosk_usage_percent = models.FloatField(default=0)
    staff_utilization_percent = models.FloatField(default=0)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Snapshot @ {self.timestamp:%H:%M} — {self.total_waiting} waiting"


class SLAConfig(models.Model):
    branch = models.ForeignKey('branch.Branch', on_delete=models.CASCADE)
    segment = models.CharField(max_length=10)
    max_wait_minutes = models.IntegerField()
    penalty_sar = models.DecimalField(max_digits=8, decimal_places=2)
    satisfaction_target = models.FloatField(default=4.5)

    class Meta:
        unique_together = [('branch', 'segment')]

    def __str__(self):
        return f"SLA {self.segment} — {self.max_wait_minutes}min"
