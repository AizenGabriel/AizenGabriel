"""Render the profile and identity assets from a single declarative source."""
from html import escape
import yaml
from lib.profile import ROOT, atomic_write, load_profile
from lib.svg import document, line, text


def hero(config: dict) -> str:
    profile = config['profile']
    elements = [text(28, 38, 'AIZEN // CONTROL PLANE', 'accent'),
                line(28, 57, 452, 57),
                '<circle class="signal pulse" cx="35" cy="85" r="5"/>',
                text(50, 91, 'OPERATIONAL / ENGINEER ONLINE', 'muted', 14),
                text(28, 151, profile['name'].upper(), '', 32),
                text(28, 187, ' · '.join(profile['roles']), 'muted', 16),
                text(28, 252, 'Building systems that', '', 24),
                text(28, 286, 'ship · scale · observe · learn', 'accent', 24),
                line(28, 319, 452, 319),
                text(28, 347, 'ENGINEERING / DEVOPS / AI', 'muted', 14),
                text(400, 347, 'v1.0', 'muted', 14)]
    return document('Aizen // Control Plane', f"{profile['name']}. {' · '.join(profile['roles'])}. Building systems that ship, scale, observe and learn.", 372, elements, 'scripts/generate_profile.py')


def architecture(config: dict) -> str:
    trajectory = config['trajectory']
    elements = [text(28, 38, 'SYSTEM TOPOLOGY', 'accent'), text(28, 68, 'One trajectory. Connected layers.', 'muted')]
    for index, stage in enumerate(trajectory):
        y = 102 + index * 63
        elements.extend([f'<rect x="28" y="{y}" width="424" height="44" rx="7" class="panel"/>',
                         text(44, y + 28, f'{index + 1:02}', 'accent'), text(90, y + 28, stage.upper(), '', 18)])
        if index < len(trajectory) - 1:
            elements.extend([line(57, y + 44, 57, y + 63), line(52, y + 57, 57, y + 62), line(62, y + 57, 57, y + 62)])
    elements.extend([text(28, 115 + len(trajectory) * 63, 'OBSERVE → LEARN → FEED BACK', 'muted', 14),
                     '<metadata>NODE 0x539: the control plane observes itself.</metadata>'])
    return document('Engineering to autonomous systems', ' → '.join(trajectory) + '. Observations feed back into engineering.', 140 + len(trajectory) * 63, elements, 'scripts/generate_profile.py')


def md(value: object) -> str:
    return escape(str(value)).replace('|', '&#124;').replace('\n', ' ').replace('`', '&#96;')


def readme(config: dict) -> str:
    p = config['profile']
    parts = ['<p align="center">\n  <img src="./assets/static/hero.svg" width="100%" alt="Aizen Gabriel — Software Engineer · DevOps · AI. Building systems that ship, scale, observe and learn.">\n</p>',
             '<!-- AUTO-GENERATED: scripts/generate_profile.py; edit config/profile.yaml. -->',
             '### 01 / SYSTEM IDENTITY', '`$ whoami`', f"**{md(p['name'])}** · {md(' · '.join(p['roles']))}", md(p['statement']),
             '### 02 / SYSTEM STATUS', '`$ system.status`',
             '| Subsystem | State |\n| :--- | :--- |\n' + '\n'.join(f"| {md(name)} | `{md(group['state'])}` |" for name, group in config['focus'].items()) + '\n| Observability | `MONITORING` |',
             'States describe the profile’s operating model; they are not skill ratings or uptime measurements.',
             '### 03 / ENGINEER RESOURCE', '`$ kubectl describe engineer aizen`']
    for name, group in config['focus'].items():
        parts.append(f"**{md(name)}** / {md(group['scope'])}\n\n" + ' · '.join(md(item) for item in group['capabilities']))
    manifest = {'apiVersion': 'engineering.aizen.dev/v1', 'kind': 'Engineer',
                'metadata': {'name': p['handle'].lower()},
                'spec': {'focus': list(config['focus']), 'principles': config['principles'],
                         'aiMode': 'interests-and-experimentation'}, 'status': {'phase': 'Running'}}
    parts.extend(['<details>\n<summary>Inspect declarative manifest</summary>\n\n```yaml\n' + yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True).rstrip() + '\n```\n\n</details>',
                  '### 04 / ARCHITECTURE', md(p['narrative']),
                  '<img src="./assets/static/architecture.svg" width="100%" alt="Software → Automation → Infrastructure → Observability → Intelligence → Autonomous Systems. Learning feeds back into engineering.">',
                  '### 05 / CURRENT PROCESSES', '`$ process.list`',
                  '| PID | Process | State |\n| :--- | :--- | :--- |\n' + '\n'.join(f"| {md(item['pid'])} | {md(item['name']).replace('-', '-<wbr>')} | {md(item['state'])} |" for item in config['processes']),
                  '### 06 / LIVE TELEMETRY',
                  '<img src="./assets/generated/telemetry.svg" width="100%" alt="Public GitHub repository telemetry; counts and synchronization time are available in the linked data snapshot.">',
                  '<img src="./assets/generated/activity.svg" width="100%" alt="Daily observed public GitHub events, with UTC dates and sample limits. Accessible values are available in the linked data snapshot.">',
                  'Public API observations, refreshed daily. Activity is a bounded event sample, not a contribution or commit total. Zero means no events returned for that day. See the [data snapshot](./assets/generated/telemetry.json) for values and the last successful synchronization.',
                  '### 07 / ENGINEERING DIRECTIVES',
                  '| Directive | Operating principle |\n| :--- | :--- |\n' + '\n'.join(f'| {md(key)} | {md(value)} |' for key, value in config['principles'].items()),
                  '### 08 / CONNECT', ' · '.join(f'[{md(label)}]({url})' for label, url in config.get('links', {}).items()),
                  '`$ exit 0`', '<!--\nSource inspection acknowledged.\n$ control-plane inspect --layer beneath-the-interface\nACCESS: ENGINEER\nThe next layer is the system that keeps this one honest.\nTrace: scripts/lib/github.py\n-->'])
    return '\n\n'.join(parts) + '\n'


def main() -> None:
    config = load_profile()
    outputs = {ROOT / 'README.md': readme(config), ROOT / 'assets/static/hero.svg': hero(config),
               ROOT / 'assets/static/architecture.svg': architecture(config)}
    for path, content in outputs.items():
        atomic_write(path, content)


if __name__ == '__main__':
    main()
