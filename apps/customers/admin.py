from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'name_ar', 'segment', 'annual_value_sar', 'churn_risk', 'satisfaction_score')
    list_filter = ('segment', 'churn_risk')
    search_fields = ('customer_id', 'name_ar', 'alias')
