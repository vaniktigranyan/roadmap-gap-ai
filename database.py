import sqlite3
import json
from typing import List, Dict, Optional


class GapAnalysisDB:
    def __init__(self, db_path: str = "gaps.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS milestones (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    state TEXT,
                    open_issues INTEGER,
                    closed_issues INTEGER,
                    due_on TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS issues (
                    number INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    body TEXT,
                    state TEXT,
                    labels TEXT,
                    milestone_title TEXT,
                    reactions_plus1 INTEGER,
                    comments INTEGER,
                    created_at TEXT,
                    closed_at TEXT,
                    html_url TEXT,
                    cluster_id INTEGER
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    review_text TEXT NOT NULL,
                    star INTEGER,
                    review_date TEXT,
                    cluster_id INTEGER
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clusters (
                    id INTEGER PRIMARY KEY,
                    label TEXT,
                    issue_count INTEGER,
                    review_count INTEGER
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gaps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    need_text TEXT NOT NULL,
                    verdict TEXT,
                    confidence REAL,
                    confidence_components TEXT,
                    evidence_review_ids TEXT,
                    matched_issue_number INTEGER,
                    reasoning TEXT,
                    cluster_id INTEGER,
                    rank INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    need_text TEXT NOT NULL,
                    verdict TEXT,
                    confidence REAL,
                    confidence_components TEXT,
                    evidence_review_ids TEXT,
                    matched_issue_number INTEGER,
                    reasoning TEXT,
                    cluster_id INTEGER,
                    in_top5 INTEGER DEFAULT 0
                )
            ''')

            conn.commit()

    # ---- Milestones ----
    def replace_milestones(self, milestones: List[Dict]):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM milestones')
            for m in milestones:
                cursor.execute('''
                    INSERT INTO milestones (id, title, state, open_issues, closed_issues, due_on)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (m['id'], m['title'], m['state'], m['open_issues'], m['closed_issues'], m.get('due_on')))
            conn.commit()

    def get_milestones(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, title, state, open_issues, closed_issues, due_on FROM milestones')
            cols = ['id', 'title', 'state', 'open_issues', 'closed_issues', 'due_on']
            return [dict(zip(cols, row)) for row in cursor.fetchall()]

    # ---- Issues ----
    def replace_issues(self, issues: List[Dict]):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM issues')
            for i in issues:
                cursor.execute('''
                    INSERT INTO issues
                    (number, title, body, state, labels, milestone_title, reactions_plus1,
                     comments, created_at, closed_at, html_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    i['number'], i['title'], i.get('body', ''), i['state'],
                    json.dumps(i.get('labels', [])), i.get('milestone_title'),
                    i.get('reactions_plus1', 0), i.get('comments', 0),
                    i.get('created_at'), i.get('closed_at'), i.get('html_url')
                ))
            conn.commit()

    def get_issues(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT number, title, body, state, labels, milestone_title,
                       reactions_plus1, comments, created_at, closed_at, html_url, cluster_id
                FROM issues
            ''')
            cols = ['number', 'title', 'body', 'state', 'labels', 'milestone_title',
                    'reactions_plus1', 'comments', 'created_at', 'closed_at', 'html_url', 'cluster_id']
            result = []
            for row in cursor.fetchall():
                d = dict(zip(cols, row))
                d['labels'] = json.loads(d['labels'] or '[]')
                result.append(d)
            return result

    def set_issue_clusters(self, number_to_cluster: Dict[int, int]):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany(
                'UPDATE issues SET cluster_id = ? WHERE number = ?',
                [(cid, num) for num, cid in number_to_cluster.items()]
            )
            conn.commit()

    # ---- Reviews ----
    def replace_reviews(self, reviews: List[Dict]):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM reviews')
            cursor.executemany('''
                INSERT INTO reviews (review_text, star, review_date)
                VALUES (?, ?, ?)
            ''', [(r['review_text'], r.get('star'), r.get('review_date')) for r in reviews])
            conn.commit()

    def get_reviews(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, review_text, star, review_date, cluster_id FROM reviews')
            cols = ['id', 'review_text', 'star', 'review_date', 'cluster_id']
            return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def set_review_clusters(self, id_to_cluster: Dict[int, int]):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany(
                'UPDATE reviews SET cluster_id = ? WHERE id = ?',
                [(cid, rid) for rid, cid in id_to_cluster.items()]
            )
            conn.commit()

    # ---- Clusters ----
    def replace_clusters(self, clusters: List[Dict]):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM clusters')
            for c in clusters:
                cursor.execute('''
                    INSERT INTO clusters (id, label, issue_count, review_count)
                    VALUES (?, ?, ?, ?)
                ''', (c['id'], c['label'], c.get('issue_count', 0), c.get('review_count', 0)))
            conn.commit()

    def get_clusters(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, label, issue_count, review_count FROM clusters')
            cols = ['id', 'label', 'issue_count', 'review_count']
            return [dict(zip(cols, row)) for row in cursor.fetchall()]

    # ---- Gaps ----
    def replace_gaps(self, gaps: List[Dict]):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM gaps')
            for rank, g in enumerate(gaps, start=1):
                cursor.execute('''
                    INSERT INTO gaps
                    (need_text, verdict, confidence, confidence_components,
                     evidence_review_ids, matched_issue_number, reasoning, cluster_id, rank)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    g['need_text'], g['verdict'], g['confidence'],
                    json.dumps(g.get('confidence_components', {})),
                    json.dumps(g.get('evidence_review_ids', [])),
                    g.get('matched_issue_number'), g.get('reasoning', ''),
                    g.get('cluster_id'), rank
                ))
            conn.commit()

    def get_gaps(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT need_text, verdict, confidence, confidence_components,
                       evidence_review_ids, matched_issue_number, reasoning, cluster_id, rank
                FROM gaps ORDER BY rank ASC
            ''')
            cols = ['need_text', 'verdict', 'confidence', 'confidence_components',
                    'evidence_review_ids', 'matched_issue_number', 'reasoning', 'cluster_id', 'rank']
            result = []
            for row in cursor.fetchall():
                d = dict(zip(cols, row))
                d['confidence_components'] = json.loads(d['confidence_components'] or '{}')
                d['evidence_review_ids'] = json.loads(d['evidence_review_ids'] or '[]')
                result.append(d)
            return result

    # ---- Candidates (all, incl. COVERED and non-top5, for live-defense traceability) ----
    def replace_candidates(self, candidates: List[Dict], top5_need_texts: set):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM candidates')
            for c in candidates:
                cursor.execute('''
                    INSERT INTO candidates
                    (need_text, verdict, confidence, confidence_components,
                     evidence_review_ids, matched_issue_number, reasoning, cluster_id, in_top5)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    c['need_text'], c['verdict'], c.get('confidence'),
                    json.dumps(c.get('confidence_components', {})),
                    json.dumps(c.get('evidence_review_ids', [])),
                    c.get('matched_issue_number'), c.get('reasoning', ''),
                    c.get('cluster_id'), int(c['need_text'] in top5_need_texts),
                ))
            conn.commit()

    def get_candidates(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT need_text, verdict, confidence, confidence_components,
                       evidence_review_ids, matched_issue_number, reasoning, cluster_id, in_top5
                FROM candidates ORDER BY confidence DESC NULLS LAST
            ''')
            cols = ['need_text', 'verdict', 'confidence', 'confidence_components',
                    'evidence_review_ids', 'matched_issue_number', 'reasoning', 'cluster_id', 'in_top5']
            result = []
            for row in cursor.fetchall():
                d = dict(zip(cols, row))
                d['confidence_components'] = json.loads(d['confidence_components'] or '{}')
                d['evidence_review_ids'] = json.loads(d['evidence_review_ids'] or '[]')
                d['in_top5'] = bool(d['in_top5'])
                result.append(d)
            return result
