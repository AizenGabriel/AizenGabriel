"""Offline contract tests: real-data semantics, failure safety and reproducibility."""
from datetime import datetime, timezone
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lib.github import GitHub, GitHubError, collect
from lib.profile import ROOT, atomic_write, load_profile
from lib.svg import document, text
from generate_profile import readme, hero, architecture, generate
from generate_activity import render as render_activity
from copy import deepcopy
from generate_telemetry import update

NOW = datetime(2026, 9, 7, 12, tzinfo=timezone.utc)


def repo(**overrides):
    return {'private': False, 'owner': {'login': 'AizenGabriel'}, 'language': 'Python',
            'pushed_at': '2026-09-06T00:00:00Z', 'fork': False, 'archived': False, **overrides}


def event(identifier, timestamp, **overrides):
    return {'id': identifier, 'public': True, 'created_at': timestamp, **overrides}


class MetricsTests(unittest.TestCase):
    def test_filters_and_event_boundaries(self):
        client = Mock()
        client.pages.side_effect = [
            [repo(), repo(fork=True), repo(archived=True), repo(private=True),
             repo(owner={'login': 'someone-else'}), repo(language=None, pushed_at=None)],
            [event('1', '2026-09-07T01:00:00Z'), event('1', '2026-09-07T01:00:00Z'),
             event('2', '2026-08-09T00:00:00Z'), event('3', '2026-08-08T23:59:59Z'),
             event('4', '2026-09-08T00:00:00Z'), event('5', '2026-09-07T02:00:00Z', public=False)]]
        data = collect(load_profile(), client, NOW)
        self.assertEqual(data['repositories'], 4)
        self.assertEqual(data['active_repositories'], 1)
        self.assertEqual(data['languages'], {'Python': 3})
        self.assertEqual(len(data['activity']), 30)
        self.assertEqual(sum(day['events'] for day in data['activity']), 2)
        self.assertEqual(data['activity'][0]['events'], 1)

    def test_pagination(self):
        client = GitHub(token='')
        client.get = Mock(side_effect=[[{}] * 100, [{}]])
        self.assertEqual(len(client.pages('/users/example/repos')), 101)
        self.assertIn('page=2', client.get.call_args.args[0])

    def test_event_cap(self):
        client = Mock()
        client.pages.side_effect = [[], [event(str(i), '2026-09-07T01:00:00Z') for i in range(300)]]
        self.assertTrue(collect(load_profile(), client, NOW)['event_limit_reached'])

    @patch('lib.github.time.sleep')
    @patch('lib.github.urlopen')
    def test_retry_network_failure(self, open_url, sleep):
        open_url.side_effect = URLError('network unavailable')
        with self.assertRaises(GitHubError):
            GitHub(token='').get('/users/example/repos')
        self.assertEqual(open_url.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    @patch('lib.github.urlopen')
    def test_rate_limit_does_not_leak_token(self, open_url):
        open_url.side_effect = HTTPError('https://api.github.com', 403, 'forbidden',
                                        {'X-RateLimit-Remaining': '0', 'X-RateLimit-Reset': '100'}, None)
        with self.assertRaisesRegex(GitHubError, 'rate limit exhausted') as error:
            GitHub(token='secret-test-value').get('/users/example/repos')
        self.assertNotIn('secret-test-value', str(error.exception))
        self.assertEqual(open_url.call_count, 1)


class OutputTests(unittest.TestCase):
    def test_api_failure_keeps_every_asset(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            for name in ['telemetry.svg', 'activity.svg', 'telemetry.json']:
                (output / name).write_text('last-valid')
            client = Mock()
            client.pages.side_effect = GitHubError('offline')
            with self.assertRaises(GitHubError):
                update(load_profile(), output, client, NOW)
            self.assertTrue(all(path.read_text() == 'last-valid' for path in output.iterdir()))

    @patch('generate_telemetry.render_activity', side_effect=ValueError('bad render'))
    def test_render_failure_keeps_assets(self, render):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / 'telemetry.svg').write_text('last-valid')
            client = Mock()
            client.pages.side_effect = [[], []]
            with self.assertRaises(ValueError):
                update(load_profile(), output, client, NOW)
            self.assertEqual((output / 'telemetry.svg').read_text(), 'last-valid')

    def test_identical_snapshot_does_not_rewrite(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            client = Mock()
            client.pages.side_effect = [[], [], [], []]
            update(load_profile(), output, client, NOW)
            before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in output.iterdir()}
            update(load_profile(), output, client, NOW)
            self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in output.iterdir()})
            for path in output.glob('*.svg'):
                ElementTree.parse(path)

    @patch('lib.profile.os.replace', side_effect=OSError('disk error'))
    def test_atomic_write_failure_preserves_previous_file(self, replace):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'asset.svg'
            path.write_text('old')
            with self.assertRaises(OSError):
                atomic_write(path, 'new')
            self.assertEqual(path.read_text(), 'old')
            self.assertEqual(list(path.parent.iterdir()), [path])

    def test_xml_escaping(self):
        value = '<script>&"injected"'
        svg = document(value, value, 100, [text(10, 20, value)], 'test')
        root = ElementTree.fromstring(svg)
        self.assertNotIn('<script>', svg)
        self.assertEqual(root.find('{http://www.w3.org/2000/svg}title').text, value)

    def test_config_only_change_and_identity_reproducibility(self):
        config = load_profile()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            generate(config, root)
            changed = deepcopy(config)
            changed['profile']['version'] = '1.2'
            changed['featured_project']['summary'] = 'Updated from YAML only.'
            import yaml
            config_path = root / 'profile.yaml'
            config_path.write_text(yaml.safe_dump(changed))
            changed = load_profile(config_path)
            generate(changed, root)
            self.assertIn('v1.2', (root / 'assets/static/hero.svg').read_text())
            self.assertIn('Updated from YAML only.', (root / 'README.md').read_text())
            before = {p.relative_to(root): (p.read_bytes(), p.stat().st_mtime_ns)
                      for p in root.rglob('*') if p.is_file()}
            generate(changed, root)
            after = {p.relative_to(root): (p.read_bytes(), p.stat().st_mtime_ns)
                     for p in root.rglob('*') if p.is_file()}
            self.assertEqual(before, after)
            for path in root.rglob('*.svg'):
                ElementTree.parse(path)

    def test_profile_presentation_and_links(self):
        import re
        config = load_profile()
        output = readme(config)
        self.assertEqual(output.count('width="480"'), 4)
        self.assertNotIn('width="100%"', output)
        self.assertEqual(output.count('#### '), 5)
        self.assertNotIn('LAB / IN PROGRESS', output)
        for path in re.findall(r'(?:src="|\]\()\./([^"\)]+)', output):
            self.assertTrue((ROOT / path.split('#')[0]).is_file(), path)
        for path in (ROOT / 'assets').rglob('*.svg'):
            ElementTree.parse(path)
        config['experiments'] = [{'name': 'Test lab', 'question': 'Can we observe it?',
                                 'url': 'https://github.com/AizenGabriel/AizenGabriel'}]
        self.assertIn('LAB / IN PROGRESS', readme(config))
        self.assertIn('Can we observe it?', readme(config))

    def test_configurable_version(self):
        import yaml
        config = load_profile()
        config['profile']['version'] = '1.7'
        self.assertIn('v1.7', hero(config))
        config['profile']['version'] = '<script>'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'profile.yaml'
            path.write_text(yaml.safe_dump(config))
            with self.assertRaisesRegex(ValueError, 'profile.version'):
                load_profile(path)

    def test_empty_and_active_timeline(self):
        client = Mock()
        client.pages.side_effect = [[], []]
        data = collect(load_profile(), client, NOW)
        empty = render_activity(data)
        self.assertIn('No public events observed', empty)
        self.assertIn('not proof of inactivity', empty)
        self.assertNotIn('class="accent"><title>', empty)
        self.assertIn('viewBox="0 0 480 143"', empty)
        data['activity'][-1]['events'] = 5
        active = render_activity(data)
        self.assertIn('5 observed / 30 days / peak 5', active)
        self.assertIn('class="accent"><title>', active)
        self.assertIn('viewBox="0 0 480 240"', active)
        data['event_limit_reached'] = True
        self.assertIn('sample may be partial', render_activity(data))
        data['activity'][-1]['events'] = 0
        capped_empty = render_activity(data)
        self.assertIn('sample may be partial', capped_empty)
        ElementTree.fromstring(capped_empty)

    def test_v12_content(self):
        config = load_profile()
        output = readme(config)
        for label in ['Inspect Engineer Resource', '[Source]', '[How It Works]',
                      '[Data & Last Sync]', '[Metric Definitions]']:
            self.assertIn(label, output)
        for name, group in config['focus'].items():
            self.assertIn(f'**{name}**\n\n', output)
            for capability in group['capabilities']:
                self.assertIn(capability, output)
        for removed in ['apiVersion:', '```yaml', 'Engineering focus', 'Infrastructure focus',
                        'Current work', 'One declarative source for identity and content.',
                        'Public API observations with explicit sample limits.',
                        'Reproducible assets and failure-safe refreshes.']:
            self.assertNotIn(removed, output)
        self.assertIn('v1.2', hero(config))
        self.assertIn('Refreshed daily. Public events are a bounded sample, not commit totals.', output)

    def test_english_dates_and_utc(self):
        from lib.dates import format_date, format_timestamp
        cases = [('2025-12-31', '31 Dec 2025'), ('2026-01-01', '01 Jan 2026'),
                 ('2024-02-29', '29 Feb 2024'), ('2026-09-07', '07 Sep 2026')]
        for source, expected in cases:
            self.assertEqual(format_date(source), expected)
        self.assertEqual(format_timestamp('2026-09-07T16:23:59Z'), '07 Sep 2026, 16:23 UTC')
        self.assertEqual(format_timestamp('2026-01-01T01:15:00+02:00'), '31 Dec 2025, 23:15 UTC')
        with self.assertRaises(ValueError):
            format_timestamp('2026-09-07T16:23:00')

    def test_formatted_svg_dates_preserve_snapshot(self):
        from generate_telemetry import render as render_telemetry
        path = ROOT / 'assets/generated/telemetry.json'
        before = path.read_bytes()
        data = json.loads(before)
        original = deepcopy(data)
        from lib.dates import format_date, format_timestamp
        telemetry = render_telemetry(data)
        self.assertIn(format_timestamp(data['synced_at']), telemetry)
        self.assertNotIn(data['synced_at'], telemetry)
        for count in [0, 3]:
            sample = deepcopy(data)
            for day in sample['activity']:
                day['events'] = count
            svg = render_activity(sample)
            self.assertIn(format_date(sample['activity'][0]['date']), svg)
            self.assertNotIn(sample['activity'][0]['date'], svg)
            root = ElementTree.fromstring(svg)
            self.assertIn(format_date(sample['activity'][-1]['date']),
                          root.find('{http://www.w3.org/2000/svg}desc').text)
            self.assertEqual(svg, render_activity(sample))
        self.assertEqual(data, original)
        self.assertEqual(path.read_bytes(), before)

    def test_workflows_and_noop_guard(self):
        import yaml
        workflows = ROOT / '.github/workflows'
        for path in workflows.glob('*.yml'):
            value = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
            self.assertIn('on', value)
            self.assertIn('jobs', value)
            steps = next(iter(value['jobs'].values()))['steps']
            runs = [step.get('run', '') for step in steps]
            generation = next(i for i, run in enumerate(runs) if 'python scripts/generate_profile.py' in run)
            tests = next(i for i, run in enumerate(runs) if 'unittest discover' in run)
            self.assertLess(generation, tests)
        workflow = yaml.load((workflows / 'update-profile.yml').read_text(), Loader=yaml.BaseLoader)
        self.assertEqual(workflow['permissions']['contents'], 'write')
        commands = workflow['jobs']['refresh']['steps'][-1]['run']
        self.assertLess(commands.index('git diff --cached --quiet'), commands.index('git commit'))


if __name__ == '__main__':
    unittest.main()
