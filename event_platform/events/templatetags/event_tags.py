from datetime import datetime

from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def local_dt(value):
    """Convert a datetime read from MongoDB to local (Asia/Manila) time.

    PyMongo returns naive datetimes that are actually in UTC, so they are
    marked as UTC first and then converted to the project's time zone.
    """
    if not isinstance(value, datetime):
        return value
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.utc)
    return timezone.localtime(value)


@register.filter
def initials(value, length=2):
    """'Intro to MongoDB' -> 'IT'; used for avatar circles."""
    words = str(value or '').split()
    return ''.join(word[0] for word in words[:int(length)]).upper()


@register.filter
def percent_of(current, maximum):
    """Whole-number percentage, capped at 100, safe when maximum is 0/None."""
    try:
        current = float(current or 0)
        maximum = float(maximum or 0)
    except (TypeError, ValueError):
        return 0
    if maximum <= 0:
        return 0
    return min(100, round(current / maximum * 100))
