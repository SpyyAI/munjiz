"""WebSocket consumer for the live dashboard."""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class DashboardConsumer(AsyncWebsocketConsumer):
    GROUP = 'dashboard'

    async def connect(self):
        await self.channel_layer.group_add(self.GROUP, self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps({'type': 'hello', 'msg': 'WebSocket متصل'}, ensure_ascii=False))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({'error': 'invalid json'}))
            return

        action = data.get('action')

        if action == 'trigger_scenario':
            scenario_id = data.get('scenario_id')
            from .tasks import run_scenario_task
            run_scenario_task.delay(scenario_id)
            await self.send(text_data=json.dumps({'type': 'ack', 'scenario_id': scenario_id}, ensure_ascii=False))

        elif action == 'update_data':
            from .tasks import run_scenario_with_custom_data_task
            run_scenario_with_custom_data_task.delay(data.get('scenario_id'), data.get('custom_data', {}))
            await self.send(text_data=json.dumps({'type': 'ack', 'scenario_id': data.get('scenario_id')}, ensure_ascii=False))

        elif action == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))

    # ---- group event handlers ----
    async def agent_message(self, event):
        await self.send(text_data=json.dumps(event['message'], ensure_ascii=False))

    async def agent_status(self, event):
        payload = {'type': 'status_update', **event['agent']}
        await self.send(text_data=json.dumps(payload, ensure_ascii=False))

    async def metrics_update(self, event):
        payload = {'type': 'metrics_update', **event['metrics']}
        await self.send(text_data=json.dumps(payload, ensure_ascii=False))

    async def scenario_lifecycle(self, event):
        # Sent at the start and end of a scenario run so every connected dashboard
        # tab can wipe stale bubbles and stay in sync.
        payload = {'type': event['phase'], **event['scenario']}
        await self.send(text_data=json.dumps(payload, ensure_ascii=False))
