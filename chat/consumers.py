import json
from uuid import uuid4

from django.core.files.base import ContentFile
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import Attachment, Avatar, Room, Message
from .utils import file_from_string_to_file


class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = None
        self.room_group_name = None
        self.room = None
        self.user = None
        self.user_inbox = None

    async def websocket_connect(self, event):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.room = await database_sync_to_async(self.get_room)(self.room_name)
        self.user = self.scope['user']
        self.user_inbox = f'inbox_{self.user.username}'

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

            await database_sync_to_async(self.room.online.add)(self.user)

            # send the user list to the newly joined user
            online_users = await database_sync_to_async(self.get_online)(self.room_name)

            await self.send(json.dumps({
                'type': 'user_list',
                'users': [{
                    'username': user.username,
                    'photo': await database_sync_to_async(get_photo_url)(user),
                        } for user in online_users],
            }))

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_join',
                    'user': {
                        'username': self.user.username,
                        'photo': await database_sync_to_async(get_photo_url)(self.user),
                    }
                },
            )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

        await database_sync_to_async(self.room.online.remove)(self.user)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_leave',
                'user': {
                    'username': self.user.username,
                    'photo': await database_sync_to_async(get_photo_url)(self.user),
                },
            }
        )

    async def websocket_receive(self, event):
        # print(type(event["text"]))
        text_data_json = json.loads(event['text'])
        message = text_data_json['message']
        photo = text_data_json.get('photo', None)

        if not self.user.is_authenticated:
            return

        if message.startswith('/pm '):
            split = message.split(' ', 2)
            target = split[1]
            target_msg = split[2]

            # send private message to the target
            await self.channel_layer.group_send(
                f'inbox_{target}',
                {
                    'type': 'private_message',
                    'user': self.user.username,
                    'message': target_msg,
                }
            )
            # send private message delivered to the user
            await self.send(json.dumps({
                'type': 'private_message_delivered',
                'target': target,
                'message': target_msg,
            }))

            await database_sync_to_async(self.create_message)(target_msg)

            return

        if photo:
            # send message with attachment
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message_with_attachment',
                    'user': {
                        'username': self.user.username,
                        'avatar': await database_sync_to_async(get_photo_url)(self.user),
                    },
                    'message': message,
                    'photo': photo,
                }
            )

            msg = await database_sync_to_async(self.create_message)(message)
            filename = f"{str(uuid4())}"
            [file, ext] = file_from_string_to_file(photo, filename, 'image')
            filename_with_ext = f"{filename}.{ext}"

            photo_file = ContentFile(file)
            await database_sync_to_async(self.create_attachment)(msg, filename_with_ext, photo_file)

            return

        # send chat message event to the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'user': {
                    'username': self.user.username,
                    'avatar': await database_sync_to_async(get_photo_url)(self.user),
                },
                'message': message,
            }
        )
        await database_sync_to_async(self.create_message)(message)
        return

    def get_room(self, name):
        return Room.objects.get(name=name)

    def get_online(self, room_name):
        return list(Room.objects.get(name=room_name).online.all())

    def create_message(self, msg):
        message = Message.objects.create(user=self.user, room=self.room, content=msg)
        return message

    def create_attachment(self, message, filename, photo):
        Attachment.objects.create(message=message, photo=photo, name=filename)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def chat_message_with_attachment(self, event):
        await self.send(text_data=json.dumps(event))

    async def user_leave(self, event):
        await self.send(text_data=json.dumps(event))

    async def user_join(self, event):
        await self.send(text_data=json.dumps(event))

    async def private_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def private_message_delivered(self, event):
        await self.send(text_data=json.dumps(event))


def get_photo_url(user):
    return Avatar.objects.get(user=user).photo.url
