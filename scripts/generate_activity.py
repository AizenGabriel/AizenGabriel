"""Render an explicitly bounded public event timeline from a shared snapshot."""
import json
from lib.profile import ROOT, atomic_write
from lib.svg import document, line, text


def render(data: dict) -> str:
    activity = data['activity']
    peak = max((day['events'] for day in activity), default=0)
    total = sum(day['events'] for day in activity)
    elements = [text(28, 38, 'ACTIVITY / PUBLIC EVENTS', 'accent'),
                text(28, 76, f'{total} observed events · {data["days"]} UTC days', '', 18),
                text(28, 105, f'Daily peak: {peak} events', 'muted'), line(28, 232, 452, 232)]
    step = 424 / len(activity)
    for index, day in enumerate(activity):
        height = day['events'] / max(peak, 1) * 100
        elements.append(f'<rect x="{28 + index * step:.2f}" y="{232 - max(height, 2):.2f}" width="{max(step - 5, 1):.2f}" height="{max(height, 2):.2f}" class="{"accent" if height else "panel"}"><title>{day["date"]}: {day["events"]} observed events</title></rect>')
    elements += [text(28, 262, activity[0]['date'], 'muted', 16), text(332, 262, activity[-1]['date'], 'muted', 16),
                 text(28, 297, 'API: up to 300 events / 30 days', 'muted', 16),
                 text(28, 323, 'CAP REACHED · history may be truncated' if data['event_limit_reached'] else 'Observed sample, not contributions', 'muted', 16)]
    description = '; '.join(f'{day["date"]}: {day["events"]} observed events' for day in activity)
    return document('Public GitHub activity', description, 350, elements, 'scripts/generate_activity.py')


def main() -> None:
    data = json.loads((ROOT / 'assets/generated/telemetry.json').read_text())
    atomic_write(ROOT / 'assets/generated/activity.svg', render(data))


if __name__ == '__main__':
    main()
