import os
import json
import math
import re
import time
from typing import List, Dict, Optional
import numpy as np
from sklearn.cluster import KMeans
from sentence_transformers import SentenceTransformer
from openai import OpenAI, RateLimitError, APIStatusError
from dotenv import load_dotenv

load_dotenv()

EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
GEN_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

VERDICT_GAP_CERTAINTY = {
    'IGNORED': 1.0,
    'UNDER-PRIORITIZED': 0.75,
    'MISUNDERSTOOD': 0.6,
}

WEIGHTS = {
    'evidence_count': 0.35,
    'rating_spread': 0.15,
    'consistency': 0.25,
    'roadmap_gap_certainty': 0.25,
}


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    text = re.sub(r'^```(json)?', '', text).strip()
    text = re.sub(r'```$', '', text).strip()
    return text


def _with_retry(fn, max_attempts: int = 5):
    for attempt in range(max_attempts):
        try:
            return fn()
        except RateLimitError:
            if attempt < max_attempts - 1:
                wait = 15 * (attempt + 1)
                print(f"Rate limited, waiting {wait}s (attempt {attempt + 1}/{max_attempts})...")
                time.sleep(wait)
                continue
            raise
        except APIStatusError as e:
            if e.status_code in (429, 500, 502, 503, 529) and attempt < max_attempts - 1:
                wait = 10 * (attempt + 1)
                print(f"API busy ({e.status_code}), waiting {wait}s (attempt {attempt + 1}/{max_attempts})...")
                time.sleep(wait)
                continue
            raise


