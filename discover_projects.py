# -*- coding: utf-8 -*-
"""
Find products this system can analyse: an app needs BOTH a large review corpus in
an allowed dataset AND a public GitHub roadmap.

The sealuzh corpus turns out to be almost entirely open-source Android apps, so a
package name usually identifies its repository. We verify every candidate against
the live GitHub API rather than trusting the mapping, then rank by how much signal
each side actually offers.

Usage:  python discover_projects.py [--top 20] [--min-reviews 200]
Writes: discovered_projects.json
"""
import sys
import os
import json
import time
import argparse

if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import duckdb
import requests
from dotenv import load_dotenv

load_dotenv()

SEALUZH = ("https://huggingface.co/datasets/sealuzh/app_reviews/resolve/main/"
           "data/train-00000-of-00001.parquet")

# package name -> candidate GitHub repo. Verified against the API before use;
# a wrong guess simply drops out of the results.
PACKAGE_TO_REPO = {
    'org.telegram.messenger': 'DrKLO/Telegram',
    'org.wikipedia': 'wikimedia/apps-android-wikipedia',
    'org.wordpress.android': 'wordpress-mobile/WordPress-Android',
    'org.torproject.android': 'guardianproject/orbot-android',
    'org.ppsspp.ppsspp': 'hrydgard/ppsspp',
    'com.frostwire.android': 'frostwire/frostwire',
    'net.sourceforge.opencamera': 'almalence/OpenCamera',
    'com.fsck.k9': 'thunderbird/thunderbird-android',
    'de.danoeh.antennapod': 'AntennaPod/AntennaPod',
    'org.isoron.uhabits': 'iSoron/uhabits',
    'com.ichi2.anki': 'ankidroid/Anki-Android',
    'com.duckduckgo.mobile.android': 'duckduckgo/Android',
    'com.amaze.filemanager': 'TeamAmaze/AmazeFileManager',
    'org.kiwix.kiwixmobile': 'kiwix/kiwix-android',
    'com.termux': 'termux/termux-app',
    'com.moez.QKSMS': 'moezbhatti/qksms',
    'de.ph1b.audiobook': 'PaulWoitaschek/Voice',
    'com.simplemobiletools.gallery': 'SimpleMobileTools/Simple-Gallery',
    'org.xbmc.kore': 'xbmc/Kore',
    'com.menny.android.anysoftkeyboard': 'AnySoftKeyboard/AnySoftKeyboard',
    'com.shatteredpixel.shatteredpixeldungeon': '00-Evan/shattered-pixel-dungeon',
    'com.vrem.wifianalyzer': 'VREMSoftwareDevelopment/WiFiAnalyzer',
    'net.nurik.roman.muzei': 'romannurik/muzei',
    'net.nurik.roman.dashclock': 'romannurik/dashclock',
    'com.better.alarm': 'yuriykulikov/AlarmClock',
    'org.petero.droidfish': 'peterosterlund2/droidfish',
    'com.watabou.pixeldungeon': 'watabou/pixel-dungeon',
    'github.daneren2005.dsub': 'daneren2005/Subsonic',
    'com.google.zxing.client.android': 'zxing/zxing',
    'org.geometerplus.zlibrary.ui.android': 'geometer/FBReaderJ',
    'com.zegoggles.smssync': 'jberkel/sms-backup-plus',
    'com.grarak.kerneladiutor': 'Grarak/KernelAdiutor',
    'org.scummvm.scummvm': 'scummvm/scummvm',
    'com.nextcloud.client': 'nextcloud/android',
    'org.openintents.filemanager': 'openintents/filemanager',
    'com.eleybourn.bookcatalogue': 'eleybourn/Book-Catalogue',
    'com.dozuki.ifixit': 'iFixit/iFixitAndroid',
    'org.kde.necessitas.ministro': 'KDE/android-ministro',
    'com.reicast.emulator': 'reicast/reicast-emulator',
    'com.opendoorstudios.ds4droid': 'jquesnelle/ds4droid',
    'com.achep.acdisplay': 'AChep/AcDisplay',
    'org.smc.inputmethod.indic': 'Indic-Keyboard/indic-keyboard',
    'com.gpl.rpg.AndorsTrail': 'AndorsTrailRelease/andors-trail',
    'com.asksven.betterbatterystats': 'asksven/BetterBatteryStats',
    'ohi.andre.consolelauncher': 'Andre1299/TUI-ConsoleLauncher',
    'com.google.android.stardroid': 'sky-map-team/stardroid',
    'com.google.android.diskusage': 'ivankovnatsky/diskusage',
    'org.npr.android.news': 'nprapps/NPR-One-Android',
    'com.plusonelabs.calendar': 'plusonelabs/calendar-widget',
    'name.boyle.chris.sgtpuzzles': 'chrisboyle/sgtpuzzles',
}

