import os
import time
from typing import List, Dict
import requests
from dotenv import load_dotenv

from product import CURRENT

load_dotenv()


class GitHubClient:
    def __init__(self, repo: str = None):
        self.repo = repo or CURRENT.repo
        self.token = os.getenv('GITHUB_TOKEN')
        self.base_url = f"https://api.github.com/repos/{self.repo}"
        self.headers = {'Accept': 'application/vnd.github+json'}
        if self.token:
            self.headers['Authorization'] = f'Bearer {self.token}'

    # GitHub refuses to paginate past 10,000 items (page * per_page), answering 422.
    # Large repos like hrydgard/ppsspp exceed that, so we cap and take the most
    # recently updated slice - which is also the part of the roadmap that reflects
    # what the team is working on now.
    MAX_ITEMS = 10000
    PER_PAGE = 100

    def _paginated_get(self, path: str, params: Dict = None, on_page=None) -> List[Dict]:
        params = dict(params or {})
        params['per_page'] = self.PER_PAGE
        max_pages = self.MAX_ITEMS // self.PER_PAGE
        page = 1
        results = []
        while page <= max_pages:
            params['page'] = page
            resp = requests.get(f"{self.base_url}{path}", headers=self.headers, params=params)

            if resp.status_code == 403 and 'rate limit' in resp.text.lower():
                reset = int(resp.headers.get('X-RateLimit-Reset', time.time() + 60))
                wait = max(reset - time.time(), 1)
                raise RuntimeError(
                    f"GitHub rate limit exceeded. Resets in {int(wait)}s. "
                    f"Set GITHUB_TOKEN in .env to raise the limit to 5000/hr."
                )
            if resp.status_code == 422:
                # Hit the pagination ceiling - keep what we already have.
                break

            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            results.extend(batch)
            if on_page:
                on_page(len(results))
            if len(batch) < self.PER_PAGE:
                break
            page += 1
        return results

    def fetch_milestones(self) -> List[Dict]:
        raw = self._paginated_get('/milestones', {'state': 'all'})
        return [
            {
                'id': m['number'],
                'title': m['title'],
                'state': m['state'],
                'open_issues': m['open_issues'],
                'closed_issues': m['closed_issues'],
                'due_on': m.get('due_on'),
            }
            for m in raw
        ]

    def fetch_issues(self, on_page=None) -> List[Dict]:
        # sort=updated keeps the freshest, most decision-relevant part of the roadmap
        # when a repo is large enough to hit the 10k pagination ceiling.
        raw = self._paginated_get('/issues', {'state': 'all', 'sort': 'updated',
                                              'direction': 'desc'}, on_page=on_page)
        issues = []
        for i in raw:
            if 'pull_request' in i:
                continue
            issues.append({
                'number': i['number'],
                'title': i['title'],
                'body': i.get('body') or '',
                'state': i['state'],
                # 'completed' = the team shipped it, 'not_planned' = they saw it and declined.
                # This distinction decides whether a closed ticket counts as COVERED or as a gap.
                'state_reason': i.get('state_reason'),
                'labels': [l['name'] for l in i.get('labels', [])],
                'milestone_title': i['milestone']['title'] if i.get('milestone') else None,
                'reactions_plus1': i.get('reactions', {}).get('+1', 0),
                'comments': i.get('comments', 0),
                'created_at': i.get('created_at'),
                'closed_at': i.get('closed_at'),
                'html_url': i.get('html_url'),
            })
        return issues
