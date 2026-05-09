"""Celery tasks that run agents asynchronously. AI path only."""
import logging
from celery import shared_task

from .models import Scenario
from .engine import AgentEngine

logger = logging.getLogger(__name__)


def _build_context(branch_id: str = 'RYD-OLY-042') -> dict:
    """Build the context dictionary fed to all agents from current DB state."""
    from apps.branch.models import Branch, Staff, Kiosk
    from apps.customers.models import Customer
    from apps.queue_system.models import QueueSnapshot, SLAConfig

    try:
        branch = Branch.objects.get(branch_id=branch_id)
    except Branch.DoesNotExist:
        return {}

    staff = list(Staff.objects.filter(branch=branch).values(
        'employee_id', 'name_ar', 'role', 'counter', 'status',
        'avg_service_time_min', 'performance_score', 'customers_served_today',
    ))
    customers = list(Customer.objects.all().values(
        'customer_id', 'name_ar', 'alias', 'segment', 'annual_value_sar',
        'visits_last_6m', 'wait_tolerance_min', 'satisfaction_score',
        'churn_risk', 'notes',
    ))
    kiosks = list(Kiosk.objects.filter(branch=branch).values(
        'kiosk_id', 'location_ar', 'status', 'usage_today',
    ))
    sla = list(SLAConfig.objects.filter(branch=branch).values(
        'segment', 'max_wait_minutes', 'penalty_sar', 'satisfaction_target',
    ))
    snap = QueueSnapshot.objects.filter(branch=branch).order_by('-timestamp').first()

    return {
        'branch': {'name': branch.name_ar, 'city': branch.city, 'id': branch.branch_id},
        'staff': staff,
        'customers': customers,
        'kiosks': kiosks,
        'sla_rules': sla,
        'queue_state': {
            'total_waiting': snap.total_waiting if snap else 34,
            'total_serving': snap.total_serving if snap else 6,
            'avg_wait_minutes': snap.avg_wait_minutes if snap else 18.0,
            'sla_compliance': snap.sla_compliance_percent if snap else 78,
            'kiosk_usage_percent': snap.kiosk_usage_percent if snap else 42,
        },
        'historical': {
            'avg_thursday_visitors': 380,
            'salary_day_multiplier': 1.8,
            'peak_hours': ['11:00-13:00', '16:00-18:00'],
        },
        'prayer_times': {'dhuhr': '12:15', 'asr': '15:42', 'maghrib': '18:24'},
        'current_time': '11:30',
        'day_context': 'خميس — نهاية الشهر — يوم رواتب',
    }


def _has_valid_llm_key() -> bool:
    from django.conf import settings as s
    key = s.OPENROUTER_API_KEY or ''
    return bool(key) and not key.startswith('sk-no-key') and 'your-key-here' not in key


def _broadcast_lifecycle(scenario, phase: str):
    """Broadcast scenario_started / scenario_ended events to all dashboard tabs."""
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    layer = get_channel_layer()
    if not layer:
        return
    async_to_sync(layer.group_send)(
        'dashboard',
        {
            'type': 'scenario.lifecycle',
            'phase': phase,
            'scenario': {
                'scenario_id': scenario.scenario_id,
                'name_ar': scenario.name_ar,
                'mode': 'ai',
            },
        },
    )


@shared_task
def run_scenario_task(scenario_id: str):
    """Run a scenario via the multi-agent AI engine."""
    try:
        scenario = Scenario.objects.get(scenario_id=scenario_id)
    except Scenario.DoesNotExist:
        logger.error("Scenario %s not found", scenario_id)
        return

    _broadcast_lifecycle(scenario, 'scenario_started')
    try:
        AgentEngine().run_scenario_with_ai(scenario, _build_context())
    except Exception:
        logger.exception("Scenario %s aborted", scenario_id)
    finally:
        _broadcast_lifecycle(scenario, 'scenario_ended')


@shared_task
def run_scenario_with_custom_data_task(scenario_id: str, custom_data: dict):
    """Run scenario with overridden context — exposed via Data Editor in dashboard."""
    try:
        scenario = Scenario.objects.get(scenario_id=scenario_id)
    except Scenario.DoesNotExist:
        return
    context = _build_context()
    context.update(custom_data or {})

    _broadcast_lifecycle(scenario, 'scenario_started')
    try:
        AgentEngine().run_scenario_with_ai(scenario, context)
    except Exception:
        logger.exception("Custom-data scenario %s aborted", scenario_id)
    finally:
        _broadcast_lifecycle(scenario, 'scenario_ended')
