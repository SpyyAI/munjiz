"""Replay scripted (non-AI) scenario messages."""
import json
import time
import logging
from pathlib import Path

from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Agent, AgentMessage, Scenario

logger = logging.getLogger(__name__)
SCRIPTS = Path(settings.BASE_DIR) / 'fixtures' / 'scenario_scripts.json'


def run_prescripted_scenario(scenario: Scenario):
    """Stream the pre-scripted messages for a scenario at their delay_ms cadence."""
    with open(SCRIPTS, encoding='utf-8') as f:
        all_scripts = json.load(f)

    script = next((s for s in all_scripts if s['scenario_id'] == scenario.scenario_id), None)
    if not script:
        logger.warning("No script found for scenario %s", scenario.scenario_id)
        return

    agents = {a.agent_type: a for a in Agent.objects.filter(is_active=True)}
    channel_layer = get_channel_layer()

    for order, m in enumerate(script.get('messages', []), start=1):
        agent = agents.get(m['agent'])
        if not agent:
            continue

        time.sleep(m.get('delay_ms', 1500) / 1000.0)

        # Broadcast status: thinking → idle
        _broadcast_status(channel_layer, agent.agent_type, 'thinking', f'يحلل: {scenario.name_ar}')

        msg = AgentMessage.objects.create(
            scenario=scenario,
            from_agent=agent,
            to_broadcast=True,
            content=m['content'],
            message_type=m.get('type', 'update'),
            is_ai_generated=False,
            order=order,
            delay_ms=m.get('delay_ms', 1500),
        )

        _broadcast_message(channel_layer, agent, msg, order)
        _broadcast_status(channel_layer, agent.agent_type, 'idle', '')


def _broadcast_message(channel_layer, agent, msg, order):
    if not channel_layer:
        return
    async_to_sync(channel_layer.group_send)(
        'dashboard',
        {
            'type': 'agent.message',
            'message': {
                'id': str(msg.id),
                'from_agent': agent.agent_type,
                'from_name': agent.name_ar,
                'from_color': agent.color,
                'content': msg.content,
                'message_type': msg.message_type,
                'is_ai_generated': msg.is_ai_generated,
                'order': order,
                'timestamp': msg.created_at.isoformat(),
            },
        },
    )


def _broadcast_status(channel_layer, agent_type, status, task):
    if not channel_layer:
        return
    async_to_sync(channel_layer.group_send)(
        'dashboard',
        {
            'type': 'agent.status',
            'agent': {'agent_type': agent_type, 'status': status, 'current_task': task},
        },
    )
