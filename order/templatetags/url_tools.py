from django import template
from django.utils.timezone import now

register = template.Library()


@register.simple_tag(takes_context=True)
def get_dates(context, **kwargs):
    """Get dates from request GET parameters, when not exists use current date"""
    request = context["request"]
    from_date = request.GET.get("from", now().strftime("%Y-%m-%d"))
    to_date = request.GET.get("to", now().strftime("%Y-%m-%d"))
    return f"{from_date}_{to_date}"
