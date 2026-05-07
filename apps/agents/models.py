from django.db import models
import uuid


class Agent(models.Model):
    AGENT_TYPES = [
        ('orchestrator', 'المنسق'),
        ('customer', 'خالد — العملاء'),
        ('queue', 'نورة — الطوابير'),
        ('operations', 'فهد — العمليات'),
        ('analytics', 'سارة — التحليلات'),
    ]
    STATUS_CHOICES = [
        ('idle', 'خامل'),
        ('thinking', 'يفكر'),
        ('analyzing', 'يحلل'),
        ('sending', 'يرسل'),
        ('waiting', 'منتظر'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent_type = models.CharField(max_length=20, choices=AGENT_TYPES, unique=True)
    name_ar = models.CharField(max_length=50)
    name_en = models.CharField(max_length=50)
    role_ar = models.CharField(max_length=100)
    color = models.CharField(max_length=7)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idle')
    current_task = models.CharField(max_length=200, blank=True)
    system_prompt = models.TextField()
    model_name = models.CharField(max_length=100, default='qwen/qwen-2.5-72b-instruct:free')
    temperature = models.FloatField(default=0.5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['agent_type']

    def __str__(self):
        return f"{self.name_ar} ({self.agent_type})"


class Scenario(models.Model):
    SCENARIO_TYPES = [
        ('routine', 'روتيني'),
        ('customer_request', 'طلب عميل'),
        ('operational_crisis', 'أزمة تشغيلية'),
        ('cultural', 'ثقافي'),
        ('opportunity', 'فرصة'),
        ('customer_crisis', 'أزمة عميل'),
        ('reporting', 'تقارير'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scenario_id = models.CharField(max_length=10, unique=True)
    name_ar = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100, blank=True)
    scenario_type = models.CharField(max_length=20, choices=SCENARIO_TYPES)
    time = models.CharField(max_length=10, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=5, default='⚡')
    is_recommended = models.BooleanField(default=False)
    tension_level = models.CharField(max_length=10, default='medium')
    is_active = models.BooleanField(default=True)
    use_ai = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scenario_id']

    def __str__(self):
        return f"{self.scenario_id}: {self.name_ar}"


class AgentMessage(models.Model):
    PRIORITY_CHOICES = [
        ('critical', 'حرج'),
        ('high', 'عالي'),
        ('medium', 'متوسط'),
        ('low', 'منخفض'),
    ]
    MESSAGE_TYPES = [
        ('alert', 'تنبيه'),
        ('analysis', 'تحليل'),
        ('suggestion', 'اقتراح'),
        ('decision', 'قرار'),
        ('update', 'تحديث'),
        ('question', 'سؤال'),
        ('confirmation', 'تأكيد'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='messages')
    from_agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='sent_messages')
    to_agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)
    to_broadcast = models.BooleanField(default=False)
    content = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='update')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_ai_generated = models.BooleanField(default=False)
    raw_data = models.JSONField(null=True, blank=True)
    order = models.IntegerField(default=0)
    delay_ms = models.IntegerField(default=1500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.from_agent.name_ar} → {self.content[:50]}"


class Decision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='decisions')
    decision_text = models.TextField()
    reasoning = models.TextField()
    agents_consulted = models.ManyToManyField(Agent, related_name='consulted_decisions', blank=True)
    authority_level = models.CharField(max_length=20, default='auto_approved')
    was_escalated = models.BooleanField(default=False)
    outcome = models.TextField(blank=True)
    financial_impact_sar = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Decision: {self.decision_text[:50]}"
