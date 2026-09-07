"""Central configuration and atomic, change-aware file writes."""
from pathlib import Path
import os
import re
import tempfile
import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_profile(path: Path = ROOT / 'config/profile.yaml') -> dict:
    data = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('Profile configuration must be a mapping')
    if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})', data['profile']['handle']):
        raise ValueError('Invalid GitHub handle')
    days = data['telemetry']['days']
    if not isinstance(days, int) or isinstance(days, bool) or not 1 <= days <= 30:
        raise ValueError('telemetry.days must be between 1 and 30')
    for label, url in data.get('links', {}).items():
        if not re.fullmatch(r'[a-zA-Z0-9 -]+', label) or not re.fullmatch(r'(https://|mailto:)[^\s<>"()]+', url):
            raise ValueError('Contact links must be explicit HTTPS or mailto URLs')
    return data


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding='utf-8') == content:
        return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        temporary.chmod(0o644)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
