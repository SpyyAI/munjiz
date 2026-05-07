from django.db import models
import uuid


class DailyReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey('branch.Branch', on_delete=models.CASCADE, related_name='daily_reports')
    date = models.DateField()
    customers_served = models.IntegerField(default=0)
    avg_wait_minutes = models.FloatField(default=0)
    sla_compliance_percent = models.FloatField(default=0)
    satisfaction_score = models.FloatField(default=0)
    self_service_percent = models.FloatField(default=0)
    decisions_made = models.IntegerField(default=0)
    sar_saved = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('branch', 'date')]
        ordering = ['-date']

    def __str__(self):
        return f"Report {self.branch.name_ar} — {self.date}"


class KPI(models.Model):
    branch = models.ForeignKey('branch.Branch', on_delete=models.CASCADE, related_name='kpis')
    name_ar = models.CharField(max_length=100)
    key = models.CharField(max_length=50)
    value = models.FloatField()
    unit = models.CharField(max_length=20, blank=True)
    target = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.name_ar}: {self.value}{self.unit}"


class Insight(models.Model):
    SEVERITY = [
        ('info', 'معلومة'),
        ('warning', 'تحذير'),
        ('critical', 'حرج'),
        ('opportunity', 'فرصة'),
    ]
    branch = models.ForeignKey('branch.Branch', on_delete=models.CASCADE, related_name='insights')
    title_ar = models.CharField(max_length=200)
    body_ar = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY, default='info')
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title_ar
