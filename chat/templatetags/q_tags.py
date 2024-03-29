from django import template

register = template.Library()


# TODO: move to model
@register.filter
def get_attachment_url(msg):
    attachment = msg.attachment.first()
    if attachment:
        return attachment.url()
    return "#"
