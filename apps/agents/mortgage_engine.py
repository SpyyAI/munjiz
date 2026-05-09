"""
Mortgage credit-risk review engine.

Drives the 5-agent sequential review of a MortgageApplication:
  Sara → Fahad → Khalid → Nora → Orchestrator

Each agent reads:
  - the application context (applicant + property + screening)
  - the mock compliance snapshot relevant to its domain
  - previous agents' findings (so later agents can reference earlier verdicts)

Each agent emits both narrative Arabic prose AND a JSON-structured findings block,
which we parse and persist as `AgentReview.structured`.

⚠️ DEMO MODE — every compliance datum is fabricated by apps.compliance.checks.
The Orchestrator's recommendation is a non-binding suggestion to a human officer.
"""
from __future__ import annotations

import json
import logging
import re

from openai import OpenAI
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from apps.agents.models import Agent
from apps.agents.prompts import get_agent_prompt
from apps.compliance.checks import collect_mock_compliance
from apps.mortgage.models import MortgageApplication, AgentReview, FinalRecommendation

logger = logging.getLogger(__name__)


class MortgageReviewError(Exception):
    """Raised when the LLM provider returns an error or empty content."""


# Order is semantically important: data → constraints → human → solution → decision
AGENT_SEQUENCE = ['analytics', 'operations', 'customer', 'queue', 'orchestrator']

AGENT_LABELS_AR = {
    'analytics':    'سارة',
    'operations':   'فهد',
    'customer':     'خالد',
    'queue':        'نورة',
    'orchestrator': 'المنسق',
}


# ---------------------------------------------------------------------------
# JSON extraction helper — agents include a fenced ```json``` block at the end
# ---------------------------------------------------------------------------
_JSON_BLOCK_RE = re.compile(r'```json\s*(\{.*?\})\s*```', re.DOTALL)


def _extract_structured(text: str) -> dict:
    """Pull the trailing JSON block from an agent's response. Returns {} on failure."""
    if not text:
        return {}
    m = _JSON_BLOCK_RE.search(text)
    if not m:
        return {}
    try:
        return json.loads(m.group(1))
    except (json.JSONDecodeError, ValueError):
        return {}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
