# -*- coding: utf-8 -*-
"""Thin wrapper kept for backwards compatibility - the real work lives in sources.py."""
from typing import List, Dict

from product import CURRENT
from sources import fetch_reviews_from


def fetch_reviews(package_name: str = None, source_id: str = None) -> List[Dict]:
    """Pull user signals for a product from whichever dataset it belongs to."""
    return fetch_reviews_from(source_id or CURRENT.source_id,
                              package_name or CURRENT.package_name)
