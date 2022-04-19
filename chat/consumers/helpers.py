# TODO: rename file, I don't know how
import json
from datetime import datetime
from uuid import uuid4
from enum import Enum, auto

from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from ..models import Avatar, MessageType, Room, Message, Attachment
from ..utils import file_from_string_to_file


class ChatMessageTypes(Enum):
    PUBLIC = auto()
    PRIVATE = auto()
    PUBLIC_WITH_ATTACHMENT = auto()
    PRIVATE_WITH_ATTACHMENT = auto()

    @classmethod
    def add_attachment(cls, msg_type):
        if msg_type is cls.PUBLIC:
            return cls.PUBLIC_WITH_ATTACHMENT
        if msg_type is cls.PRIVATE:
            return cls.PRIVATE_WITH_ATTACHMENT
        raise Exception(f"Wrong message type: {msg_type}. Must be {cls.PUBLIC} or {cls.PRIVATE}")


class AbstractChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.room_group_name = None
        self.user_inbox = None
        self.room_name = None
        self.room = None
        self.user_msg_loading = None

    async def websocket_connect(self, event):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        self.room = await database_sync_to_async(self.get_room)(self.room_name)
        self.user = self.scope["user"]
        self.user_inbox = f"inbox_{self.user.username}"
        self.user_msg_loading = f"msg_loading_{self.user.username}"

        # connection has to be accepted
        await self.accept()

        # join to the room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        if self.user.is_authenticated:
            # create a user inbox for private messages
            await self.channel_layer.group_add(
                self.user_inbox,
                self.channel_name,
            )

            # create a user loading messages
            await self.channel_layer.group_add(
                self.user_msg_loading,
                self.channel_name,
            )

            await database_sync_to_async(self.room.online.add)(self.user)

            # send the user list to the newly joined user
            online_users = await database_sync_to_async(self.get_online)(self.room_name)

            await self.send(
                json.dumps(
                    {
                        "type": "user_list",
                        "users": [
                            {
                                "username": user.username,
                                "photo": await database_sync_to_async(get_photo_url)(
                                    user
                                ),
                            }
                            for user in online_users
                        ],
                    }
                )
            )

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_join",
                    "user": {
                        "username": self.user.username,
                        "photo": await database_sync_to_async(get_photo_url)(self.user),
                    },
                },
            )

    async def websocket_receive(self, event):
        pass

    async def disconnect(self, close_code):
        pass

    async def send_and_save_msg(self, content, attachment=None, private=False, target=None):
        msg = await database_sync_to_async(self.create_message)(content, private, target)
        content = str(msg.content)
        timestamp = await database_sync_to_async(msg.get_timestamp)()
        message = {
            "content": content,
            "timestamp": timestamp,
        }
        private_or_public = self.room_group_name if private is False else f"inbox_{target}"
        msg_type = ChatMessageTypes.PRIVATE if private else ChatMessageTypes.PUBLIC
        if attachment is not None:
            filename = f"{str(uuid4())}"
            [file, ext] = file_from_string_to_file(attachment, filename, "image")
            filename_with_ext = f"{filename}.{ext}"

            photo_file = ContentFile(file)
            att = await database_sync_to_async(self.create_attachment)(
                msg, filename_with_ext, photo_file
            )
            message["attachment"] = await database_sync_to_async(att.url)()
            msg_type = ChatMessageTypes.add_attachment(msg_type)

        if private:
            message["to"] = target

        event_type = f"chat_{str(msg_type).split('.')[1].lower()}_message"
        await self.channel_layer.group_send(
            private_or_public,
            {
                "type": event_type,
                "user": {
                    "username": self.user.username,
                    "avatar_url": await database_sync_to_async(get_photo_url)(
                        self.user
                    ),
                },
                "message": message,
            }
        )

        if private:
            # send private message delivered to the user
            await self.send(
                json.dumps(
                    {
                        "type": "private_message_delivered",
                        "target": target,
                        "message": message,
                    }
                )
            )

        return

    def get_room(self, name):
        return Room.objects.get(name=name)

    def get_online(self, room_name):
        return list(Room.objects.get(name=room_name).online.all())

    def create_message(self, msg, private=False, target=None):
        to = None
        if target is not None:
            to = User.objects.get(username=target)
        message = Message.objects.create(
            user=self.user,
            room=self.room,
            content=msg,
            msg_type=MessageType.PUBLIC if private is False else MessageType.PRIVATE,
            to=to,
            timestamp=datetime.now()
        )
        return message

    def create_attachment(self, message, filename, photo):
        attachment = Attachment.objects.create(message=message, photo=photo, name=filename)
        return attachment

    async def chat_public_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def chat_private_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def chat_public_with_attachment_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def chat_private_with_attachment_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def private_message_delivered(self, event):
        await self.send(text_data=json.dumps(event))

    async def user_list(self, event):
        await self.send(text_data=json.dumps(event))


def get_photo_url(user):
    return Avatar.objects.get(user=user).photo.url
