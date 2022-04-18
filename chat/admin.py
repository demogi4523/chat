from django.contrib import admin

from .models import Room, Message, Avatar, Attachment

admin.site.register(Room)


# TODO: fix this page
class AvatarModel(admin.ModelAdmin):
    readonly_fields = ['avatar']

    def avatar(self, obj):
        return obj.get_photo()


admin.site.register(Avatar, AvatarModel)


class MessageModel(admin.ModelAdmin):
    readonly_fields = [
        'content',
        'user',
        'room',
        'attachment',
    ]

    def attachment(self, obj):
        return obj.attachment.first().photo_tag()


admin.site.register(Message, MessageModel)


class AttachmentManager(admin.ModelAdmin):
    readonly_fields = ["photo_tag"]


admin.site.register(Attachment, AttachmentManager)
