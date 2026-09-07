"""Public GitHub REST metrics, with bounded retries and explicit event coverage."""
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class GitHubError(RuntimeError):
    pass


class GitHub:
    def __init__(self, token: str | None = None):
        self.token = token if token is not None else os.environ.get('GITHUB_TOKEN')

    def get(self, path: str):
        if not path.startswith('/users/'):
            raise GitHubError('Only public user endpoints are supported')
        headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'aizen-control-plane',
                   'X-GitHub-Api-Version': '2022-11-28'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        for attempt in range(3):
            try:
                with urlopen(Request('https://api.github.com' + path, headers=headers), timeout=25) as response:
                    return json.load(response)
            except HTTPError as exc:
                if exc.code == 403 and exc.headers.get('X-RateLimit-Remaining') == '0':
                    raise GitHubError(f'GitHub rate limit exhausted; reset epoch: {exc.headers.get("X-RateLimit-Reset", "unknown")}') from None
                if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                    raise GitHubError(f'GitHub request failed: HTTP {exc.code}') from None
                delay = exc.headers.get('Retry-After', '')
                if delay.isdigit() and int(delay) > 30:
                    raise GitHubError('GitHub requests a longer retry delay; try again later') from None
                time.sleep(int(delay) if delay.isdigit() else 2 ** attempt)
            except (URLError, TimeoutError) as exc:
                if attempt == 2:
                    raise GitHubError('GitHub network request failed after 3 attempts') from None
                time.sleep(2 ** attempt)
            except (ValueError, UnicodeError):
                raise GitHubError('GitHub returned invalid JSON') from None

    def pages(self, path: str, maximum: int = 1000, **query) -> list[dict]:
        items = []
        for page in range(1, maximum + 1):
            batch = self.get(path + '?' + urlencode({**query, 'per_page': 100, 'page': page}))
            if not isinstance(batch, list) or any(not isinstance(item, dict) for item in batch):
                raise GitHubError('Expected a list of GitHub objects')
            items.extend(batch)
            if len(batch) < 100:
                return items
        if maximum != 3:
            raise GitHubError('Repository pagination limit reached; refusing partial totals')
        return items


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def collect(config: dict, client: GitHub | None = None, now: datetime | None = None) -> dict:
    client = client or GitHub()
    now = now or datetime.now(timezone.utc)
    handle = config['profile']['handle']
    days = config['telemetry']['days']
    repos = client.pages(f'/users/{handle}/repos', type='owner', sort='full_name')
    repos = [r for r in repos if not r['private'] and r['owner']['login'].casefold() == handle.casefold()]
    events = client.pages(f'/users/{handle}/events/public', maximum=3)
    first_day = now.date() - timedelta(days=days - 1)
    counts = Counter()
    seen = set()
    for event in events:
        if event['id'] in seen or not event['public']:
            continue
        seen.add(event['id'])
        timestamp = parse_time(event['created_at'])
        if first_day <= timestamp.date() <= now.date() and timestamp <= now:
            counts[timestamp.date().isoformat()] += 1
    languages = Counter(r['language'] for r in repos if r['language'])
    return {
        'handle': handle, 'synced_at': now.isoformat(timespec='seconds').replace('+00:00', 'Z'),
        'repositories': len(repos),
        'active_repositories': sum(bool(r['pushed_at']) and now - timedelta(days=days) <= parse_time(r['pushed_at']) <= now
                                   and not r['fork'] and not r['archived'] for r in repos),
        'languages': dict(sorted(languages.items(), key=lambda item: (-item[1], item[0]))),
        'days': days, 'event_limit_reached': len(events) >= 300,
        'activity': [{'date': (first_day + timedelta(days=i)).isoformat(),
                      'events': counts[(first_day + timedelta(days=i)).isoformat()]} for i in range(days)],
        'sources': [f'https://api.github.com/users/{handle}/repos', f'https://api.github.com/users/{handle}/events/public'],
    }