class MortgageReviewEngine:

    def __init__(self):
        self.client = OpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY or 'sk-no-key',
        )
        self.channel_layer = get_channel_layer()

    # -------------------------------------------------------------------
    # Public entry point
    # -------------------------------------------------------------------
    def run(self, application: MortgageApplication) -> FinalRecommendation:
        """Run the full 5-agent review on a MortgageApplication."""
        application.status = 'under_review'
        application.save(update_fields=['status'])

        # Build the canonical context once
        app_context = application.to_context()
        compliance = collect_mock_compliance(app_context)

        # Hot-load agent rows once
        agents_by_type = {a.agent_type: a for a in Agent.objects.filter(is_active=True)}

        previous_findings: dict[str, dict] = {}

        self._broadcast_lifecycle(application, 'review_started')

        for order, agent_type in enumerate(AGENT_SEQUENCE, start=1):
            agent = agents_by_type.get(agent_type)
            if not agent:
                logger.warning("No active Agent row for type=%s; skipping", agent_type)
                continue

            self._broadcast_status(application, agent, 'thinking')

            content = self._call_agent(
                agent=agent,
                application=application,
                app_context=app_context,
                compliance=compliance,
                previous=previous_findings,
            )
            structured = _extract_structured(content)

            review = AgentReview.objects.create(
                application=application,
                agent_type=agent_type,
                order=order,
                content=content,
                structured=structured,
                compliance_snapshot=self._snapshot_for(agent_type, compliance),
                is_demo=True,
            )
            previous_findings[agent_type] = structured

            self._broadcast_status(application, agent, 'idle')
            self._broadcast_review(application, agent, review)

        # Persist Orchestrator's final recommendation as a denormalised record
        orch_findings = previous_findings.get('orchestrator', {})
        # Stash escalation_reason inside summary_per_agent so we don't need a new column.
        summary = dict(orch_findings.get('summary_per_agent', {}) or {})
        if orch_findings.get('escalation_reason'):
            summary['escalation_reason'] = orch_findings['escalation_reason']
        rec = FinalRecommendation.objects.update_or_create(
            application=application,
            defaults={
                'recommendation': orch_findings.get('recommendation', 'needs_human_review'),
                'summary_per_agent': summary,
                'conditions_if_any': orch_findings.get('conditions_if_any', []),
                'residual_risks_for_human_review': orch_findings.get('residual_risks_for_human_review', []),
                'binding': False,
                'demo_mode': True,
            },
        )[0]

        application.status = 'review_complete'
        application.save(update_fields=['status'])
        self._broadcast_lifecycle(application, 'review_complete', recommendation=rec.recommendation)
        return rec

    # -------------------------------------------------------------------
    # Internal: build prompt & call LLM
    # -------------------------------------------------------------------
    def _call_agent(self, agent, application, app_context, compliance, previous):
        system_prompt = agent.system_prompt or get_agent_prompt(agent.agent_type)
        user_message = self._build_user_message(
            agent.agent_type, app_context, compliance, previous
        )

        try:
            response = self.client.chat.completions.create(
                model=agent.model_name or settings.LLM_MODEL_DEFAULT,
                max_tokens=1800 if agent.agent_type == 'orchestrator' else 1100,
                temperature=agent.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                extra_headers={
                    "HTTP-Referer": "https://munjiz.ai",
                    "X-Title": "Munjiz Mortgage Demo",
                },
            )
            result = response.choices[0].message.content or ''
            if not result.strip():
                raise MortgageReviewError(f"Empty content from {agent.name_ar}")
            return result
        except MortgageReviewError:
            raise
        except Exception as e:
            logger.exception("LLM call failed for %s: %s", agent.name_ar, e)
            raise MortgageReviewError(str(e)) from e

    # -------------------------------------------------------------------
    def _build_user_message(self, agent_type, app_context, compliance, previous):
        """Each agent gets a tailored prompt with only the compliance signals it needs."""
        applicant = app_context["applicant"]
        prop = app_context["property"]
        application = app_context["application"]

        header = (
            "## ⚠️ DEMO MODE\n"
            "كل بيانات الامتثال أدناه مُحاكاة تجريبية. لم تُستدعَ SIMAH / SDAIA / "
            "ABD / Sakani / البورصة العقارية حقيقياً. الهدف عرض المعمارية فقط.\n\n"
            "## ملخّص الطلب\n"
            f"- رقم الطلب: {application['id']}\n"
            f"- المتقدّم: {applicant['name_ar']} ({applicant['nationality']})، العمر {applicant['age']}\n"
            f"- الراتب الشهري: {applicant['monthly_salary_sar']:,.0f} ريال\n"
            f"- التزامات شهرية حالية: {applicant['existing_monthly_obligations_sar']:,.0f} ريال\n"
            f"- جهة العمل: {applicant['employer_name']} ({applicant['employer_sector']})\n"
            f"- مدّة الخدمة: {applicant['employment_duration_months']} شهراً\n"
            f"- مبلغ القرض المطلوب: {application['requested_loan_sar']:,.0f} ريال\n"
            f"- مدّة القرض: {application['requested_term_years']} سنة\n"
            f"- العقار: {prop['property_type']} في {prop['city']}، "
            f"المصدر: {prop['source']}، السعر المُعلَن: {prop['declared_price_sar']:,.0f} ريال\n"
        )

        # Per-agent compliance carve-outs
        if agent_type == 'analytics':
            payload = {"simah": compliance.get("simah")}
            instruction = "حلّلي SIMAH-style data + الراتب + الالتزامات + DBR بعد القرض المُقترَح."
        elif agent_type == 'operations':
            payload = {"sdaia": compliance.get("sdaia"), "employer": compliance.get("employer")}
            instruction = "تحقّق من الهوية (SDAIA-style) ومن جهة العمل من المستندات."
        elif agent_type == 'customer':
            payload = {"abd": compliance.get("abd")}
            instruction = (
                "استخدم نتائج الفحص الإتاحة (ABD-style screening) لتحديد احتياجات الدعم/الموافقة. "
                "تذكّر: لا تَرفض أبداً بسبب الإعاقة أو الحاجة للدعم."
            )
        elif agent_type == 'queue':
            payload = {
                "sakani": compliance.get("sakani"),
                "real_estate_exchange": compliance.get("real_estate_exchange"),
            }
            instruction = "قَيِّمي العقار حسب مَساره (Sakani إن مُسَجَّل، البورصة العقارية إن مستقلّ)."
        else:  # orchestrator
            payload = {
                "all_agent_findings": previous,
                "compliance_summary": {
                    "simah_band": compliance.get("simah", {}).get("risk_band"),
                    "sdaia_id_status": compliance.get("sdaia", {}).get("id_status"),
                    "employer_consistent": compliance.get("employer", {}).get("consistent"),
                    "abd_pathways": compliance.get("abd", {}).get("suggested_bank_pathways", []),
                    "property_path": "sakani" if compliance.get("sakani") else "real_estate_exchange",
                },
            }
            instruction = (
                "ادْرس نتائج الوكلاء الأربعة، أصدر التوصية النهائية حسب القواعد المُحدَّدة في system prompt. "
                "اكتب تقريراً عربياً رسمياً ينتهي بكتلة JSON المطلوبة."
            )

        return header + "\n## بيانات الامتثال (Demo)\n```json\n" + \
               json.dumps(payload, ensure_ascii=False, indent=2, default=str) + \
               "\n```\n\n## مهمتك\n" + instruction

    # -------------------------------------------------------------------
    @staticmethod
    def _snapshot_for(agent_type: str, compliance: dict) -> dict:
        """Persist only the compliance fields that this agent actually saw."""
        if agent_type == 'analytics':
            return {"simah": compliance.get("simah")}
        if agent_type == 'operations':
            return {"sdaia": compliance.get("sdaia"), "employer": compliance.get("employer")}
        if agent_type == 'customer':
            return {"abd": compliance.get("abd")}
        if agent_type == 'queue':
            return {
                "sakani": compliance.get("sakani"),
                "real_estate_exchange": compliance.get("real_estate_exchange"),
            }
        return {}  # orchestrator gets the previous-findings dict, persisted on the review row

    # -------------------------------------------------------------------
    # Broadcasts (WebSocket)
    # -------------------------------------------------------------------
    def _broadcast_lifecycle(self, application, phase, **extra):
        if not self.channel_layer:
            return
        payload = {
            'type': 'review.lifecycle',
            'phase': phase,
            'application_id': application.application_id,
            **extra,
        }
        async_to_sync(self.channel_layer.group_send)(
            f'app_{application.application_id}', payload
        )

    def _broadcast_status(self, application, agent, status):
        if not self.channel_layer:
            return
        async_to_sync(self.channel_layer.group_send)(
            f'app_{application.application_id}',
            {
                'type': 'agent.status',
                'agent_type': agent.agent_type,
                'agent_name_ar': agent.name_ar,
                'status': status,
            },
        )

    def _broadcast_review(self, application, agent, review):
        if not self.channel_layer:
            return
        async_to_sync(self.channel_layer.group_send)(
            f'app_{application.application_id}',
            {
                'type': 'agent.review',
                'review': {
                    'id': str(review.id),
                    'agent_type': agent.agent_type,
                    'agent_name_ar': agent.name_ar,
                    'agent_color': agent.color,
                    'order': review.order,
                    'content': review.content,
                    'structured': review.structured,
                    'compliance_snapshot': review.compliance_snapshot,
                    'created_at': review.created_at.isoformat(),
                },
            },
        )
