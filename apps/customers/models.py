from django.db import models
import uuid


class Customer(models.Model):
    SEGMENT_CHOICES = [
        ('vip', 'VIP'),
        ('premium', 'Premium'),
        ('standard', 'Standard'),
    ]
    CHURN_RISK = [
        ('very_low', 'منخفض جداً'),
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'عالي'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_id = models.CharField(max_length=10, unique=True)
    name_ar = models.CharField(max_length=100)
    alias = models.CharField(max_length=50, blank=True)
    segment = models.CharField(max_length=10, choices=SEGMENT_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    annual_value_sar = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avg_monthly_transactions = models.IntegerField(default=0)
    preferred_services = models.JSONField(default=list)
    visits_last_6m = models.IntegerField(default=0)
    wait_tolerance_min = models.IntegerField(default=15)
    satisfaction_score = models.FloatField(default=4.0)
    nps_score = models.IntegerField(default=7)
    churn_risk = models.CharField(max_length=10, choices=CHURN_RISK, default='low')
    preferred_channel = models.CharField(max_length=20, default='WhatsApp')
    customer_since = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-annual_value_sar']

    def __str__(self):
        return f"{self.name_ar} ({self.segment})"
