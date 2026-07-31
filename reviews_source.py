import os
from typing import List, Dict
import duckdb
from dotenv import load_dotenv

load_dotenv()

PARQUET_URL = "https://huggingface.co/datasets/sealuzh/app_reviews/resolve/main/data/train-00000-of-00001.parquet"


def fetch_reviews(package_name: str = None) -> List[Dict]:
    """Pull reviews for a package from the sealuzh/app_reviews HF dataset."""
    package_name = package_name or os.getenv('HF_REVIEW_PACKAGE', 'org.torproject.android')

    con = duckdb.connect()
    rows = con.execute(
        f"""
        SELECT review, star, date
        FROM read_parquet('{PARQUET_URL}')
        WHERE package_name = ?
        """,
        [package_name],
    ).fetchall()

    reviews = []
    seen = set()
    for review_text, star, date in rows:
        if not review_text:
            continue
        text = review_text.strip()
        if len(text) < 15:
            continue
        key = text[:100].lower()
        if key in seen:
            continue
        seen.add(key)
        reviews.append({'review_text': text, 'star': star, 'review_date': date})

    return reviews
