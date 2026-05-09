from django.contrib import admin
from .models import Applicant, MortgageApplication, Document, AgentReview, FinalRecommendation


@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ('applicant_id', 'name_ar', 'nationality', 'monthly_salary_sar', 'employer_name')
    search_fields = ('applicant_id', 'name_ar', 'employer_name')
    list_filter = ('nationality', 'employer_sector')


@admin.register(MortgageApplication)
class MortgageApplicationAdmin(admin.ModelAdmin):
    list_display = ('application_id', 'applicant', 'requested_loan_sar', 'property_source', 'status', 'created_at')
    list_filter = ('status', 'property_source', 'property_city')
    search_fields = ('application_id', 'applicant__name_ar', 'applicant__applicant_id')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('application', 'kind', 'original_filename', 'uploaded_at')
    list_filter = ('kind',)


@admin.register(AgentReview)
class AgentReviewAdmin(admin.ModelAdmin):
    list_display = ('application', 'agent_type', 'order', 'is_demo', 'created_at')
    list_filter = ('agent_type', 'is_demo')


@admin.register(FinalRecommendation)
class FinalRecommendationAdmin(admin.ModelAdmin):
    list_display = ('application', 'recommendation', 'demo_mode', 'created_at')
    list_filter = ('recommendation', 'demo_mode')
