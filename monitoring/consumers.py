import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ExamSession, SuspiciousEvent

EVENT_WEIGHTS = {
    'tab_switch': 0.12,
    'copy':       0.10,
    'paste':      0.15,
    'focus_loss': 0.08,
    'right_click':0.05,
    'fast_answer':0.06,
}

class ExamConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group = f'exam_{self.session_id}'

        # Join the room group for this session
        await self.channel_layer.group_add(
            self.room_group,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group,
            self.channel_name
        )

    async def receive(self, text_data):
        """Called when browser sends an event via WebSocket."""
        data = json.loads(text_data)
        event_type = data.get('type')
        metadata = data.get('metadata', {})

       
        trust_score = await self.save_event(event_type, metadata)

        await self.channel_layer.group_send(
            f'dashboard_{self.session_id}',
            {
                'type': 'trust_update',
                'event_type': event_type,
                'trust_score': trust_score,
                'session_id': self.session_id,
            }
        )

        # Send acknowledgement back to student
        await self.send(text_data=json.dumps({
            'status': 'received',
            'trust_score': trust_score
        }))

    @database_sync_to_async
    def save_event(self, event_type, metadata):
        """Save suspicious event and recalculate trust score."""
        try:
            session = ExamSession.objects.get(id=self.session_id)

            # Determine severity
            weight = EVENT_WEIGHTS.get(event_type, 0.05)
            if weight >= 0.12:
                severity = 'high'
            elif weight >= 0.08:
                severity = 'med'
            else:
                severity = 'low'

            # Save the event
            SuspiciousEvent.objects.create(
                session=session,
                event_type=event_type,
                metadata=metadata,
                severity=severity
            )

            # Recalculate trust score
            events = SuspiciousEvent.objects.filter(session=session)
            penalty = sum(
                EVENT_WEIGHTS.get(e.event_type, 0.05)
                for e in events
            )
            new_score = round(max(0.0, 1.0 - penalty), 2)
            session.trust_score = new_score

            # Auto-flag if below threshold
            if new_score < session.exam.trust_threshold:
                session.status = 'flagged'

            session.save()
            return new_score

        except ExamSession.DoesNotExist:
            return 1.0


class DashboardConsumer(AsyncWebsocketConsumer):
    """Examiner's live dashboard — receives trust updates."""

    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group = f'dashboard_{self.session_id}'

        await self.channel_layer.group_add(
            self.room_group,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group,
            self.channel_name
        )

    async def trust_update(self, event):
        """Forward trust score updates to the examiner browser."""
        await self.send(text_data=json.dumps({
            'event_type': event['event_type'],
            'trust_score': event['trust_score'],
            'session_id': event['session_id'],
        }))