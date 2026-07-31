import os
import time
from typing import List, Dict
import requests
from dotenv import load_dotenv

load_dotenv()


class GitHubClient:
    def __init__(self, repo: str = None):
        self.repo = repo or os.getenv('GITHUB_REPO', 'guardianproject/orbot-android')
        self.token = os.getenv('GITHUB_TOKEN')
        self.base_url = f"https://api.github.com/repos/{self.repo}"
        self.headers = {'Accept': 'application/vnd.github+json'}
        if self.token:
            self.headers['Authorization'] = f'Bearer {self.token}'

    def _paginated_get(self, path: str, params: Dict = None) -> List[Dict]:
        params = dict(params or {})
        params['per_page'] = 100
        page = 1
        results = []
        while True:
            params['page'] = page
            resp = requests.get(f"{self.base_url}{path}", headers=self.headers, params=params)
            if resp.status_code == 403 and 'rate limit' in resp.text.lower():
                reset = int(resp.headers.get('X-RateLimit-Reset', time.time() + 60))
                wait = max(reset - time.time(), 1)
                raise RuntimeError(
                    f"GitHub rate limit exceeded. Resets in {int(wait)}s. "
                    f"Set GITHUB_TOKEN in .env to raise the limit to 5000/hr."
                )
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            results.extend(batch)
            if len(batch) < 100:
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

    def fetch_issues(self) -> List[Dict]:
        raw = self._paginated_get('/issues', {'state': 'all'})
        issues = []
        for i in raw:
            if 'pull_request' in i:
                continue
            issues.append({
                'number': i['number'],
                'title': i['title'],
                'body': i.get('body') or '',
                'state': i['state'],
                'labels': [l['name'] for l in i.get('labels', [])],
                'milestone_title': i['milestone']['title'] if i.get('milestone') else None,
                'reactions_plus1': i.get('reactions', {}).get('+1', 0),
                'comments': i.get('comments', 0),
                'created_at': i.get('created_at'),
                'closed_at': i.get('closed_at'),
                'html_url': i.get('html_url'),
            })
        return issues
