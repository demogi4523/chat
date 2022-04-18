import json

from channels.db import database_sync_to_async
from django.core.paginator import Paginator

from ..models import Message
from .helpers import AbstractChatConsumer, get_photo_url


class ChatConsumer(AbstractChatConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

        await database_sync_to_async(self.room.online.remove)(self.user)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_leave",
                "user": {
                    "username": self.user.username,
                    "photo": await database_sync_to_async(get_photo_url)(self.user),
                },
            },
        )

    async def websocket_receive(self, event):
        text_data_json = json.loads(event["text"])
        content = text_data_json.get("message", None)
        attachment = text_data_json.get("photo", None)
        updater = text_data_json.get("updater", None)

        target = None
        private = False

        if not self.user.is_authenticated:
            return

        if updater:
            page = updater["page"]
            target = self.user.username
            messages = await database_sync_to_async(get_messages_load)(self.room, page)
            await self.channel_layer.group_send(
                f"msg_loading_{target}",
                {
                    "type": "message_loading",
                    "messages": messages,
                }
            )

            return

        if content.startswith("/pm "):
            _, target, content = content.split(" ", 2)
            private = True

        await self.send_and_save_msg(content, attachment, private, target)

        return

    async def user_leave(self, event):
        await self.send(text_data=json.dumps(event))

    async def user_join(self, event):
        await self.send(text_data=json.dumps(event))

    async def message_loading(self, event):
        await self.send(text_data=json.dumps(event))


def get_messages_load(room, page_number):
    paginator = Paginator(Message.objects.filter(room=room).all().order_by('-timestamp'), 5)
    if page_number > paginator.num_pages:
        return {"ended": True}
    page = paginator.get_page(page_number)
    page = [msg.json() for msg in page.object_list]
    return {'ended': False, 'page': page}
