import os

from django.db import models
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.db.models.signals import post_delete
from django.dispatch import receiver

from core.settings import MEDIA_URL, MEDIA_ROOT

default_image = os.path.join("avas", "default.jpeg")


class Avatar(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    photo = models.ImageField(blank=False, default=default_image, upload_to="avas")

    def __str__(self):
        return f"{self.user.username} avatar"

    def url(self):
        return os.path.join(MEDIA_URL, str(self.photo))

    def get_photo(self):
        # used in the admin site model as a "thumbnail"
        html = '<img src="{}" width="150" height="150" />'
        return mark_safe(html.format(self.url()))


class Room(models.Model):
    name = models.CharField(max_length=128)
    online = models.ManyToManyField(to=User, blank=True)

    def get_online_count(self):
        return self.online.count()

    def join(self, user):
        self.online.add(user)
        self.save()

    def __str__(self):
        return f"{self.name} ({self.get_online_count()})"


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
        return f"{self.user.username}: {self.content} [{self.timestamp}]"


class Attachment(models.Model):
    message = models.ForeignKey(
        to=Message, on_delete=models.CASCADE, related_name="attachment"
    )
    photo = models.ImageField(upload_to="attachments", blank=False)
    name = models.CharField(max_length=128, unique=True, default="qq")

    def url(self):
        return os.path.join(MEDIA_URL, "attachments", self.name)

    def photo_tag(self):
        # used in the admin site model as a "thumbnail"
        html = '<img src="{}" width="150" height="150" />'
        return mark_safe(html.format(self.url()))

    photo_tag.short_description = "Photo"

    def delete_file(self):
        filepath = os.path.join(MEDIA_ROOT, "attachments", self.name)
        try:
            os.remove(filepath)
        except FileNotFoundError:
            print(f"{filepath} not found")

    def __str__(self):
        return f"{self.message}"


@receiver(post_delete, sender=Attachment)
def delelte_attachment_file(sender, instance, using, **kwargs):
    instance.delete_file()
