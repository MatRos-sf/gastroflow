from django import template

register = template.Library()


@register.filter
def duration_hhmmss(value):
    """
    Zamienia timedelta -> "HH:MM:SS".
    Jeśli brak danych (None), zwraca "—".
    """
    if value is None:
        return "—"
    total_seconds = int(value.total_seconds())
    hours, rem = divmod(total_seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
