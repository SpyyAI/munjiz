from django.urls import path
from .views import (
    mortgage_dashboard,
    list_demo_applicants,
    create_application,
    application_compliance_preview,
    trigger_review,
    application_report,
    upload_document,
)

app_name = 'mortgage'

urlpatterns = [
    # Page
    path('', mortgage_dashboard, name='dashboard'),

    # API
    path('api/applicants/', list_demo_applicants, name='list-applicants'),
    path('api/applications/', create_application, name='create-application'),
    path('api/applications/<str:application_id>/compliance-preview/',
         application_compliance_preview, name='compliance-preview'),
    path('api/applications/<str:application_id>/trigger/',
         trigger_review, name='trigger-review'),
    path('api/applications/<str:application_id>/report/',
         application_report, name='application-report'),
    path('api/applications/<str:application_id>/documents/',
         upload_document, name='upload-document'),
]
