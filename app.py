import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from database import GapAnalysisDB
from github_client import GitHubClient
from reviews_source import fetch_reviews
from gap_analyzer import GapAnalyzer
from i18n import get_text

st.set_page_config(
    page_title="Orbot Gap Analysis",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded",
)

VERDICT_COLORS = {
    'IGNORED': '#dc2626',
    'UNDER-PRIORITIZED': '#d97706',
    'MISUNDERSTOOD': '#7c3aed',
}
VERDICT_LABEL_KEYS = {
    'IGNORED': 'verdict_ignored',
    'UNDER-PRIORITIZED': 'verdict_underprioritized',
    'MISUNDERSTOOD': 'verdict_misunderstood',
    'COVERED': 'verdict_covered',
}

st.markdown(
    """
<style>
    .main-header { font-size: 2.2rem; margin-bottom: 0.2rem; }
    .sub-header { color: #888; margin-bottom: 1.5rem; }
    .gap-card {
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    .verdict-badge {
        display: inline-block;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        color: white;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .evidence-item {
        border-left: 3px solid rgba(128,128,128,0.3);
        padding-left: 0.6rem;
        margin: 0.3rem 0;
        font-size: 0.9rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def get_db():
    return GapAnalysisDB()


def t(key: str, **kwargs) -> str:
    return get_text(st.session_state.get('lang', 'en'), key, **kwargs)


def run_pipeline():
    db = get_db()
    progress = st.progress(0)
    status = st.empty()

    status.text(t('status_fetching_github'))
    gh = GitHubClient()
    milestones = gh.fetch_milestones()
    issues = gh.fetch_issues()
    progress.progress(20)

    status.text(t('status_fetching_reviews'))
    reviews = fetch_reviews()
    progress.progress(35)

    db.replace_milestones(milestones)
    db.replace_issues(issues)
    db.replace_reviews(reviews)
    reviews = db.get_reviews()  # re-read to get assigned ids
    progress.progress(45)

    status.text(t('status_clustering'))
    ga = GapAnalyzer()
    result = ga.run(issues, reviews, top_n=5)
    progress.progress(85)

    status.text(t('status_saving'))
    db.replace_clusters(list(result['clusters'].values()))
    db.set_issue_clusters({issues[i]['number']: int(result['issue_clusters'][i]) for i in range(len(issues))})
    db.set_review_clusters({reviews[i]['id']: int(result['review_clusters'][i]) for i in range(len(reviews))})
    db.replace_gaps(result['gaps'])
    top5_texts = {g['need_text'] for g in result['gaps']}
    db.replace_candidates(result['all_candidates'], top5_texts)
    progress.progress(100)
    status.text(t('status_done'))


def render_gap_card(rank: int, gap: dict, reviews_by_id: dict, issues_by_number: dict):
    color = VERDICT_COLORS.get(gap['verdict'], '#6b7280')
    verdict_label = t(VERDICT_LABEL_KEYS.get(gap['verdict'], 'verdict_ignored'))
    with st.container():
        st.markdown(f'<div class="gap-card">', unsafe_allow_html=True)
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"**#{rank}. {gap['need_text']}**")
            st.markdown(
                f'<span class="verdict-badge" style="background-color:{color}">{verdict_label}</span>',
                unsafe_allow_html=True,
            )
        with col2:
            st.metric(t('confidence_label'), f"{gap['confidence']:.0f}%")

        with st.expander(t('confidence_breakdown')):
            comp = gap['confidence_components']
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(t('evidence_volume'), f"{comp['evidence_count_norm']:.2f}", help=t('evidence_volume_help'))
            c2.metric(t('rating_spread'), f"{comp['rating_spread']:.2f}", help=t('rating_spread_help'))
            c3.metric(t('consistency'), f"{comp['cross_signal_consistency']:.2f}", help=t('consistency_help'))
            c4.metric(t('gap_certainty'), f"{comp['roadmap_gap_certainty']:.2f}", help=t('gap_certainty_help'))
            st.caption(t('supported_by', n=comp['supporting_review_count']))

        st.markdown(f"*{gap['reasoning']}*")

        with st.expander(t('evidence_trace', n=len(gap['evidence_review_ids']))):
            for rid in gap['evidence_review_ids']:
                r = reviews_by_id.get(rid)
                if r:
                    st.markdown(
                        f'<div class="evidence-item">[{rid}] {r.get("star", "?")}★ — {r["review_text"]}</div>',
                        unsafe_allow_html=True,
                    )

        if gap.get('matched_issue_number'):
            issue = issues_by_number.get(gap['matched_issue_number'])
            if issue:
                st.markdown(t(
                    'closest_issue',
                    number=issue['number'], title=issue['title'], url=issue['html_url'],
                    state=issue['state'], milestone=issue.get('milestone_title') or t('none_milestone'),
                ))
        else:
            st.markdown(t('no_matched_issue'))

        st.markdown('</div>', unsafe_allow_html=True)


def render_candidates_table(candidates: list):
    if not candidates:
        return
    rows = []
    for c in candidates:
        rows.append({
            t('candidates_col_need'): c['need_text'],
            t('candidates_col_verdict'): t(VERDICT_LABEL_KEYS.get(c['verdict'], 'verdict_ignored')),
            t('candidates_col_confidence'): f"{c['confidence']:.0f}%" if c['confidence'] is not None else '—',
            t('candidates_col_top5'): '✅' if c['in_top5'] else '',
            t('candidates_col_evidence_count'): len(c['evidence_review_ids']),
            t('candidates_col_matched_issue'): f"#{c['matched_issue_number']}" if c.get('matched_issue_number') else '—',
        })
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def render_cluster_chart(clusters: list):
    if not clusters:
        return
    df = pd.DataFrame(clusters).sort_values('review_count', ascending=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df['label'], x=df['issue_count'], name=t('chart_issues'),
        orientation='h', marker_color='#2563eb',
    ))
    fig.add_trace(go.Bar(
        y=df['label'], x=df['review_count'], name=t('chart_reviews'),
        orientation='h', marker_color='#059669',
    ))
    fig.update_layout(
        barmode='group', height=max(320, 34 * len(df)),
        xaxis_title=t('chart_count_axis'), margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )
    st.plotly_chart(fig, width="stretch")


def main():
    if 'lang' not in st.session_state:
        st.session_state['lang'] = 'en'

    lang_options = {'English': 'en', 'Русский': 'ru'}
    current_label = 'English' if st.session_state['lang'] == 'en' else 'Русский'
    chosen = st.sidebar.selectbox(
        t('language_label'), list(lang_options.keys()),
        index=list(lang_options.keys()).index(current_label),
    )
    st.session_state['lang'] = lang_options[chosen]

    st.markdown(f'<div class="main-header">{t("main_header")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">{t("sub_header")}</div>', unsafe_allow_html=True)

    db = get_db()

    st.sidebar.title(t('sidebar_title'))
    st.sidebar.markdown(t('sidebar_caption'))
    if st.sidebar.button(t('run_button'), type="primary"):
        run_pipeline()

    issues = db.get_issues()
    reviews = db.get_reviews()
    milestones = db.get_milestones()
    clusters = db.get_clusters()
    gaps = db.get_gaps()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t('metric_issues'), len(issues))
    col2.metric(t('metric_reviews'), len(reviews))
    col3.metric(t('metric_milestones'), len(milestones))
    col4.metric(t('metric_clusters'), len(clusters))

    if not gaps:
        st.info(t('no_analysis_yet'))
        return

    st.markdown("---")
    st.header(t('top_needs_header'))
    st.caption(t('top_needs_caption'))

    reviews_by_id = {r['id']: r for r in reviews}
    issues_by_number = {i['number']: i for i in issues}

    for i, gap in enumerate(gaps, start=1):
        render_gap_card(i, gap, reviews_by_id, issues_by_number)

    st.markdown("---")
    st.header(t('clusters_header'))
    st.caption(t('clusters_caption'))
    render_cluster_chart(clusters)

    candidates = db.get_candidates()
    if candidates:
        st.markdown("---")
        st.header(t('candidates_header'))
        st.caption(t('candidates_caption'))
        render_candidates_table(candidates)

    st.markdown("---")
    st.header(t('raw_data_header'))
    tab1, tab2, tab3 = st.tabs([t('tab_issues'), t('tab_reviews'), t('tab_milestones')])

    with tab1:
        if issues:
            df = pd.DataFrame(issues)
            cluster_label_map = {c['id']: c['label'] for c in clusters}
            df['cluster_label'] = df['cluster_id'].map(cluster_label_map)
            st.dataframe(
                df[['number', 'title', 'state', 'milestone_title', 'cluster_label', 'reactions_plus1', 'html_url']],
                width="stretch",
            )

    with tab2:
        if reviews:
            df = pd.DataFrame(reviews)
            cluster_label_map = {c['id']: c['label'] for c in clusters}
            df['cluster_label'] = df['cluster_id'].map(cluster_label_map)
            st.dataframe(df[['id', 'star', 'review_date', 'cluster_label', 'review_text']], width="stretch")

    with tab3:
        if milestones:
            st.dataframe(pd.DataFrame(milestones), width="stretch")

    st.markdown("---")
    st.markdown(
        f'<div style="text-align:center;color:#888;padding:1rem;">{t("footer")}</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
