"""Fetch once, render both panels, then atomically replace successful outputs."""
import json
import sys
from lib.github import collect
from lib.profile import ROOT, atomic_write, load_profile
from lib.svg import document, line, text
from generate_activity import render as render_activity


def render(data: dict) -> str:
    elements = [text(28, 34, 'GITHUB / TELEMETRY', 'accent', 14),
                text(28, 74, data['repositories'], '', 22), text(90, 72, 'public repositories', 'muted', 14),
                text(28, 108, data['active_repositories'], '', 22), text(90, 106, f'pushed in {data["days"]} days¹', 'muted', 14),
                text(28, 142, len(data['languages']), '', 22), text(90, 140, 'primary languages²', 'muted', 14),
                line(28, 159, 452, 159),
                text(28, 184, '¹ Excludes forks and archives.', 'muted', 14),
                text(28, 207, '² Repository primary languages only.', 'muted', 14),
                text(28, 240, 'SYNC / ' + data['synced_at'], 'accent', 14)]
    return document('GitHub telemetry', f"{data['repositories']} public owned repositories. {data['active_repositories']} non-fork, non-archived repositories pushed in {data['days']} days. {len(data['languages'])} primary languages, including forks. Last synchronization {data['synced_at']}.", 264, elements, 'scripts/generate_telemetry.py')


def update(config: dict, output=ROOT / 'assets/generated', client=None, now=None) -> None:
    data = collect(config, client=client, now=now)
    # Render and validate everything before touching the last successful assets.
    outputs = {'telemetry.svg': render(data), 'activity.svg': render_activity(data),
               'telemetry.json': json.dumps(data, indent=2, ensure_ascii=False) + '\n'}
    for filename, content in outputs.items():
        atomic_write(output / filename, content)


def main() -> int:
    try:
        update(load_profile())
    except Exception as exc:
        print(f'Telemetry refresh failed ({type(exc).__name__}): {exc}. Last valid assets retained for API/render failures.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
