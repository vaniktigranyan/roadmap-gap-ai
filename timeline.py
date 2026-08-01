# -*- coding: utf-8 -*-
"""
Response latency: how long the roadmap took to answer a need users had already voiced.

This is the core "silent stakeholder" measurement. The review corpus runs Dec 2015 - May 2017,
while 889 of the 932 roadmap issues were opened after the last review was written. So for each
need we can state, from data alone, how many years passed between users signalling it and the
team framing a ticket for it - or that no ticket ever framed it at all.
"""
from datetime import datetime, date
from typing import Dict, List, Optional

_REVIEW_FMT = "%B %d %Y"


def parse_review_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), _REVIEW_FMT).date()
    except (ValueError, AttributeError):
        return None


def parse_iso(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def humanize_span(days: Optional[int]) -> Optional[str]:
    """'5y 10m' / '7m' / '12d' - compact enough to sit inside a card."""
    if days is None:
        return None
    if days < 0:
        days = 0
    years, rem = divmod(days, 365)
    months = rem // 30
    if years and months:
        return f"{years}y {months}m"
    if years:
        return f"{years}y"
    if months:
        return f"{months}m"
    return f"{days}d"


def month_label(d: Optional[date]) -> str:
    return d.strftime("%b %Y") if d else "—"


def gap_timeline(gap: Dict, reviews_by_id: Dict, issues_by_number: Dict) -> Dict:
    """
    Returns the signal window, what the roadmap did, and the latency between them.

    status:
      never    - no issue ever matched this need (verdict IGNORED)
      open     - a ticket exists and is still open
      resolved - the ticket was closed as completed
      declined - the ticket was closed as not_planned
    """
    ev_dates = sorted(
        d for d in (
            parse_review_date(reviews_by_id[i].get('review_date'))
            for i in gap.get('evidence_review_ids', []) if i in reviews_by_id
        ) if d
    )
    first_signal = ev_dates[0] if ev_dates else None
    last_signal = ev_dates[-1] if ev_dates else None

    out = {
        'first_signal': first_signal,
        'last_signal': last_signal,
        'n_signals': len(ev_dates),
        'issue_number': None,
        'issue_created': None,
        'issue_closed': None,
        'status': 'never',
        'latency_days': None,
        'latency_label': None,
        'resolution_days': None,
        'resolution_label': None,
        'closest_number': gap.get('closest_issue_number'),
        'closest_similarity': gap.get('closest_issue_similarity'),
        'closest_created': None,
    }

    closest = issues_by_number.get(gap.get('closest_issue_number'))
    if closest:
        out['closest_created'] = parse_iso(closest.get('created_at'))

    issue = issues_by_number.get(gap.get('matched_issue_number'))
    if not issue:
        return out

    created = parse_iso(issue.get('created_at'))
    closed = parse_iso(issue.get('closed_at'))
    out.update({
        'issue_number': issue['number'],
        'issue_created': created,
        'issue_closed': closed,
    })

    if issue.get('state') == 'open':
        out['status'] = 'open'
    elif issue.get('state_reason') == 'not_planned':
        out['status'] = 'declined'
    else:
        out['status'] = 'resolved'

    # Latency is measured from the last time users voiced it: the fairest reading,
    # since the team could only respond to signals that already existed.
    if created and last_signal:
        out['latency_days'] = (created - last_signal).days
        out['latency_label'] = humanize_span(out['latency_days'])
    if closed and last_signal:
        out['resolution_days'] = (closed - last_signal).days
        out['resolution_label'] = humanize_span(out['resolution_days'])

    return out


def corpus_summary(gaps: List[Dict], reviews_by_id: Dict, issues_by_number: Dict) -> Dict:
    """Headline latency figures across the ranked gaps."""
    tls = [gap_timeline(g, reviews_by_id, issues_by_number) for g in gaps]
    never = sum(1 for t in tls if t['status'] == 'never')
    latencies = [t['latency_days'] for t in tls if t['latency_days'] is not None]
    latencies.sort()
    median = latencies[len(latencies) // 2] if latencies else None
    return {
        'timelines': tls,
        'never_count': never,
        'median_latency_days': median,
        'median_latency_label': humanize_span(median),
        'worst_latency_label': humanize_span(max(latencies)) if latencies else None,
    }
