from django.shortcuts import render

from .models import Room

def index_view(req):
  return render(req, 'index.html', {
    'rooms': Room.objects.all(),
  })

def room_view(req, room_name):
  chat_room, created = Room.objects.get_or_create(name=room_name)
  return render(req, 'room.html', {
    'room': chat_room
  })
