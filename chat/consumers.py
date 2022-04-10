import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import Room, Message

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

        # print(online_users)
        await self.send(json.dumps({
          'type': 'user_list',
          'users': [user.username for user in online_users],
        }))

        await self.channel_layer.group_send(
          self.room_group_name,
          {
            'type': 'user_join',
            'user': self.user.username,
          },
        )


  async def websocket_disconnect(self, close_code):
      await self.channel_layer.group_discard(
        self.room_group_name,
        self.channel_name,
      )

      await database_sync_to_async(self.room.online.remove)(self.user)

      await self.channel_layer.group_send(
        self.room_group_name,
        {
          'type': 'user_leave',
          'user': self.user.username,
        },
      )


  async def websocket_receive(self, event):
    text_data_json = json.loads(event['text'])
    message = text_data_json['message']

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
      return


    # send chat message event to the room
    await self.channel_layer.group_send(
      self.room_group_name,
      {
        'type': 'chat_message',
        'user': self.user.username,
        'message': message,
      }
    )
    await database_sync_to_async(self.create_message)(message)

  def get_room(self, name):
    return Room.objects.get(name=name)

  def get_online(self, room_name):
    return list(Room.objects.get(name=room_name).online.all())

  def create_message(self, message):
    Message.objects.create(user=self.user, room=self.room, content=message)


  async def chat_message(self, event):
    await self.send(text_data=json.dumps(event))

  async def user_leave(self, event):
    await self.send(text_data=json.dumps(event))

  async def user_join(self, event):
    await self.send(text_data=json.dumps(event))

  async def private_message(self, event):
    await self.send(text_data=json.dumps(event))

  async def private_message_delivered(self, event):
    await self.send(text_data=json.dumps(event))