"""Render an explicitly bounded public event timeline from a shared snapshot."""
import json
from lib.dates import format_date
from lib.profile import ROOT, atomic_write
from lib.svg import document, line, text


def render(data: dict) -> str:
    activity = data['activity']
    peak = max((day['events'] for day in activity), default=0)
    total = sum(day['events'] for day in activity)
    elements = [text(28, 34, 'ACTIVITY / PUBLIC EVENTS', 'accent', 14)]
    if total == 0:
        elements.extend([text(28, 66, 'No public events observed', '', 16),
                         text(28, 92, f'{format_date(activity[0]["date"])} → {format_date(activity[-1]["date"])} / UTC', 'muted', 14),
                         text(28, 119, 'Returned sample only; not proof of inactivity.', 'muted', 14)])
        height = 143
    else:
        elements.extend([text(28, 65, f'{total} observed / {data["days"]} days / peak {peak}', '', 16), line(28, 156, 452, 156)])
        step = 424 / len(activity)
        for index, day in enumerate(activity):
            bar_height = day['events'] / peak * 64
            if bar_height:
                elements.append(f'<rect x="{28 + index * step:.2f}" y="{156 - bar_height:.2f}" width="{max(step - 5, 1):.2f}" height="{bar_height:.2f}" class="accent"><title>{format_date(day["date"])}: {day["events"]} observed events</title></rect>')
        elements.extend([text(28, 183, format_date(activity[0]['date']), 'muted', 14), text(352, 183, format_date(activity[-1]['date']), 'muted', 14)])
        height = 240
    if data['event_limit_reached']:
        elements.append(text(28, height - 15, '300-event cap reached; sample may be partial.', 'muted', 14))
        if total == 0:
            # Leave a separate line for cap information even for a short window.
            elements[-1] = text(28, height + 4, '300-event cap reached; sample may be partial.', 'muted', 14)
            height += 28
    elif total:
        elements.append(text(28, 216, 'Up to 300 events / 30 days; not contributions.', 'muted', 14))
    description = 'Bounded public event sample. ' + '; '.join(f'{format_date(day["date"])}: {day["events"]} observed events' for day in activity)
    return document('Public GitHub activity', description, height, elements, 'scripts/generate_activity.py')


def main() -> None:
    data = json.loads((ROOT / 'assets/generated/telemetry.json').read_text())
    atomic_write(ROOT / 'assets/generated/activity.svg', render(data))


if __name__ == '__main__':
    main()
