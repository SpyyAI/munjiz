"""Mortgage credit-risk demo — views & API endpoints."""
from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import never_cache
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

from apps.agents.models import Agent
from apps.compliance.checks import collect_mock_compliance
from .models import Applicant, MortgageApplication, Document, AgentReview, FinalRecommendation
from .tasks import run_mortgage_review_task


REC_LABELS_AR = {
    'recommend_initial_approval':         'موافقة أوّلية',
    'recommend_approval_with_conditions': 'موافقة مشروطة',
    'needs_human_review':                 'موافقة مبدئية مشروطة',
    'not_recommended':                    'غير موصى',
}


# ---------------------------------------------------------------------------
# Page view — the dashboard
# ---------------------------------------------------------------------------
@never_cache
def mortgage_dashboard(request):
    """Single-page mortgage credit-risk dashboard."""
    agents = list(Agent.objects.filter(is_active=True).order_by('agent_type'))
    # Annotate each with the demo role labels for this domain
    role_map = {
        'analytics':    ('سارة',   'تقييم الجدارة الائتمانية',                '#FF1744', 'sara_initial'),
        'operations':   ('فهد',    'التحقق من الهوية والأهلية القانونية',     '#FF6D00', 'fahad_initial'),
        'customer':     ('خالد',   'قدرة العميل والدعم',                      '#2979FF', 'khalid_initial'),
        'queue':        ('نورة',   'تقييم العقار والضمان',                    '#AA00FF', 'nora_initial'),
        'orchestrator': ('المنسق', 'التوصية النهائية',                        '#00C853', 'orchestrator_initial'),
    }
    for a in agents:
        ar, role, color, _ = role_map.get(a.agent_type, (a.name_ar, a.role_ar, a.color, ''))
        a.display_name = ar
        a.display_role = role
        a.display_color = color

    applicants = list(Applicant.objects.all().order_by('applicant_id'))
    return render(request, 'mortgage/dashboard.html', {
        'agents': agents,
        'applicants': applicants,
    })


# ---------------------------------------------------------------------------
# REST: pre-built demo applicants + property scenarios
# ---------------------------------------------------------------------------
def list_demo_applicants(request):
    out = [{
        'applicant_id': a.applicant_id,
        'name_ar': a.name_ar,
        'national_id': a.national_id,
        'nationality': a.nationality,
        'monthly_salary_sar': float(a.monthly_salary_sar),
        'existing_obligations_sar': float(a.existing_monthly_obligations_sar),
        'employer_name': a.employer_name,
        'employer_sector': a.employer_sector,
        'notes': a.notes,
    } for a in Applicant.objects.all().order_by('applicant_id')]
    return JsonResponse({'applicants': out, 'demo_mode': True})


# ---------------------------------------------------------------------------
# REST: create + start review (single endpoint for demo simplicity)
# ---------------------------------------------------------------------------
@csrf_exempt
@require_POST
def create_application(request):
    """
    Create a new MortgageApplication from form data + an optional applicant_id
    to use as starting profile. Returns the application_id and a WS URL.
    """
    try:
        body = json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return HttpResponseBadRequest("invalid json")

    applicant_id = body.get('applicant_id')
    applicant = None
    if applicant_id:
        applicant = Applicant.objects.filter(applicant_id=applicant_id).first()
    if not applicant:
        # Build ad-hoc demo applicant
        applicant = Applicant.objects.create(
            applicant_id=body.get('applicant_id') or f"DEMO-A-{Applicant.objects.count() + 1:03d}",
            name_ar=body.get('name_ar') or 'متقدّم تجريبي',
            national_id=body.get('national_id', ''),
            nationality=body.get('nationality', 'saudi'),
            age=body.get('age', 35),
            monthly_salary_sar=body.get('monthly_salary_sar', 18000),
            existing_monthly_obligations_sar=body.get('existing_monthly_obligations_sar', 1500),
            employer_name=body.get('employer_name', 'شركة الراجحي للتقنية'),
            employer_sector=body.get('employer_sector', 'private'),
            employment_duration_months=body.get('employment_duration_months', 36),
        )

    app_id = body.get('application_id') or f"DEMO-APP-{MortgageApplication.objects.count() + 1:03d}"

    application = MortgageApplication.objects.create(
        application_id=app_id,
        applicant=applicant,
        requested_loan_sar=body.get('requested_loan_sar', 800000),
        requested_term_years=body.get('requested_term_years', 25),
        property_source=body.get('property_source', 'sakani'),
        property_id=body.get('property_id', 'SAKANI-2026-1042'),
        property_address=body.get('property_address', 'حي الياسمين، الرياض'),
        property_city=body.get('property_city', 'الرياض'),
        property_declared_price_sar=body.get('property_declared_price_sar', 1100000),
        property_type=body.get('property_type', 'فيلا دوبلكس'),
        # Khalid screening
        needs_general_support=body.get('needs_general_support', False),
        needs_legal_representative=body.get('needs_legal_representative', False),
        needs_accessibility=body.get('needs_accessibility', False),
        accessibility_types=body.get('accessibility_types', []),
        needs_translation=body.get('needs_translation', False),
        needs_extended_consent=body.get('needs_extended_consent', False),
        needs_independent_advice=body.get('needs_independent_advice', False),
        status='screening_complete',
    )

    return JsonResponse({
        'application_id': application.application_id,
        'ws_url': f'/ws/application/{application.application_id}/',
        'demo_mode': True,
        'note': 'هذا طلب تجريبي. لن تُجرى أيّ فحوصات حقيقية.',
    }, status=201)


