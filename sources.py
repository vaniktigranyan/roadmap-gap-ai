# -*- coding: utf-8 -*-
"""
Pluggable user-signal sources.

The brief allows five datasets. The binding constraint is not size but whether a
signal can be tied to ONE product that also has a public GitHub roadmap - without
that, "same product, both sides" is impossible. Each adapter below therefore
declares how it identifies a product, and we verified every dataset against that
test rather than assuming:

  sealuzh/app_reviews          package_name (395 apps)      USABLE - the backbone
  play_market_2025_1m          app_name (217 apps, but      USABLE for the handful
                               only 42 carry reviews)       that are open source
  Kerassy/trustpilot-reviews   company domain (1579)        NOT USABLE - checked all
                                                            1579; every one is UK
                                                            retail/services, none has
                                                            a public issue tracker
  Tobi-Bueck/customer-support  no product field at all      NOT USABLE - synthetic
                               (subject/body/queue only)     multi-language tickets
  Kaggle 200k support tickets  requires Kaggle credentials  NOT REACHABLE - API
                                                            answers 403 without a key

Adding a source later means writing one `fetch` function and registering it.
"""
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

import duckdb

SEALUZH_URL = ("https://huggingface.co/datasets/sealuzh/app_reviews/resolve/main/"
               "data/train-00000-of-00001.parquet")
PLAY2025_BASE = ("https://huggingface.co/datasets/dmytrobuhai/"
                 "play_market_2025_1m_reviews_500_titles/resolve/main/")
TRUSTPILOT_URL = ("https://huggingface.co/datasets/Kerassy/trustpilot-reviews-123k/"
                  "resolve/main/trustpilot_reviews_2005.csv")

MIN_REVIEW_CHARS = 15


def _clean(rows) -> List[Dict]:
    """Drop empties, drop stubs too short to carry a signal, de-duplicate."""
    out, seen = [], set()
    for text, star, date in rows:
        if not text:
            continue
        text = str(text).strip()
        if len(text) < MIN_REVIEW_CHARS:
            continue
        key = text[:100].lower()
        if key in seen:
            continue
        seen.add(key)
        out.append({'review_text': text, 'star': star, 'review_date': date})
    return out


# ---------------------------------------------------------------- adapters
def fetch_sealuzh(product_key: str) -> List[Dict]:
    """Android reviews keyed by package name. Corpus spans 2014 - May 2017."""
    con = duckdb.connect()
    rows = con.execute(
        f"SELECT review, star, date FROM read_parquet('{SEALUZH_URL}') WHERE package_name = ?",
        [product_key],
    ).fetchall()
    return _clean(rows)


def fetch_play_market_2025(product_key: str) -> List[Dict]:
    """Google Play reviews keyed by app name. Corpus runs to Apr 2025."""
    con = duckdb.connect()
    rows = con.execute(
        f"""SELECT r.review_text, r.review_score, CAST(r.review_date AS VARCHAR)
            FROM read_csv_auto('{PLAY2025_BASE}apps_reviews.csv') r
            JOIN read_csv_auto('{PLAY2025_BASE}apps_info.csv') i ON i.app_id = r.app_id
            WHERE i.app_name = ?""",
        [product_key],
    ).fetchall()
    return _clean(rows)


def fetch_trustpilot(product_key: str) -> List[Dict]:
    """Trustpilot reviews keyed by company domain. Kept for completeness - no company
    in this corpus has a public roadmap, so it cannot currently source a product."""
    con = duckdb.connect()
    rows = con.execute(
        f"""SELECT review, stars, NULL
            FROM read_csv_auto('{TRUSTPILOT_URL}', ignore_errors=true)
            WHERE company = ?""",
        [product_key],
    ).fetchall()
    return _clean(rows)


@dataclass(frozen=True)
class Source:
    id: str
    label: str
    key_field: str          # the column that identifies a product
    fetch: Optional[Callable[[str], List[Dict]]]
    usable: bool
    note: str

    def __call__(self, product_key: str) -> List[Dict]:
        if not self.usable or self.fetch is None:
            raise RuntimeError(f"Source '{self.id}' cannot source a product: {self.note}")
        return self.fetch(product_key)


SOURCES: Dict[str, Source] = {
    'sealuzh': Source(
        id='sealuzh',
        label='sealuzh/app_reviews — Android reviews (2014–2017)',
        key_field='package_name',
        fetch=fetch_sealuzh,
        usable=True,
        note='395 apps, mostly open source, so package names map to GitHub repos.',
    ),
    'play2025': Source(
        id='play2025',
        label='play_market_2025 — Google Play reviews (to Apr 2025)',
        key_field='app_name',
        fetch=fetch_play_market_2025,
        usable=True,
        note='217 apps listed but only 42 carry reviews; nearly all are closed-source.',
    ),
    'trustpilot': Source(
        id='trustpilot',
        label='Kerassy/trustpilot-reviews-123k — company reviews',
        key_field='company',
        fetch=fetch_trustpilot,
        usable=False,
        note='All 1579 companies are UK retail/services; none has a public issue tracker, '
             'so no product can have both sides.',
    ),
    'tickets_hf': Source(
        id='tickets_hf',
        label='Tobi-Bueck/customer-support-tickets',
        key_field='(none)',
        fetch=None,
        usable=False,
        note='Columns are subject/body/answer/queue/priority only - the tickets name no '
             'product, so they cannot be paired with any roadmap.',
    ),
    'tickets_kaggle': Source(
        id='tickets_kaggle',
        label='Kaggle 200k customer support tickets',
        key_field='(unknown)',
        fetch=None,
        usable=False,
        note='Kaggle API returns 403 without credentials, so the schema cannot be verified.',
    ),
}

DEFAULT_SOURCE = 'sealuzh'


def get_source(source_id: str) -> Source:
    if source_id not in SOURCES:
        raise ValueError(f"Unknown source '{source_id}'. Known: {', '.join(SOURCES)}")
    return SOURCES[source_id]


def usable_sources() -> List[Source]:
    return [s for s in SOURCES.values() if s.usable]


def fetch_reviews_from(source_id: str, product_key: str) -> List[Dict]:
    return get_source(source_id)(product_key)
