"""Render the profile and identity assets from a single declarative source."""
from html import escape
from lib.profile import ROOT, atomic_write, load_profile
from lib.svg import document, line, text


def hero(config: dict) -> str:
    profile = config['profile']
    elements = [line(29, 29, 43, 20), line(43, 20, 43, 38), line(43, 38, 29, 29),
                '<g class="accent"><circle cx="29" cy="29" r="3"/><circle cx="43" cy="20" r="3"/><circle cx="43" cy="38" r="3"/></g>',
                text(59, 34, 'AIZEN // CONTROL PLANE', 'accent', 14),
                text(28, 87, profile['name'].upper(), '', 28),
                text(28, 116, ' · '.join(profile['roles']), 'muted', 14),
                text(28, 159, 'ship · scale · observe · learn', 'accent', 18),
                line(28, 186, 452, 186),
                '<circle class="signal pulse" cx="33" cy="213" r="4"/>',
                text(47, 218, 'BUILDING / LEARNING', 'muted', 14),
                text(398, 218, 'v' + profile['version'], 'muted', 14)]
    return document('Aizen // Control Plane', f"{profile['name']}. {' · '.join(profile['roles'])}. Building systems that ship, scale, observe and learn. Version {profile['version']}.", 240, elements, 'scripts/generate_profile.py')


def architecture(config: dict) -> str:
    nodes = config['architecture']['nodes']
    elements = [text(28, 34, 'SYSTEM TOPOLOGY', 'accent', 14)]
    # Clockwise loop: delivery, observation, automation, and feedback into software.
    for label, (x, y) in zip(nodes, [(28, 57), (264, 57), (264, 139), (28, 139)]):
        elements.extend([f'<rect x="{x}" y="{y}" width="188" height="44" rx="7" class="panel"/>',
                         text(x + 12, y + 27, label.upper(), '', 14)])
    elements.extend([line(216, 79, 264, 79), line(258, 74, 264, 79), line(258, 84, 264, 79),
                     line(358, 101, 358, 139), line(353, 133, 358, 139), line(363, 133, 358, 139),
                     line(264, 161, 216, 161), line(222, 156, 216, 161), line(222, 166, 216, 161),
                     line(122, 139, 122, 101), line(117, 107, 122, 101), line(127, 107, 122, 101),
                     text(170, 126, 'FEEDBACK', 'muted', 14),
                     '<path class="line" stroke-dasharray="4 5" d="M122 183 V217 H264"/>',
                     text(275, 222, config['architecture']['exploration'], 'accent', 14),
                     '<metadata>NODE 0x539: the control plane observes itself.</metadata>'])
    return document('Engineering feedback loop', 'Software is delivered to infrastructure. Observability informs automation, which feeds back into software. AI is a direction of exploration.', 248, elements, 'scripts/generate_profile.py')


def md(value: object) -> str:
    return escape(str(value)).replace('|', '&#124;').replace('\n', ' ').replace('`', '&#96;')


def picture(path: str, alt: str) -> str:
    return f'<p align="center">\n  <img src="./assets/{path}.svg" width="480" alt="{escape(alt, quote=True)}">\n</p>'


def readme(config: dict) -> str:
    p = config['profile']
    project = config['featured_project']
    capabilities = '\n\n'.join(f"**{md(name)}**\n\n" + ' · '.join(md(item) for item in group['capabilities'])
                               for name, group in config['focus'].items())
    parts = [picture('static/hero', f"{p['name']} — {' · '.join(p['roles'])}. Ship, scale, observe and learn. v{p['version']}"),
             '<!-- AUTO-GENERATED: scripts/generate_profile.py; edit config/profile.yaml. -->',
             '#### 01 / IDENTITY', '`$ whoami`', md(p['statement']),
             '<details>\n<summary>Inspect Engineer Resource</summary>\n\n' + capabilities +
             '\n\n</details>',
             '#### 02 / FEATURED PROJECT', f"**{md(project['name'])}** — {md(project['summary'])}",
             ' · '.join(md(item) for item in project['technologies']),
             f"[Source]({project['source']}) · [How It Works]({project['documentation']})",
             '#### 03 / ARCHITECTURE', md(p['narrative']),
             picture('static/architecture', 'Software → Infrastructure → Observability → Automation → Software. AI is a direction of exploration.')]
    if config.get('experiments'):
        parts.extend(['**LAB / IN PROGRESS**', '\n\n'.join(
            f"**{md(item['name'])}** — {md(item['question'])} [Follow the work]({item['url']})" for item in config['experiments'])])
    parts.extend(['#### 04 / PUBLIC TELEMETRY',
                  picture('generated/telemetry', 'Public repository counts and last successful synchronization. Text values are available in the data snapshot below.'),
                  picture('generated/activity', 'Observed public GitHub events by UTC day. A bounded sample, not a contribution total.'),
                  'Refreshed daily. Public events are a bounded sample, not commit totals. '
                  '[Data & Last Sync](./assets/generated/telemetry.json) · [Metric Definitions](./docs/DEVELOPMENT.md#metric-contracts)',
                  '#### 05 / CONNECT', ' · '.join(f'[{md(label)}]({url})' for label, url in config.get('links', {}).items()),
                  '`$ exit 0`', '<!--\nSource inspection acknowledged.\n$ control-plane inspect --layer beneath-the-interface\nACCESS: ENGINEER\nThe next layer is the system that keeps this one honest.\nTrace: scripts/lib/github.py\n-->'])
    return '\n\n'.join(parts) + '\n'


def generate(config: dict, output=ROOT) -> None:
    outputs = {output / 'README.md': readme(config), output / 'assets/static/hero.svg': hero(config),
               output / 'assets/static/architecture.svg': architecture(config)}
    for path, content in outputs.items():
        atomic_write(path, content)


if __name__ == '__main__':
    generate(load_profile())
