from django.apps import AppConfig


class MortgageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.mortgage'
    label = 'mortgage'
    verbose_name = 'طلبات التمويل العقاري (Mortgage Applications)'
