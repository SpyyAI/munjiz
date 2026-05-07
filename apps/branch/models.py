from django.db import models
import uuid


class Branch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch_id = models.CharField(max_length=20, unique=True)
    name_ar = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    address = models.TextField(blank=True)
    counters_total = models.IntegerField(default=8)
    kiosks_total = models.IntegerField(default=4)
    screens_total = models.IntegerField(default=3)
    waiting_capacity = models.IntegerField(default=40)
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name_ar


class Staff(models.Model):
    STATUS_CHOICES = [
        ('active', 'نشط'),
        ('on_break', 'في استراحة'),
        ('on_leave', 'في إجازة'),
        ('off_duty', 'خارج الدوام'),
    ]
    ROLE_CHOICES = [
        ('senior_teller', 'صراف رئيسي'),
        ('teller', 'صراف'),
        ('relationship_manager', 'مستشار علاقات'),
        ('branch_manager', 'مدير الفرع'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_id = models.CharField(max_length=10, unique=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='staff')
    name_ar = models.CharField(max_length=100)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    counter = models.CharField(max_length=10, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    avg_service_time_min = models.FloatField(default=5.0)
    performance_score = models.FloatField(default=4.0)
    customers_served_today = models.IntegerField(default=0)
    experience_years = models.IntegerField(default=1)
    break_started = models.DateTimeField(null=True, blank=True)
    expected_return = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['employee_id']

    def __str__(self):
        return f"{self.name_ar} ({self.get_role_display()})"


class Counter(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='counters')
    number = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)
    assigned_staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_counters')
    counter_type = models.CharField(max_length=20, default='general')

    def __str__(self):
        return f"شباك {self.number}"


class Kiosk(models.Model):
    STATUS_CHOICES = [
        ('available', 'متاح'),
        ('in_use', 'مستخدم'),
        ('maintenance', 'صيانة'),
    ]
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='kiosks')
    kiosk_id = models.CharField(max_length=10)
    location_ar = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    services_supported = models.JSONField(default=list)
    usage_today = models.IntegerField(default=0)

    def __str__(self):
        return f"كشك {self.kiosk_id}"


class DigitalScreen(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='screens')
    screen_id = models.CharField(max_length=10)
    location_ar = models.CharField(max_length=100)
    current_content = models.CharField(max_length=50, default='welcome_message')
    content_options = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"شاشة {self.screen_id}"
