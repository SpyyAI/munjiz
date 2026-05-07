from datetime import date, timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.queue_system.models import QueueSnapshot
from apps.branch.models import Branch
from apps.agents.models import AgentMessage, Decision
from .models import DailyReport, KPI, Insight
from .serializers import KPISerializer, InsightSerializer


def _live_kpis():
    """Compute live KPIs on the fly from the latest snapshot + counts."""
    snap = QueueSnapshot.objects.order_by('-timestamp').first()
    branch = Branch.objects.first()
    waiting = snap.total_waiting if snap else 0
    avg_wait = snap.avg_wait_minutes if snap else 0.0
    sla_pct = snap.sla_compliance_percent if snap else 0.0
    kiosk_pct = snap.kiosk_usage_percent if snap else 0.0
    decisions_today = Decision.objects.filter(created_at__date=date.today()).count()
    msgs_today = AgentMessage.objects.filter(created_at__date=date.today()).count()
    return [
        {'key': 'customers_in_branch', 'name_ar': 'العملاء بالفرع', 'value': waiting, 'unit': '', 'target': 30},
        {'key': 'avg_wait_minutes', 'name_ar': 'متوسط الانتظار', 'value': round(avg_wait, 1), 'unit': 'دقيقة', 'target': 10},
        {'key': 'sla_compliance', 'name_ar': 'الالتزام بـ SLA', 'value': round(sla_pct, 1), 'unit': '٪', 'target': 95},
        {'key': 'satisfaction', 'name_ar': 'رضا العملاء', 'value': 4.6, 'unit': '/5', 'target': 4.5},
        {'key': 'self_service', 'name_ar': 'الخدمة الذاتية', 'value': round(kiosk_pct, 1), 'unit': '٪', 'target': 50},
        {'key': 'decisions_today', 'name_ar': 'قرارات اليوم', 'value': decisions_today + msgs_today, 'unit': '', 'target': None},
    ]


@api_view(['GET'])
def today_kpis(request):
    return Response({'kpis': _live_kpis()})


@api_view(['GET'])
def comparison(request):
    today = date.today()
    yesterday = today - timedelta(days=1)
    branch = Branch.objects.first()
    today_rep = DailyReport.objects.filter(branch=branch, date=today).first()
    yest_rep = DailyReport.objects.filter(branch=branch, date=yesterday).first()
    return Response({
        'today': today_rep and {
            'customers_served': today_rep.customers_served,
            'avg_wait_minutes': today_rep.avg_wait_minutes,
            'sla_compliance_percent': today_rep.sla_compliance_percent,
            'satisfaction_score': today_rep.satisfaction_score,
        },
        'yesterday': yest_rep and {
            'customers_served': yest_rep.customers_served,
            'avg_wait_minutes': yest_rep.avg_wait_minutes,
            'sla_compliance_percent': yest_rep.sla_compliance_percent,
            'satisfaction_score': yest_rep.satisfaction_score,
        },
    })


@api_view(['GET'])
def insights(request):
    return Response(InsightSerializer(Insight.objects.filter(is_resolved=False)[:10], many=True).data)
