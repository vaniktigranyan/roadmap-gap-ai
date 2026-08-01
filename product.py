# -*- coding: utf-8 -*-
"""
Which product is being analysed.

Everything downstream - the review query, the GitHub fetch, every LLM prompt, the
database file and the UI copy - resolves the product through here, so pointing the
system at a different app is a config change rather than a code change.

Selection order:
  1. ANALYSIS_PACKAGE env var (looked up in discovered_projects.json for repo/name)
  2. GITHUB_REPO / PRODUCT_NAME / PRODUCT_DESCRIPTION env vars, which override
  3. the built-in default

Run `python discover_projects.py` to regenerate the catalogue of analysable products.
"""
import os
import json
import re
from dataclasses import dataclass
from typing import List, Optional

from dotenv import load_dotenv

from sources import DEFAULT_SOURCE, get_source

load_dotenv()

CATALOGUE_PATH = "discovered_projects.json"

DEFAULT_PACKAGE = "org.torproject.android"
DEFAULT_REPO = "guardianproject/orbot-android"
DEFAULT_NAME = "Orbot"
DEFAULT_DESCRIPTION = "a Tor anonymity and proxy app for Android"


@dataclass(frozen=True)
class Product:
    package_name: str      # the key used to look this product up in its source
    repo: str
    name: str
    description: str
    source_id: str = DEFAULT_SOURCE

    @property
    def source(self):
        return get_source(self.source_id)

    @property
    def slug(self) -> str:
        """Filesystem-safe id, used to keep one database per product."""
        return re.sub(r'[^a-z0-9]+', '_', self.package_name.lower()).strip('_')

    @property
    def db_path(self) -> str:
        return f"gaps_{self.slug}.db"

    @property
    def debate_path(self) -> str:
        return f"debate_{self.slug}.json"

    @property
    def label(self) -> str:
        """'Orbot - a Tor anonymity and proxy app for Android', for prompts."""
        return f"{self.name} ({self.description})" if self.description else self.name

    @property
    def repo_url(self) -> str:
        return f"https://github.com/{self.repo}"


def load_catalogue() -> List[dict]:
    if not os.path.exists(CATALOGUE_PATH):
        return []
    try:
        with open(CATALOGUE_PATH, encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


# Repo tails make poor product names ("orbot-android", "Anki-Android"), so the
# well-known ones are spelled properly. Anything else falls back to _prettify.
DISPLAY_NAMES = {
    'guardianproject/orbot-android': 'Orbot',
    'hrydgard/ppsspp': 'PPSSPP',
    'wordpress-mobile/WordPress-Android': 'WordPress for Android',
    'thunderbird/thunderbird-android': 'Thunderbird for Android (K-9 Mail)',
    'ankidroid/Anki-Android': 'AnkiDroid',
    'AntennaPod/AntennaPod': 'AntennaPod',
    'TeamAmaze/AmazeFileManager': 'Amaze File Manager',
    'zxing/zxing': 'Barcode Scanner (ZXing)',
    'AnySoftKeyboard/AnySoftKeyboard': 'AnySoftKeyboard',
    'iSoron/uhabits': 'Loop Habit Tracker',
    '00-Evan/shattered-pixel-dungeon': 'Shattered Pixel Dungeon',
    'frostwire/frostwire': 'FrostWire',
    'chrisboyle/sgtpuzzles': "Simon Tatham's Puzzles",
    'jberkel/sms-backup-plus': 'SMS Backup+',
    'PaulWoitaschek/Voice': 'Voice Audiobook Player',
    'termux/termux-app': 'Termux',
    'SimpleMobileTools/Simple-Gallery': 'Simple Gallery',
    'daneren2005/Subsonic': 'DSub',
    'duckduckgo/Android': 'DuckDuckGo',
    'yuriykulikov/AlarmClock': 'Simple Alarm Clock',
    'sky-map-team/stardroid': 'Sky Map',
    'bluesky-social/social-app': 'Bluesky',
    'plusonelabs/calendar-widget': 'Calendar Widget',
}


def _prettify(repo: str) -> str:
    """'guardianproject/orbot-android' -> 'Orbot Android'."""
    tail = repo.split('/')[-1]
    words = re.split(r'[-_.]+', tail)
    return ' '.join(w[:1].upper() + w[1:] for w in words if w)


def get_product(package_name: Optional[str] = None) -> Product:
    # Env overrides describe whichever product the env selected. When a caller asks
    # for a specific package they must not leak in, or every lookup would collapse
    # onto the same repo.
    from_env = package_name is None
    package_name = package_name or os.getenv('ANALYSIS_PACKAGE') or DEFAULT_PACKAGE

    entry = next((e for e in load_catalogue() if e.get('package_name') == package_name), None)

    if entry:
        repo = entry['repo']
        description = entry.get('description') or ''
        name = DISPLAY_NAMES.get(repo) or _prettify(repo)
    elif package_name == DEFAULT_PACKAGE:
        repo, name, description = DEFAULT_REPO, DEFAULT_NAME, DEFAULT_DESCRIPTION
    else:
        repo = os.getenv('GITHUB_REPO', '') if from_env else ''
        if not repo:
            raise ValueError(
                f"Unknown package '{package_name}'. Either add it to {CATALOGUE_PATH} "
                f"(run: python discover_projects.py) or set GITHUB_REPO explicitly."
            )
        name, description = DISPLAY_NAMES.get(repo) or _prettify(repo), ''

    if from_env:
        repo = os.getenv('GITHUB_REPO', repo)
        name = os.getenv('PRODUCT_NAME', name)
        description = os.getenv('PRODUCT_DESCRIPTION', description)

    source_id = (entry or {}).get('source_id') or DEFAULT_SOURCE
    if from_env:
        source_id = os.getenv('ANALYSIS_SOURCE', source_id)

    return Product(package_name=package_name, repo=repo, name=name,
                   description=description, source_id=source_id)


def list_products() -> List[Product]:
    """Every product in the catalogue, best-scoring first."""
    return [get_product(e['package_name']) for e in load_catalogue()]


CURRENT = get_product()
