"""Core agent execution engine using Qwen via OpenRouter (OpenAI-compatible)."""
import json
import logging
import time

from openai import OpenAI
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Agent, AgentMessage, Scenario
from .prompts import get_agent_prompt

logger = logging.getLogger(__name__)


class LLMUnavailable(Exception):
    """Raised when the LLM provider returns an error or empty content. The caller
    should retry the call (SDK retry) or fail over to a secondary provider."""


class AgentEngine:
    def __init__(self):
        self.client = OpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY or 'sk-no-key',
        )
        self.channel_layer = get_channel_layer()

    # ------------------------------------------------------------------
    # Single-agent execution
    # ------------------------------------------------------------------
    def run_agent(self, agent: Agent, context: dict, scenario: Scenario) -> str:
        agent.status = 'thinking'
        agent.current_task = f'يحلل سيناريو: {scenario.name_ar}'
        agent.save(update_fields=['status', 'current_task'])
        self._broadcast_status(agent)

        system_prompt = agent.system_prompt or get_agent_prompt(agent.agent_type)

        qs = context.get('queue_state', {}) or {}
        # Other context (everything except the headline live numbers) — secondary detail
        side_context = {k: v for k, v in context.items() if k not in ('queue_state', 'day_context', 'current_time')}

        user_message = (
            f"## السيناريو الحالي\n"
            f"{scenario.name_ar} ({scenario.scenario_id}) — {scenario.time}\n\n"
            f"## ⚡ الحالة الحيّة الآن (المصدر الموثوق — استخدم هذه الأرقام)\n"
            f"- العملاء بالانتظار: **{qs.get('total_waiting', '?')}**\n"
            f"- متوسط الانتظار: **{qs.get('avg_wait_minutes', '?')} دقيقة**\n"
            f"- الالتزام بـ SLA: **{qs.get('sla_compliance', '?')}%**\n"
            f"- استخدام الكيوسكات: **{qs.get('kiosk_usage_percent', qs.get('kiosk_usage', '?'))}%**\n"
            f"- سياق اليوم: **{context.get('day_context', 'يوم عادي')}**\n"
            f"- الوقت الحالي: **{context.get('current_time', scenario.time)}**\n\n"
            f"## وصف السيناريو (سرد قصصي فقط — قد يحتوي أرقاماً قديمة، تجاهلها إذا اختلفت عن الأرقام الحيّة)\n"
            f"{scenario.description}\n\n"
            f"## بيانات تشغيلية إضافية (موظفين/كيوسكات/عملاء/SLA…)\n"
            f"```json\n{json.dumps(side_context, ensure_ascii=False, indent=2, default=str)}\n```\n\n"
            f"## مهمتك\n"
            f"حلّل **الحالة الحيّة الآن** وقدّم رأيك بناءً على دورك. "
            f"⚠️ مهم: استخدم الأرقام الحيّة في الأعلى ولا تنسخ أرقاماً من وصف السيناريو إذا اختلفت. "
            f"تحدّث بالعامية السعودية المهنية. ردّ مختصر وعملي (3-5 جمل). ابدأ بإيموجي مناسب."
        )

        try:
            response = self.client.chat.completions.create(
                model=agent.model_name or settings.LLM_MODEL_DEFAULT,
                max_tokens=500,
                temperature=agent.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                extra_headers={
                    "HTTP-Referer": "https://munjiz.ai",
                    "X-Title": "Munjiz Branch AI",
                },
            )
            result = response.choices[0].message.content
            if not result or not result.strip():
                raise LLMUnavailable(f"LLM returned empty content for {agent.name_ar}")
        except LLMUnavailable:
            self._reset_agent_status(agent)
            raise
        except Exception as e:
            logger.warning("LLM API error for %s: %s", agent.name_ar, e)
            self._reset_agent_status(agent)
            raise LLMUnavailable(str(e)) from e

        self._reset_agent_status(agent)
        return result

    def _reset_agent_status(self, agent: Agent):
        agent.status = 'idle'
        agent.current_task = ''
        agent.save(update_fields=['status', 'current_task'])
        self._broadcast_status(agent)

    # ------------------------------------------------------------------
    # Full scenario orchestration
    # ------------------------------------------------------------------
    def run_scenario_with_ai(self, scenario: Scenario, context: dict) -> dict[str, str]:
        try:
            agents = {a.agent_type: a for a in Agent.objects.filter(is_active=True)}
        except Exception as e:
            logger.exception("Failed to load agents: %s", e)
            return {}

        order = 0
        responses: dict[str, str] = {}

        # Sara: data analysis
        if 'analytics' in agents:
            r = self.run_agent(agents['analytics'], context, scenario)
            order += 1
            self._save_and_broadcast(scenario, agents['analytics'], r, order, 'analysis')
            responses['analytics'] = r

        # Fahad: operational status
        if 'operations' in agents:
            ctx = {**context, 'sara_analysis': responses.get('analytics', '')}
            r = self.run_agent(agents['operations'], ctx, scenario)
            order += 1
            self._save_and_broadcast(scenario, agents['operations'], r, order, 'update')
            responses['operations'] = r

        # Khalid: customer perspective
        if 'customer' in agents:
            ctx = {**context, **{'sara_analysis': responses.get('analytics', ''), 'fahad_report': responses.get('operations', '')}}
            r = self.run_agent(agents['customer'], ctx, scenario)
            order += 1
            self._save_and_broadcast(scenario, agents['customer'], r, order, 'analysis')
            responses['customer'] = r

        # Nora: queue solutions
        if 'queue' in agents:
            ctx = {**context, **{'sara_analysis': responses.get('analytics', ''), 'fahad_report': responses.get('operations', ''), 'khalid_input': responses.get('customer', '')}}
            r = self.run_agent(agents['queue'], ctx, scenario)
            order += 1
            self._save_and_broadcast(scenario, agents['queue'], r, order, 'suggestion')
            responses['queue'] = r

        # Orchestrator: final decision
        if 'orchestrator' in agents:
            ctx = {
                **context,
                'agent_inputs': {
                    'سارة (التحليلات)': responses.get('analytics', ''),
                    'فهد (العمليات)': responses.get('operations', ''),
                    'خالد (العملاء)': responses.get('customer', ''),
                    'نورة (الطوابير)': responses.get('queue', ''),
                },
            }
            r = self.run_agent(agents['orchestrator'], ctx, scenario)
            order += 1
            self._save_and_broadcast(scenario, agents['orchestrator'], r, order, 'decision')
            responses['orchestrator'] = r

        return responses

    # ------------------------------------------------------------------
    # Persistence + WebSocket broadcast
    # ------------------------------------------------------------------
    def _save_and_broadcast(self, scenario, agent, content, order, msg_type):
        msg = AgentMessage.objects.create(
            scenario=scenario,
            from_agent=agent,
            to_broadcast=True,
            content=content,
            message_type=msg_type,
            is_ai_generated=True,
            order=order,
        )
        self._broadcast_message(agent, msg, msg_type, order)

    def _broadcast_message(self, agent, msg, msg_type, order):
        if not self.channel_layer:
            return
        async_to_sync(self.channel_layer.group_send)(
            'dashboard',
            {
                'type': 'agent.message',
                'message': {
                    'id': str(msg.id),
                    'from_agent': agent.agent_type,
                    'from_name': agent.name_ar,
                    'from_color': agent.color,
                    'content': msg.content,
                    'message_type': msg_type,
                    'is_ai_generated': msg.is_ai_generated,
                    'order': order,
                    'timestamp': msg.created_at.isoformat(),
                },
            },
        )

    def _broadcast_status(self, agent):
        if not self.channel_layer:
            return
        async_to_sync(self.channel_layer.group_send)(
            'dashboard',
            {
                'type': 'agent.status',
                'agent': {
                    'agent_type': agent.agent_type,
                    'status': agent.status,
                    'current_task': agent.current_task,
                },
            },
        )