# Products whose signals come from a source other than sealuzh. The 2025 Play corpus
# only carries reviews for 42 apps and nearly all are closed-source; Bluesky is the one
# that also has a public issue tracker, so it is the proof that the source layer works.
EXTRA_PRODUCTS = [
    {'package_name': 'Bluesky', 'repo': 'bluesky-social/social-app',
     'source_id': 'play2025', 'display_name': 'Bluesky', 'reviews': 8136,
     'avg_star': 3.09, 'star_spread': 5},
]

GH = "https://api.github.com"


def gh_headers():
    h = {'Accept': 'application/vnd.github+json'}
    token = os.getenv('GITHUB_TOKEN')
    if token:
        h['Authorization'] = f'Bearer {token}'
    return h


def review_counts(min_reviews: int):
    con = duckdb.connect()
    rows = con.execute(f"""
        SELECT package_name, COUNT(*) AS n,
               AVG(CAST(star AS DOUBLE)) AS avg_star,
               COUNT(DISTINCT star) AS star_spread
        FROM read_parquet('{SEALUZH}')
        WHERE length(trim(review)) >= 15
        GROUP BY 1 HAVING COUNT(*) >= {min_reviews}
        ORDER BY n DESC
    """).fetchall()
    return {r[0]: {'reviews': r[1], 'avg_star': round(r[2], 2), 'star_spread': r[3]} for r in rows}


def _get(url, headers, params=None, attempts: int = 3):
    """A flaky connection must not cost us the whole scan, so retry then give up."""
    for i in range(attempts):
        try:
            return requests.get(url, headers=headers, params=params, timeout=25)
        except requests.exceptions.RequestException:
            if i == attempts - 1:
                return None
            time.sleep(2 * (i + 1))
    return None


def probe_repo(repo: str, headers) -> dict:
    r = _get(f"{GH}/repos/{repo}", headers)
    if r is None:
        return {'ok': False, 'error': 'network unreachable'}
    if r.status_code != 200:
        return {'ok': False, 'error': f"HTTP {r.status_code}"}
    d = r.json()

    ms = _get(f"{GH}/repos/{repo}/milestones", headers, {'state': 'all', 'per_page': 100})
    milestones = len(ms.json()) if ms is not None and ms.status_code == 200 else 0

    s = _get(f"{GH}/search/issues", headers, {'q': f'repo:{repo} is:issue', 'per_page': 1})
    total_issues = s.json().get('total_count', 0) if s is not None and s.status_code == 200 else 0

    return {
        'ok': True,
        'repo': d['full_name'],
        'description': (d.get('description') or '').strip(),
        'stars': d.get('stargazers_count', 0),
        'open_issues': d.get('open_issues_count', 0),
        'total_issues': total_issues,
        'milestones': milestones,
        'archived': d.get('archived', False),
        'pushed_at': (d.get('pushed_at') or '')[:10],
        'has_issues': d.get('has_issues', False),
    }


