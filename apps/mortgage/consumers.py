"""WebSocket consumer for the mortgage review flow."""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class MortgageReviewConsumer(AsyncWebsocketConsumer):
    """One application = one WS group. Clients join `app_{application_id}`."""

    async def connect(self):
        self.application_id = self.scope['url_route']['kwargs']['application_id']
        self.group = f'app_{self.application_id}'
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps(
            {'type': 'hello', 'application_id': self.application_id}, ensure_ascii=False
        ))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return
        if data.get('action') == 'start_review':
            from .tasks import run_mortgage_review_task
            run_mortgage_review_task.delay(self.application_id)
            await self.send(text_data=json.dumps(
                {'type': 'ack', 'started': self.application_id}, ensure_ascii=False
            ))

    # Group event handlers
    async def review_lifecycle(self, event):
        await self.send(text_data=json.dumps(event, ensure_ascii=False))

    async def agent_status(self, event):
        await self.send(text_data=json.dumps(event, ensure_ascii=False))

    async def agent_review(self, event):
        await self.send(text_data=json.dumps(event, ensure_ascii=False))
