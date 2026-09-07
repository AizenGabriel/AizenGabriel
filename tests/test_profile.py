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
from generate_profile import readme, hero, architecture
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

    def test_committed_assets_and_local_links(self):
        config = load_profile()
        self.assertEqual((ROOT / 'README.md').read_text(), readme(config))
        self.assertEqual((ROOT / 'assets/static/hero.svg').read_text(), hero(config))
        self.assertEqual((ROOT / 'assets/static/architecture.svg').read_text(), architecture(config))
        for path in (ROOT / 'assets').rglob('*.svg'):
            ElementTree.parse(path)
        import re
        for path in re.findall(r'src="\./([^"]+)"', readme(config)):
            self.assertTrue((ROOT / path).is_file(), path)

    def test_workflows_and_noop_guard(self):
        import yaml
        workflows = ROOT / '.github/workflows'
        for path in workflows.glob('*.yml'):
            value = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
            self.assertIn('on', value)
            self.assertIn('jobs', value)
        workflow = yaml.load((workflows / 'update-profile.yml').read_text(), Loader=yaml.BaseLoader)
        self.assertEqual(workflow['permissions']['contents'], 'write')
        commands = workflow['jobs']['refresh']['steps'][-1]['run']
        self.assertLess(commands.index('git diff --cached --quiet'), commands.index('git commit'))


if __name__ == '__main__':
    unittest.main()