def score(reviews: int, total_issues: int, milestones: int, archived: bool,
          star_spread: int) -> float:
    """Both sides must be substantial; a dead or issue-less repo is unusable."""
    if archived or total_issues < 50:
        return 0.0
    import math
    review_pts = min(1.0, math.log10(max(reviews, 1)) / 4)      # 10k reviews -> 1.0
    issue_pts = min(1.0, math.log10(max(total_issues, 1)) / 4)  # 10k issues  -> 1.0
    milestone_pts = min(1.0, milestones / 20)
    spread_pts = min(1.0, star_spread / 5)
    return round(100 * (0.40 * review_pts + 0.35 * issue_pts +
                        0.15 * milestone_pts + 0.10 * spread_pts), 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--top', type=int, default=20)
    ap.add_argument('--min-reviews', type=int, default=200)
    args = ap.parse_args()

    headers = gh_headers()
    if 'Authorization' not in headers:
        print("WARNING: no GITHUB_TOKEN - you will hit the 60 req/hr anonymous limit.\n")

    counts = review_counts(args.min_reviews)
    print(f"{len(counts)} apps in sealuzh with >= {args.min_reviews} usable reviews")
    candidates = {p: c for p, c in counts.items() if p in PACKAGE_TO_REPO}
    print(f"{len(candidates)} of them have a known GitHub repo - verifying each...\n")

    results = []
    for pkg, stats in sorted(candidates.items(), key=lambda kv: -kv[1]['reviews']):
        repo = PACKAGE_TO_REPO[pkg]
        info = probe_repo(repo, headers)
        if not info.get('ok'):
            print(f"  skip  {repo:<45} {info.get('error')}")
            continue
        if not info['has_issues'] or info['archived'] or info['total_issues'] < 50:
            why = 'archived' if info['archived'] else f"only {info['total_issues']} issues"
            print(f"  skip  {repo:<45} {why}")
            continue

        s = score(stats['reviews'], info['total_issues'], info['milestones'],
                  info['archived'], stats['star_spread'])
        results.append({
            'package_name': pkg,
            'source_id': 'sealuzh',
            'repo': info['repo'],
            'description': info['description'],
            'display_name': info['repo'].split('/')[-1],
            'reviews': stats['reviews'],
            'avg_star': stats['avg_star'],
            'total_issues': info['total_issues'],
            'open_issues': info['open_issues'],
            'milestones': info['milestones'],
            'stars': info['stars'],
            'last_push': info['pushed_at'],
            'score': s,
        })
        print(f"  ok    {info['repo']:<45} {stats['reviews']:>6} reviews  "
              f"{info['total_issues']:>6} issues  score {s}")

    for extra in EXTRA_PRODUCTS:
        info = probe_repo(extra['repo'], headers)
        if not info.get('ok') or not info['has_issues']:
            print(f"  skip  {extra['repo']:<45} unreachable")
            continue
        results.append({
            'package_name': extra['package_name'],
            'source_id': extra['source_id'],
            'repo': info['repo'],
            'description': info['description'],
            'display_name': extra['display_name'],
            'reviews': extra['reviews'],
            'avg_star': extra['avg_star'],
            'total_issues': info['total_issues'],
            'open_issues': info['open_issues'],
            'milestones': info['milestones'],
            'stars': info['stars'],
            'last_push': info['pushed_at'],
            'score': score(extra['reviews'], info['total_issues'], info['milestones'],
                           info['archived'], extra['star_spread']),
        })
        print(f"  ok    {info['repo']:<45} {extra['reviews']:>6} reviews  "
              f"{info['total_issues']:>6} issues  [{extra['source_id']}]")

    results.sort(key=lambda r: -r['score'])
    top = results[:args.top]

    print(f"\n{'='*98}\nTOP {len(top)} ANALYSABLE PRODUCTS\n{'='*98}")
    print(f"{'#':<3} {'score':<7} {'reviews':<9} {'issues':<8} {'ms':<4} {'source':<10} "
          f"{'repo':<40} key")
    for i, r in enumerate(top, 1):
        print(f"{i:<3} {r['score']:<7} {r['reviews']:<9} {r['total_issues']:<8} "
              f"{r['milestones']:<4} {r.get('source_id', 'sealuzh'):<10} {r['repo']:<40} "
              f"{r['package_name']}")

    with open('discovered_projects.json', 'w', encoding='utf-8') as f:
        json.dump(top, f, indent=2, ensure_ascii=False)
    print(f"\nSaved -> discovered_projects.json")
    print("Run any of them with:  ANALYSIS_PACKAGE=<package>  GITHUB_REPO=<repo>")


if __name__ == '__main__':
    main()
