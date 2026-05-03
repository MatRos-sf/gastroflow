import datetime

from django.utils import timezone


def convert_date_from_str_to_date(
    date_str: str, time_min: bool = True, *, date_format: str = "%Y-%m-%d"
) -> datetime.datetime:
    """Convert date string to datetime object"""
    tz = timezone.get_current_timezone()
    if date_str:
        try:
            date_object = datetime.datetime.strptime(date_str, date_format).date()
        except ValueError:
            date_object = timezone.localdate()

    else:
        date_object = timezone.localdate()

    return datetime.datetime.combine(
        date_object, datetime.time.min if time_min else datetime.time.max, tzinfo=tz
    )