# ---------------------------------------------------------------------------
# REST: pre-flight compliance preview (DEMO data, used to populate UI immediately)
# ---------------------------------------------------------------------------
def application_compliance_preview(request, application_id):
    application = get_object_or_404(MortgageApplication, application_id=application_id)
    snapshot = collect_mock_compliance(application.to_context())
    return JsonResponse({'application_id': application_id, 'compliance': snapshot, 'demo_mode': True})


# ---------------------------------------------------------------------------
# REST: trigger review (alternative to WS-based start)
# ---------------------------------------------------------------------------
@csrf_exempt
@require_POST
def trigger_review(request, application_id):
    application = get_object_or_404(MortgageApplication, application_id=application_id)
    run_mortgage_review_task.delay(application.application_id)
    return JsonResponse({
        'queued': True, 'application_id': application_id,
        'ws_url': f'/ws/application/{application_id}/',
    }, status=202)


# ---------------------------------------------------------------------------
# REST: final report
# ---------------------------------------------------------------------------
def application_report(request, application_id):
    application = get_object_or_404(MortgageApplication, application_id=application_id)
    reviews = [{
        'agent_type': r.agent_type,
        'order': r.order,
        'content': r.content,
        'structured': r.structured,
        'compliance_snapshot': r.compliance_snapshot,
        'created_at': r.created_at.isoformat(),
    } for r in application.reviews.all().order_by('order')]
    rec = getattr(application, 'final_recommendation', None)
    final = None
    if rec:
        final = {
            'recommendation': rec.recommendation,
            'recommendation_label_ar': REC_LABELS_AR.get(rec.recommendation, rec.recommendation),
            'summary_per_agent': rec.summary_per_agent,
            'conditions_if_any': rec.conditions_if_any,
            'residual_risks_for_human_review': rec.residual_risks_for_human_review,
            'escalation_reason': (rec.summary_per_agent or {}).get('escalation_reason', ''),
            'binding': rec.binding,
            'demo_mode': rec.demo_mode,
        }
    return JsonResponse({
        'application_id': application_id,
        'status': application.status,
        'reviews': reviews,
        'final_recommendation': final,
        'demo_disclaimer': (
            'هذه نتيجة تجريبية ضمن نظام عَرض. ليست قراراً ائتمانياً ملزماً قانونياً، '
            'ويجب أن يُراجعها مسؤول بشري في البنك قبل أيّ إجراء.'
        ),
    })


# ---------------------------------------------------------------------------
# REST: simple file upload (demo — stores in MEDIA dir)
# ---------------------------------------------------------------------------
@csrf_exempt
@require_POST
def upload_document(request, application_id):
    application = get_object_or_404(MortgageApplication, application_id=application_id)
    kind = request.POST.get('kind', 'other')
    f = request.FILES.get('file')
    if not f:
        return HttpResponseBadRequest('file required')
    Document.objects.create(
        application=application,
        kind=kind,
        original_filename=f.name,
        file=f,
        file_size_bytes=f.size,
        mime_type=f.content_type,
    )
    return JsonResponse({'ok': True, 'kind': kind, 'filename': f.name})
