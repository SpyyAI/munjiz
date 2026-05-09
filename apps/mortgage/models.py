"""
Mortgage application data model — DEMO scope.

⚠️ This stores demo applications, demo uploaded documents, demo screening answers,
and demo compliance results. No real customer data should ever be persisted in
this schema as-is. Production deployment would replace this with the bank's
authoritative LOS (Loan Origination System) tables.
"""
from django.db import models
import uuid


# ---------------------------------------------------------------------------
# Applicant — minimal demo profile
# ---------------------------------------------------------------------------
class Applicant(models.Model):
    NATIONALITY_CHOICES = [
        ('saudi', 'مواطن سعودي'),
        ('resident', 'مقيم'),
    ]
    EMPLOYER_SECTOR = [
        ('government', 'حكومي'),
        ('private', 'قطاع خاص'),
        ('semi_government', 'شبه حكومي'),
        ('self_employed', 'عمل حر'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    applicant_id = models.CharField(max_length=20, unique=True)   # DEMO-A-001
    name_ar = models.CharField(max_length=120)
    national_id = models.CharField(max_length=20, blank=True, default='')
    nationality = models.CharField(max_length=20, choices=NATIONALITY_CHOICES, default='saudi')
    age = models.IntegerField(default=35)
    monthly_salary_sar = models.DecimalField(max_digits=12, decimal_places=2)
    existing_monthly_obligations_sar = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    employer_name = models.CharField(max_length=120, blank=True)
    employer_sector = models.CharField(max_length=20, choices=EMPLOYER_SECTOR, default='private')
    employment_duration_months = models.IntegerField(default=24)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['applicant_id']

    def __str__(self):
        return f"{self.applicant_id} · {self.name_ar}"


# ---------------------------------------------------------------------------
# Mortgage Application — the core record
# ---------------------------------------------------------------------------
class MortgageApplication(models.Model):
    STATUS_CHOICES = [
        ('draft', 'مسودّة'),
        ('docs_uploaded', 'المستندات مرفوعة'),
        ('screening_complete', 'فحص الدعم مكتمل'),
        ('under_review', 'قيد المراجعة'),
        ('review_complete', 'المراجعة منتهية'),
    ]
    PROPERTY_SOURCE = [
        ('sakani', 'مشروع مُسَجَّل / Sakani'),
        ('independent', 'عقار مستقلّ'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application_id = models.CharField(max_length=20, unique=True)   # DEMO-APP-001
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='applications')
    requested_loan_sar = models.DecimalField(max_digits=14, decimal_places=2)
    requested_term_years = models.IntegerField(default=25)

    # Property
    property_source = models.CharField(max_length=20, choices=PROPERTY_SOURCE, default='sakani')
    property_id = models.CharField(max_length=40, blank=True)       # for sakani
    property_address = models.CharField(max_length=255, blank=True) # for independent
    property_city = models.CharField(max_length=60, default='الرياض')
    property_declared_price_sar = models.DecimalField(max_digits=14, decimal_places=2)
    property_type = models.CharField(max_length=60, default='فيلا')

    # Khalid screening (voluntary, ethical)
    needs_general_support = models.BooleanField(default=False)
    needs_legal_representative = models.BooleanField(default=False)
    needs_accessibility = models.BooleanField(default=False)
    accessibility_types = models.JSONField(default=list)        # e.g. ["sign_language_arabic"]
    needs_translation = models.BooleanField(default=False)
    needs_extended_consent = models.BooleanField(default=False)
    needs_independent_advice = models.BooleanField(default=False)

    # Workflow
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.application_id} · {self.applicant.name_ar}"

    def to_context(self) -> dict:
        """Build the dict structure that mock compliance + agents consume."""
        return {
            "application": {
                "id": self.application_id,
                "requested_loan_sar": float(self.requested_loan_sar),
                "requested_term_years": self.requested_term_years,
            },
            "applicant": {
                "id": self.applicant.applicant_id,
                "name_ar": self.applicant.name_ar,
                "nationality": self.applicant.nationality,
                "age": self.applicant.age,
                "monthly_salary_sar": float(self.applicant.monthly_salary_sar),
                "existing_monthly_obligations_sar": float(self.applicant.existing_monthly_obligations_sar),
                "employer_name": self.applicant.employer_name,
                "employer_sector": self.applicant.employer_sector,
                "employment_duration_months": self.applicant.employment_duration_months,
            },
            "property": {
                "source": self.property_source,
                "property_id": self.property_id,
                "address": self.property_address,
                "city": self.property_city,
                "declared_price_sar": float(self.property_declared_price_sar),
                "property_type": self.property_type,
            },
            "screening_answers": {
                "needs_general_support": self.needs_general_support,
                "needs_legal_representative": self.needs_legal_representative,
                "needs_accessibility": self.needs_accessibility,
                "accessibility_types": self.accessibility_types,
                "needs_translation": self.needs_translation,
                "needs_extended_consent": self.needs_extended_consent,
                "needs_independent_advice": self.needs_independent_advice,
            },
            "documents": [
                {"kind": d.kind, "filename": d.original_filename}
                for d in self.documents.all()
            ],
        }


# ---------------------------------------------------------------------------
# Uploaded document
# ---------------------------------------------------------------------------
class Document(models.Model):
    DOC_KINDS = [
        ('national_id',     'الهوية الوطنية'),
        ('salary_slip',     'تعريف بالراتب'),
        ('employment_letter', 'خطاب تعريف'),
        ('bank_statement',  'كشف حساب بنكي (٣ أشهر)'),
        ('property_deed',   'صك ملكية / عرض'),
        ('property_listing', 'بيان مشروع Sakani'),
        ('other',           'مستند آخر'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        MortgageApplication, on_delete=models.CASCADE, related_name='documents'
    )
    kind = models.CharField(max_length=30, choices=DOC_KINDS)
    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='mortgage_docs/%Y/%m/', blank=True, null=True)
    file_size_bytes = models.IntegerField(default=0)
    mime_type = models.CharField(max_length=80, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['kind', 'uploaded_at']

    def __str__(self):
        return f"{self.application.application_id} · {self.get_kind_display()}"


# ---------------------------------------------------------------------------
# Per-agent review record
# ---------------------------------------------------------------------------
class AgentReview(models.Model):
    AGENT_TYPES = [
        ('analytics',    'سارة — الجدارة الائتمانية'),
        ('operations',   'فهد — الهوية والقانوني'),
        ('customer',     'خالد — قدرة العميل والدعم'),
        ('queue',        'نورة — تقييم العقار'),
        ('orchestrator', 'المنسق — التوصية النهائية'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        MortgageApplication, on_delete=models.CASCADE, related_name='reviews'
    )
    agent_type = models.CharField(max_length=20, choices=AGENT_TYPES)
    order = models.IntegerField(default=0)

    # The agent's full Arabic narrative
    content = models.TextField()

    # Structured findings (parsed JSON block from the prompt output)
    structured = models.JSONField(default=dict, blank=True)

    # The mock compliance snapshot that was passed to this agent
    compliance_snapshot = models.JSONField(default=dict, blank=True)

    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.application.application_id} · {self.get_agent_type_display()}"


# ---------------------------------------------------------------------------
# Final recommendation (Orchestrator's structured output, denormalised)
# ---------------------------------------------------------------------------
class FinalRecommendation(models.Model):
    RECOMMENDATIONS = [
        ('recommend_initial_approval',          'توصية بالموافقة الأوّلية'),
        ('recommend_approval_with_conditions',  'توصية بموافقة مشروطة'),
        ('needs_human_review',                  'يحتاج مراجعة بشرية'),
        ('not_recommended',                     'غير موصى بها'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.OneToOneField(
        MortgageApplication, on_delete=models.CASCADE, related_name='final_recommendation'
    )
    recommendation = models.CharField(max_length=50, choices=RECOMMENDATIONS)
    summary_per_agent = models.JSONField(default=dict)
    conditions_if_any = models.JSONField(default=list)
    residual_risks_for_human_review = models.JSONField(default=list)
    binding = models.BooleanField(default=False)
    demo_mode = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.application.application_id} · {self.get_recommendation_display()}"
