from django import template
from django.utils.safestring import mark_safe
import markdown

register = template.Library()


@register.filter("markdown")
def apply_markdown(text: str):

    return mark_safe(markdown.markdown(text))
