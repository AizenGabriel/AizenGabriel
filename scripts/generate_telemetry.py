"""Fetch once, render both panels, then atomically replace successful outputs."""
import json
import sys
from lib.github import collect
from lib.profile import ROOT, atomic_write, load_profile
from lib.svg import document, line, text
from generate_activity import render as render_activity


def render(data: dict) -> str:
    elements = [text(28, 38, 'GITHUB / TELEMETRY', 'accent'), text(28, 70, '@' + data['handle'], 'muted'),
                line(28, 90, 452, 90), text(28, 135, str(data['repositories']), '', 30),
                text(98, 130, 'public repositories', 'muted'),
                text(28, 186, str(data['active_repositories']), '', 30),
                text(98, 181, f'pushed in {data["days"]} days¹', 'muted'),
                text(28, 237, str(len(data['languages'])), '', 30),
                text(98, 232, 'primary languages²', 'muted'), line(28, 259, 452, 259)]
    languages = list(data['languages'].items())[:4]
    if languages:
        for index, (language, count) in enumerate(languages):
            elements.append(text(28, 289 + index * 27, f'{language[:26]} / {count} repos', 'accent'))
    else:
        elements.append(text(28, 289, 'No primary language reported', 'muted'))
    foot = 300 + max(len(languages), 1) * 27
    elements.extend([text(28, foot + 20, '¹ Owned; excludes forks and archives.', 'muted', 16),
                     text(28, foot + 47, '² Primary languages; includes forks.', 'muted', 16),
                     text(28, foot + 89, 'LAST SUCCESSFUL SYNC / UTC', 'accent', 16),
                     text(28, foot + 116, data['synced_at'], 'muted')])
    return document('GitHub telemetry', f"{data['repositories']} public owned repositories. {data['active_repositories']} non-fork, non-archived repositories pushed in {data['days']} days. {len(data['languages'])} primary languages. Last synchronization {data['synced_at']}.", foot + 145, elements, 'scripts/generate_telemetry.py')


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
