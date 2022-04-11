from curses.ascii import US
import os

from django.db import models
from django.contrib.auth.models import User

from core.settings import MEDIA_ROOT


default_image = os.path.join('avas', 'default.jpeg')



class Avatar(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    photo = models.ImageField(blank=False,
                              default=default_image,
                              upload_to='avas')
    
    def __str__(self):
        return f"{self.user.username} avatar"

class Room(models.Model):
    name = models.CharField(max_length=128)
    online = models.ManyToManyField(to=User, blank=True)

    def get_online_count(self):
        return self.online.count()

    def join(self, user):
        self.online.add(user)
        self.save()

    def __str__(self):
        return f'{self.name} ({self.get_online_count()})'


class PersonalChat(models.Model):
    pass


class CommunityChat(models.Model):
    pass


class Message(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    room = models.ForeignKey(to=Room, on_delete=models.CASCADE)
    content = models.CharField(max_length=512)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username}: {self.content} [{self.timestamp}]'
