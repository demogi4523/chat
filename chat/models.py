import os
import json
from datetime import datetime

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from core.settings import MEDIA_URL, MEDIA_ROOT, DEFAULT_AVATAR_ROOT


# TODO: fix structure of project for attachments and avatars and examples images
# TODO: add scripts for manage.py for quickstart project on new machine(automate)
class Avatar(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='avatar')
    photo = models.ImageField(blank=False, default=DEFAULT_AVATAR_ROOT, upload_to="avas")

    def __str__(self):
        return f"{self.user.username} avatar"

    def url(self):
        return os.path.join(MEDIA_URL, str(self.photo))

    def get_photo(self):
        # used in the admin site model as a "thumbnail"
        # TODO: create thumbnail
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


class MessageType(models.TextChoices):
    PUBLIC = 'PUBLIC', _('Public')
    PRIVATE = 'PRIVATE', _('Private')


class Message(models.Model):
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='message'
    )
    room = models.ForeignKey(to=Room, on_delete=models.CASCADE)
    content = models.CharField(max_length=512)
    msg_type = models.CharField(
        max_length=7,
        choices=MessageType.choices,
        default=MessageType.PUBLIC
    )
    to = models.ForeignKey(
        to=User,
        on_delete=models.PROTECT,
        null=True,
        default=None,
        related_name='private_message'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def json(self):
        attachment = self.attachment.first()
        msg = {
            'username': str(self.user),
            'room': str(self.room),
            'content': self.content,
            'avatar_url': self.user.avatar.photo.url,
            'timestamp': datetime.isoformat(self.timestamp),
        }

        if attachment:
            attachment_url = attachment.url()
            msg["attachment"] = attachment_url

        return json.dumps(msg)

    def get_timestamp(self):
        return datetime.isoformat(self.timestamp)

    def get_attachment_url(self):
        attachment = self.attachment.first()
        if attachment:
            return attachment.url()
        raise Exception("Message hasn't attachment!!!")

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
        # TODO: create thumbnail
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
