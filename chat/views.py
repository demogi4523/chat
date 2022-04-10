from django.http import HttpResponse
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth import login, authenticate, logout as lgt

from .models import Avatar, Room
from .forms import LoginForm

def index_page(req):
  if req.method == 'GET':
    user = req.user
    if user.is_authenticated:
      return redirect('chat:chat-index')
    form = LoginForm()
    return render(req, 'login.html', {
      'form': form,
    })
  
  if req.method == 'POST':
    form = LoginForm(req.POST)
    if form.is_valid():
      cd = form.cleaned_data
      user = authenticate(username=cd['username'], password=cd['password'])
      if user is None:
        return HttpResponse("Wrong password or username")
      login(req, user)
      return redirect('chat:chat-index')
  
  return HttpResponse("Wrong", status=405)

def index_view(req):
  return render(req, 'index.html', {
    'rooms': Room.objects.all(),
  })

def room_view(req, room_name):
  chat_room, created = Room.objects.get_or_create(name=room_name)
  # print(req.user)
  path = Avatar.objects.get(user=req.user).photo
  # print(path)
  return render(req, 'room.html', {
    'room': chat_room,
    'path': path,
    'req': req,
    'username': req.user.username,
  })

def logout(req):
  lgt(req)
  return redirect('index-page')