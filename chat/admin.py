from django.contrib import admin

from .models import Room, Message, Avatar, Attachment

admin.site.register(Room)
admin.site.register(Message)
admin.site.register(Avatar)


class AttachmentManager(admin.ModelAdmin):
    readonly_fields = ["photo_tag"]


admin.site.register(Attachment, AttachmentManager)