class GapAnalyzer:
    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = OpenAI(api_key=api_key)
        self._embedder = None

    @property
    def embedder(self) -> SentenceTransformer:
        if self._embedder is None:
            self._embedder = SentenceTransformer(EMBED_MODEL_NAME)
        return self._embedder

    # ---- Embeddings (local, free, no rate limits) ----
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        return self.embedder.encode(texts, show_progress_bar=False, convert_to_numpy=True)

    def _generate_json(self, prompt: str) -> dict:
        response = _with_retry(lambda: self.client.chat.completions.create(
            model=GEN_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        ))
        return json.loads(_strip_json_fence(response.choices[0].message.content))

    # ---- Clustering ----
    def cluster_taxonomy(self, issues: List[Dict], reviews: List[Dict]):
        issue_texts = [f"{i['title']}\n{i['body'][:500]}" for i in issues]
        review_texts = [r['review_text'][:500] for r in reviews]

        all_texts = issue_texts + review_texts
        embeddings = self.embed_texts(all_texts)

        issue_emb = embeddings[:len(issues)]
        review_emb = embeddings[len(issues):]

        n_items = len(all_texts)
        k = min(14, max(5, n_items // 45))
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(embeddings)

        issue_labels = labels[:len(issues)]
        review_labels = labels[len(issues):]

        cluster_info = self._label_clusters(k, issues, reviews, issue_labels, review_labels)

        return {
            'issue_embeddings': issue_emb,
            'review_embeddings': review_emb,
            'issue_clusters': issue_labels,
            'review_clusters': review_labels,
            'clusters': cluster_info,
        }

    def _label_clusters(self, k, issues, reviews, issue_labels, review_labels) -> Dict[int, Dict]:
        samples = {}
        for cid in range(k):
            issue_sample = [issues[i]['title'] for i in np.where(issue_labels == cid)[0][:4]]
            review_sample = [reviews[i]['review_text'][:150] for i in np.where(review_labels == cid)[0][:4]]
            samples[cid] = {
                'issue_titles': issue_sample,
                'review_snippets': review_sample,
                'issue_count': int(np.sum(issue_labels == cid)),
                'review_count': int(np.sum(review_labels == cid)),
            }

        prompt = f"""You are naming functional areas of an Android privacy app (Orbot, a Tor proxy app).
Given clusters of GitHub issue titles and user review snippets, give each cluster a short (2-5 word)
functional area label, e.g. "Bridges & censorship circumvention", "Battery drain", "VPN/tethering mode",
"Onboarding & UX", "Notifications", "Stability & crashes", "Connection speed".

Clusters:
{json.dumps(samples, indent=2)}

Return JSON: {{"0": "label", "1": "label", ...}} keyed by cluster id as string, one entry per cluster id 0..{k - 1}."""

        labels_map = self._generate_json(prompt)

        clusters = {}
        for cid in range(k):
            clusters[cid] = {
                'id': cid,
                'label': labels_map.get(str(cid), f"Cluster {cid}"),
                'issue_count': samples[cid]['issue_count'],
                'review_count': samples[cid]['review_count'],
            }
        return clusters

    # ---- Need extraction ----
    def extract_needs_for_cluster(self, cluster_label: str, reviews: List[Dict], min_reviews: int = 8) -> List[Dict]:
        if len(reviews) < min_reviews:
            return []

        sample = reviews[:60]
        reviews_block = "\n".join(
            f"[{r['id']}] ({r.get('star', '?')}★) {r['review_text'][:300]}" for r in sample
        )

        prompt = f"""You are analyzing user reviews of Orbot (a Tor anonymity/proxy Android app) in the
functional area "{cluster_label}".

Reviews (format: [review_id] (stars) text):
{reviews_block}

Your job is NOT to summarize complaints. Find LATENT needs: things users need but don't say directly.
Look for second-order signals: workarounds people describe, comparisons to other apps/tools, contradictions
(e.g. praise + a quiet workaround), recurring context clues about *why* something is used, patterns that
only show up across multiple reviews rather than in any single one.

Return JSON: {{"needs": [{{"need": "clear statement of the underlying need in user terms",
"supporting_review_ids": [id, id, ...], "rationale": "why this is a latent (not surface) need"}}]}}

Only include needs with at least 3 supporting review ids. Return at most 3 needs. If nothing latent found,
return {{"needs": []}}."""

        try:
            result = self._generate_json(prompt)
            return result.get('needs', [])
        except Exception as e:
            print(f"Need extraction error for cluster '{cluster_label}': {e}")
            return []

    # ---- Matching + verdict ----
    def match_and_verdict(self, need_text: str, need_embedding: np.ndarray,
                           cluster_issues: List[Dict], cluster_issue_embeddings: np.ndarray) -> Dict:
        if len(cluster_issues) == 0:
            return {'matched_issue': None, 'verdict': 'IGNORED', 'reasoning': 'No roadmap issues exist in this functional area at all.'}

        sims = cluster_issue_embeddings @ need_embedding / (
            np.linalg.norm(cluster_issue_embeddings, axis=1) * np.linalg.norm(need_embedding) + 1e-9
        )
        best_idx = int(np.argmax(sims))
        best_sim = float(sims[best_idx])
        best_issue = cluster_issues[best_idx]

        if best_sim < 0.4:
            return {'matched_issue': None, 'verdict': 'IGNORED',
                     'reasoning': f'No roadmap issue found addressing this (best similarity {best_sim:.2f} below threshold).'}

        prompt = f"""User need: "{need_text}"

Closest matching GitHub roadmap issue:
Title: {best_issue['title']}
Body: {best_issue['body'][:800]}
State: {best_issue['state']}
Milestone: {best_issue.get('milestone_title') or 'none (unscheduled)'}
Community reactions (+1): {best_issue.get('reactions_plus1', 0)}
Comments: {best_issue.get('comments', 0)}

Classify the relationship between the user need and this issue. Choose exactly one:
- "COVERED": the issue, if implemented, would fully satisfy the user need as stated
- "UNDER-PRIORITIZED": the issue addresses the need but is stale/unscheduled/low-engagement (backlog, no milestone, open a long time, few reactions)
- "MISUNDERSTOOD": the issue is nominally in the same area but is framed around a different problem than the actual user need (e.g. solves a technical symptom, not the workflow need)

Return JSON: {{"verdict": "COVERED"|"UNDER-PRIORITIZED"|"MISUNDERSTOOD", "reasoning": "one or two sentences citing specifics from the issue text"}}"""

        try:
            result = self._generate_json(prompt)
            return {
                'matched_issue': best_issue['number'],
                'verdict': result.get('verdict', 'UNDER-PRIORITIZED'),
                'reasoning': result.get('reasoning', ''),
                'similarity': best_sim,
            }
        except Exception as e:
            return {'matched_issue': best_issue['number'], 'verdict': 'UNDER-PRIORITIZED',
                     'reasoning': f'LLM verdict classification failed ({e}); defaulting based on match.',
                     'similarity': best_sim}

    # ---- Confidence ----
    @staticmethod
    def compute_confidence(supporting_reviews: List[Dict], review_embeddings: np.ndarray, verdict: str) -> Dict:
        n = len(supporting_reviews)
        evidence_count = min(1.0, math.log(1 + n) / math.log(1 + 30))

        stars = set(r.get('star') for r in supporting_reviews if r.get('star') is not None)
        rating_spread = min(1.0, len(stars) / 3)

        if len(review_embeddings) >= 2:
            norm = review_embeddings / (np.linalg.norm(review_embeddings, axis=1, keepdims=True) + 1e-9)
            sim_matrix = norm @ norm.T
            iu = np.triu_indices(len(norm), k=1)
            consistency = float(np.mean(sim_matrix[iu])) if len(iu[0]) > 0 else 1.0
            consistency = max(0.0, min(1.0, consistency))
        else:
            consistency = 0.5

        gap_certainty = VERDICT_GAP_CERTAINTY.get(verdict, 0.5)

        confidence = (
            WEIGHTS['evidence_count'] * evidence_count +
            WEIGHTS['rating_spread'] * rating_spread +
            WEIGHTS['consistency'] * consistency +
            WEIGHTS['roadmap_gap_certainty'] * gap_certainty
        )

        return {
            'confidence': round(confidence * 100, 1),
            'components': {
                'evidence_count_norm': round(evidence_count, 3),
                'rating_spread': round(rating_spread, 3),
                'cross_signal_consistency': round(consistency, 3),
                'roadmap_gap_certainty': gap_certainty,
                'supporting_review_count': n,
            },
        }

    # ---- Full pipeline ----
    def run(self, issues: List[Dict], reviews: List[Dict], top_n: int = 5) -> Dict:
        taxonomy = self.cluster_taxonomy(issues, reviews)
        clusters = taxonomy['clusters']

        candidates = []
        for cid, info in clusters.items():
            cluster_reviews = [r for i, r in enumerate(reviews) if taxonomy['review_clusters'][i] == cid]
            cluster_review_idx = [i for i, c in enumerate(taxonomy['review_clusters']) if c == cid]
            cluster_review_emb = taxonomy['review_embeddings'][cluster_review_idx]

            needs = self.extract_needs_for_cluster(info['label'], cluster_reviews)

            for need in needs:
                support_ids = set(need.get('supporting_review_ids', []))
                idx_map = {r['id']: i for i, r in enumerate(cluster_reviews)}
                support_local_idx = [idx_map[rid] for rid in support_ids if rid in idx_map]
                if len(support_local_idx) < 3:
                    continue
                support_reviews = [cluster_reviews[i] for i in support_local_idx]
                support_emb = cluster_review_emb[support_local_idx]

                need_emb = self.embed_texts([need['need']])[0]
                # Match against the FULL issue pool, not just this cluster: KMeans is
                # imperfect on short noisy text and can silo a genuinely relevant issue
                # into a different cluster than the review topic that names the same need.
                match = self.match_and_verdict(need['need'], need_emb, issues, taxonomy['issue_embeddings'])

                reasoning = f"{need.get('rationale', '')} | Roadmap check: {match.get('reasoning', '')}"

                if match['verdict'] == 'COVERED':
                    # Kept (not discarded) so a judge asking "did you consider X?" can be
                    # answered: yes, and here's why it was excluded (roadmap already covers it).
                    candidates.append({
                        'need_text': need['need'],
                        'verdict': 'COVERED',
                        'confidence': None,
                        'confidence_components': {},
                        'evidence_review_ids': [r['id'] for r in support_reviews],
                        'matched_issue_number': match.get('matched_issue'),
                        'reasoning': reasoning,
                        'cluster_id': cid,
                    })
                    continue

                conf = self.compute_confidence(support_reviews, support_emb, match['verdict'])

                candidates.append({
                    'need_text': need['need'],
                    'verdict': match['verdict'],
                    'confidence': conf['confidence'],
                    'confidence_components': conf['components'],
                    'evidence_review_ids': [r['id'] for r in support_reviews],
                    'matched_issue_number': match.get('matched_issue'),
                    'reasoning': reasoning,
                    'cluster_id': cid,
                })

        gap_candidates = [c for c in candidates if c['verdict'] != 'COVERED']
        gap_candidates.sort(key=lambda g: g['confidence'], reverse=True)
        top_gaps = gap_candidates[:top_n]

        all_candidates_sorted = sorted(candidates, key=lambda c: (c['confidence'] is None, -(c['confidence'] or 0)))

        return {'gaps': top_gaps, 'all_candidates': all_candidates_sorted, 'clusters': clusters,
                'issue_clusters': taxonomy['issue_clusters'], 'review_clusters': taxonomy['review_clusters']}
