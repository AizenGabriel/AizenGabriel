"""Locale-independent English dates for presentation; source data stays ISO."""
from datetime import date, datetime, timezone

MONTHS = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')


def format_date(value: str) -> str:
    parsed = date.fromisoformat(value)
    return f'{parsed.day:02d} {MONTHS[parsed.month - 1]} {parsed.year:04d}'


def format_timestamp(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Synchronization timestamp must include a timezone')
    utc = parsed.astimezone(timezone.utc)
    return f'{format_date(utc.date().isoformat())}, {utc.hour:02d}:{utc.minute:02d} UTC'
