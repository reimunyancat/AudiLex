import json
from channels.generic.websocket import AsyncWebsocketConsumer

class AudioConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.audio_id = self.scope['url_route']['kwargs']['audio_id']
        self.room_group_name = f'audio_{self.audio_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        pass

    async def audio_update(self, event):
        message = event['message']
        status_type = event['type']

        await self.send(text_data=json.dumps({
            'type': status_type,
            'message': message
        }))
