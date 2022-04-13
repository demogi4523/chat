from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout as lgt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator

from .models import Avatar, Message, Room
from .forms import LoginForm, RegisterForm, AccountPhotoUpdateForm


@require_http_methods(["GET", "POST"])
def login_view(req):
    if req.method == "GET":
        user = req.user
        if user.is_authenticated:
            return redirect("chat:chat-index")
        form = LoginForm()
        return render(
            req,
            "login.html",
            {
                "form": form,
            },
        )

    if req.method == "POST":
        next_page = req.GET.get("next", "chat:chat-index")
        form = LoginForm(req.POST)
        if form.is_valid():
            cd = form.cleaned_data
            username = cd["username"]
            password = cd["password"]
            user = authenticate(username=username, password=password)
            if user is None:
                return HttpResponse("Wrong password or username")
            login(req, user)
            return redirect(next_page)


@require_http_methods(["GET"])
@login_required(login_url="login-required")
def index_view(req):
    return render(
        req,
        "index.html",
        {
            "rooms": Room.objects.all(),
        },
    )


@require_http_methods(["GET"])
@login_required(login_url="login-required")
def room_view(req, room_name):
    chat_room, created = Room.objects.get_or_create(name=room_name)
    path = Avatar.objects.get(user=req.user).photo
    paginator = Paginator(Message.objects.all(), 25)
    messages = paginator.get_page(0)
    return render(
        req,
        "room.html",
        {
            "room": chat_room,
            "path": path,
            "req": req,
            "username": req.user.username,
            "messages": messages,
        },
    )


@login_required
def logout(req):
    lgt(req)
    return redirect("index-page")


@require_http_methods(["GET", "POST"])
def signup_view(req):
    form = RegisterForm(req.POST)
    if form.is_valid():
        form.save()
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password1")
        user = authenticate(username=username, password=password)
        login(req, user)
        next_page = req.GET.get("next", "chat:chat-index")
        return redirect(next_page)
    else:
        form = RegisterForm()
    return render(req, "reg.html", {"form": form})


@require_http_methods(["GET"])
def login_required_view(req):
    next_page = req.GET.get("next", None)
    return render(req, "login_required.html", {"next_page": next_page})


@require_http_methods(["GET", "POST"])
def account_settings(req):
    # TODO: Crop avatar
    if req.method == "GET":
        form = AccountPhotoUpdateForm()
        return render(
            req,
            "account_settings.html",
            {
                "form": form,
                "prev_photo": Avatar.objects.get(user=req.user).photo.url,
            },
        )
    if req.method == "POST":
        form = AccountPhotoUpdateForm(req.POST, req.FILES)
        if form.is_valid():
            photo = form.cleaned_data["photo"]
            print(photo)
            avatar = Avatar.objects.get(user=req.user)
            avatar.photo = photo
            avatar.save()
            return HttpResponse("OK")
        return HttpResponse("Wrong!", 405)
