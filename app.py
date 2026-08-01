import os
import json
import time
import sqlite3
import statistics

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from database import GapAnalysisDB
from github_client import GitHubClient
from reviews_source import fetch_reviews
from gap_analyzer import GapAnalyzer
from project_chat import ProjectChat, build_context
from timeline import gap_timeline, corpus_summary, month_label
from product import get_product, list_products, CURRENT
from i18n import get_text

st.set_page_config(
    page_title=f"Silent Stakeholder — {CURRENT.name}",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

VERDICT_COLORS = {
    'IGNORED': '#e11d48',
    'UNDER-PRIORITIZED': '#ea580c',
    'MISUNDERSTOOD': '#7c3aed',
    'COVERED': '#059669',
}
VERDICT_SHORT_KEYS = {
    'IGNORED': 'verdict_short_ignored',
    'UNDER-PRIORITIZED': 'verdict_short_underprioritized',
    'MISUNDERSTOOD': 'verdict_short_misunderstood',
    'COVERED': 'verdict_short_covered',
}
RULING_COLORS = {'UPHELD': '#059669', 'CONTESTED': '#d97706', 'OVERTURNED': '#e11d48'}

CSS = """
<style>
  .block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1120px; }
  html, body, [class*="css"] { font-variant-numeric: tabular-nums; }

  /* ---------- hero ---------- */
  .hero { margin-bottom: 1.6rem; }
  .hero-eyebrow {
    display: inline-block; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.14em;
    text-transform: uppercase; padding: 0.25rem 0.65rem; border-radius: 6px;
    background: linear-gradient(135deg, rgba(124,58,237,0.16), rgba(37,99,235,0.16));
    border: 1px solid rgba(124,58,237,0.28); margin-bottom: 0.85rem;
  }
  .hero-title {
    font-size: 2.7rem; font-weight: 760; letter-spacing: -0.035em;
    line-height: 1.06; margin-bottom: 0.6rem;
  }
  .hero-title .accent {
    background: linear-gradient(100deg, #7c3aed, #2563eb 60%, #0891b2);
    -webkit-background-clip: text; background-clip: text; color: transparent;
  }
  .hero-sub {
    font-size: 1.03rem; line-height: 1.55; max-width: 46rem;
    color: rgba(140,140,150,0.98); margin-bottom: 0.9rem;
  }
  .hero-meta { display: flex; flex-wrap: wrap; gap: 1.2rem; font-size: 0.8rem; }
  .hero-meta-item { color: rgba(140,140,150,0.85); }
  .hero-meta-item b { color: rgba(160,160,170,1); font-weight: 650; }

  /* ---------- summary strip ---------- */
  .strip { display: flex; flex-wrap: wrap; gap: 0.6rem; margin: 0.4rem 0 0.2rem 0; }
  .stat {
    flex: 1 1 150px; padding: 0.75rem 0.9rem; border-radius: 11px;
    border: 1px solid rgba(128,128,128,0.18); background: rgba(128,128,128,0.045);
  }
  .stat-val { font-size: 1.5rem; font-weight: 720; line-height: 1.1; letter-spacing: -0.02em; }
  .stat-key {
    font-size: 0.68rem; letter-spacing: 0.09em; text-transform: uppercase;
    color: rgba(140,140,150,0.9); margin-top: 0.2rem; font-weight: 600;
  }

  /* ---------- gap card ---------- */
  .gap-head { display: flex; align-items: flex-start; gap: 0.75rem; }
  .rank {
    flex: 0 0 auto; width: 27px; height: 27px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 750; font-size: 0.85rem; margin-top: 0.12rem;
    background: rgba(128,128,128,0.13); border: 1px solid rgba(128,128,128,0.16);
  }
  .need { font-size: 1.15rem; font-weight: 640; line-height: 1.4; letter-spacing: -0.011em; }

  .pill {
    display: inline-block; padding: 0.22rem 0.6rem; border-radius: 999px;
    font-size: 0.66rem; font-weight: 750; letter-spacing: 0.05em; white-space: nowrap;
    border: 1px solid transparent;
  }
  .pill-outline { background: transparent; }

  .conf { margin: 1rem 0 0.7rem 0; }
  .conf-top {
    display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 0.35rem;
  }
  .conf-key {
    font-size: 0.66rem; letter-spacing: 0.1em; text-transform: uppercase;
    color: rgba(140,140,150,0.9); font-weight: 650;
  }
  .conf-val { font-size: 1.45rem; font-weight: 740; letter-spacing: -0.025em; }
  .conf-track { height: 6px; border-radius: 999px; background: rgba(128,128,128,0.15); overflow: hidden; }
  .conf-fill { height: 100%; border-radius: 999px; }

  .chips { display: flex; flex-wrap: wrap; gap: 0.4rem; }
  .chip {
    padding: 0.26rem 0.62rem; border-radius: 8px; font-size: 0.78rem;
    background: rgba(128,128,128,0.075); border: 1px solid rgba(128,128,128,0.15);
  }
  .chip .k { color: rgba(140,140,150,0.9); }
  .chip .v { font-weight: 680; margin-left: 0.15rem; }
  .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.95em; }

  /* ---------- response-latency timeline ---------- */
  .tl {
    display: flex; align-items: stretch; gap: 0.6rem; margin: 0.95rem 0 0.2rem 0;
    padding: 0.7rem 0.85rem; border-radius: 10px;
    background: rgba(128,128,128,0.045); border: 1px solid rgba(128,128,128,0.14);
  }
  .tl-node { flex: 0 0 auto; max-width: 34%; }
  .tl-node.right { text-align: right; }
  .tl-when { font-size: 0.78rem; font-weight: 680; line-height: 1.3; }
  .tl-what { font-size: 0.72rem; color: rgba(140,140,150,0.92); line-height: 1.35; margin-top: 0.1rem; }
  .tl-mid { flex: 1 1 auto; display: flex; flex-direction: column; justify-content: center; min-width: 0; }
  .tl-track { position: relative; height: 2px; margin: 0.35rem 0; }
  .tl-dot {
    position: absolute; top: -3px; width: 8px; height: 8px; border-radius: 50%;
  }
  .tl-dot.l { left: 0; } .tl-dot.r { right: 0; }
  .tl-latency {
    text-align: center; font-size: 0.75rem; font-weight: 720; letter-spacing: 0.01em;
  }
  .tl-latency-sub {
    text-align: center; font-size: 0.68rem; color: rgba(140,140,150,0.85); margin-top: 0.05rem;
  }

  /* ---------- evidence ---------- */
  .quote {
    position: relative; padding: 0.55rem 0 0.55rem 0.85rem; margin: 0.5rem 0;
    border-left: 2px solid rgba(128,128,128,0.3); font-size: 0.895rem; line-height: 1.5;
  }
  .quote-meta {
    display: flex; align-items: center; gap: 0.5rem;
    font-size: 0.72rem; color: rgba(140,140,150,0.9); margin-bottom: 0.2rem;
  }
  .rid {
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    background: rgba(128,128,128,0.13); padding: 0.05rem 0.35rem; border-radius: 4px;
  }
  .comp-row {
    display: flex; justify-content: space-between; align-items: baseline;
    padding: 0.45rem 0; border-bottom: 1px dashed rgba(128,128,128,0.16);
  }
  .comp-name { font-size: 0.87rem; font-weight: 620; }
  .comp-hint { font-size: 0.75rem; color: rgba(140,140,150,0.88); line-height: 1.4; }
  .comp-val { font-size: 1rem; font-weight: 720; }

  /* ---------- sections ---------- */
  .sec-title {
    font-size: 1.5rem; font-weight: 720; letter-spacing: -0.02em; margin-bottom: 0.2rem;
  }
  .sec-sub {
    color: rgba(140,140,150,0.95); font-size: 0.9rem; line-height: 1.5;
    margin-bottom: 1.1rem; max-width: 46rem;
  }

  /* ---------- panel / debate ---------- */
  .speaker { display: flex; align-items: center; gap: 0.55rem; margin-bottom: 0.4rem; }
  .speaker-emoji {
    width: 30px; height: 30px; border-radius: 9px; display: flex;
    align-items: center; justify-content: center; font-size: 1rem;
    background: rgba(128,128,128,0.12); border: 1px solid rgba(128,128,128,0.17);
  }
  .speaker-name { font-weight: 680; font-size: 0.93rem; }
  .speaker-role { font-size: 0.72rem; color: rgba(140,140,150,0.9); }
  .roster { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem; }
  .roster-item {
    display: flex; align-items: center; gap: 0.45rem; padding: 0.4rem 0.7rem;
    border-radius: 9px; background: rgba(128,128,128,0.06);
    border: 1px solid rgba(128,128,128,0.15); font-size: 0.83rem;
  }
  .headline {
    font-size: 1.02rem; line-height: 1.55; font-weight: 560;
    padding: 0.9rem 1.1rem; border-radius: 11px;
    background: linear-gradient(135deg, rgba(124,58,237,0.09), rgba(37,99,235,0.06));
    border: 1px solid rgba(124,58,237,0.22);
  }
  .footer-note {
    text-align: center; color: rgba(140,140,150,0.65);
    font-size: 0.8rem; padding: 2rem 0 0.5rem 0;
  }
  .stale {
    font-size: 0.83rem; padding: 0.6rem 0.85rem; border-radius: 9px;
    background: rgba(234,88,12,0.09); border: 1px solid rgba(234,88,12,0.3);
  }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_resource
def get_db(db_path: str):
    return GapAnalysisDB(db_path)


def stored_gap_count(db_path: str) -> int:
    """How many results a product already has. Opened read-only so that merely
    browsing the product list never creates an empty database."""
    if not os.path.exists(db_path):
        return 0
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            return con.execute("SELECT COUNT(*) FROM gaps").fetchone()[0]
        finally:
            con.close()
    except sqlite3.Error:
        return 0


def t(key: str, **kwargs) -> str:
    return get_text(st.session_state.get('lang', 'en'), key, **kwargs)


def agent_label(agent_key: str, fallback: str) -> str:
    """Panel role names are stored in English in the transcript; show them translated."""
    translated = t(f'agent_{agent_key}')
    return fallback if translated == f'agent_{agent_key}' else translated


def localise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Raw-data tables ship database column names; give them readable headers."""
    return df.rename(columns={c: t(f'col_{c}') for c in df.columns
                              if t(f'col_{c}') != f'col_{c}'})


def conf_gradient(c: float) -> str:
    if c >= 70:
        return "linear-gradient(90deg,#7c3aed,#2563eb)"
    if c >= 55:
        return "linear-gradient(90deg,#2563eb,#0891b2)"
    return "linear-gradient(90deg,#64748b,#0891b2)"


def pill(text: str, color: str, outline: bool = False) -> str:
    if outline:
        return (f'<span class="pill pill-outline" style="color:{color};border-color:{color}66">'
                f'{text}</span>')
    return f'<span class="pill" style="background:{color};color:#fff">{text}</span>'


def load_debate(path: str):
    for candidate in (path, 'debate_result.json'):
        if candidate and os.path.exists(candidate):
            try:
                with open(candidate, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                continue
    return None


def run_pipeline(product):
    """Full analysis. Large repos take minutes, so every stage reports as it goes."""
    db = get_db(product.db_path)
    started = time.time()

    def elapsed():
        secs = int(time.time() - started)
        return f"{secs // 60}m {secs % 60}s" if secs >= 60 else f"{secs}s"

    with st.status(t('run_status_title', product=product.name), expanded=True) as status:
        bar = st.progress(0.0)
        line = st.empty()

        def say(msg, frac):
            line.markdown(f"**{msg}**  \n<span style='color:rgba(140,140,150,0.9);"
                          f"font-size:0.8rem'>{t('run_elapsed', time=elapsed())}</span>",
                          unsafe_allow_html=True)
            bar.progress(min(max(frac, 0.0), 1.0))

        try:
            say(t('run_github', repo=product.repo), 0.02)
            gh = GitHubClient(product.repo)
            milestones = gh.fetch_milestones()
            say(t('run_github_milestones', n=len(milestones), repo=product.repo), 0.04)

            # Big repos page slowly - show the count climbing so it never looks frozen.
            def on_page(count):
                say(t('run_github_paging', n=count, repo=product.repo),
                    0.04 + 0.26 * min(count / 10000, 1.0))

            issues = gh.fetch_issues(on_page=on_page)
            say(t('run_github_done', n=len(issues)), 0.32)

            say(t('run_reviews', package=product.package_name), 0.34)
            reviews = fetch_reviews(product.package_name)
            if not reviews:
                status.update(label=t('run_no_reviews', package=product.package_name),
                              state="error")
                return
            say(t('run_reviews_done', n=len(reviews)), 0.40)

            say(t('run_saving_sources'), 0.42)
            db.replace_milestones(milestones)
            db.replace_issues(issues)
            db.replace_reviews(reviews)
            reviews = db.get_reviews()

            # Clustering + per-area LLM mining is the long tail; map it onto 45-92%.
            stage = {'i': 0}

            def analysis_progress(msg):
                stage['i'] += 1
                say(msg, 0.45 + 0.47 * min(stage['i'] / 20, 1.0))

            ga = GapAnalyzer(product=product)
            result = ga.run(issues, reviews, top_n=5, progress=analysis_progress)

            say(t('run_saving_results'), 0.95)
            db.replace_clusters(list(result['clusters'].values()))
            db.set_issue_clusters({issues[i]['number']: int(result['issue_clusters'][i])
                                   for i in range(len(issues))})
            db.set_review_clusters({reviews[i]['id']: int(result['review_clusters'][i])
                                    for i in range(len(reviews))})
            db.replace_gaps(result['gaps'])
            db.replace_candidates(result['all_candidates'],
                                  {g['need_text'] for g in result['gaps']})

            say(t('run_done', n=len(result['gaps'])), 1.0)
            status.update(label=t('run_status_done', product=product.name, time=elapsed()),
                          state="complete", expanded=False)
        except Exception as e:
            status.update(label=t('run_status_failed', error=str(e)[:160]), state="error")
            st.exception(e)
            return

    st.success(t('run_success', n=len(result['gaps']), product=product.name, time=elapsed()))
    # Any button press reruns the script, which redraws the page against the new results.
    st.button(t('run_show_results'), type="primary")


# ------------------------------------------------------------------ hero
def render_hero(issues, reviews, gaps, candidates, ruling, latency, product):
    st.markdown(
        f'<div class="hero">'
        f'  <div class="hero-eyebrow">{t("hero_eyebrow")}</div>'
        f'  <div class="hero-title">{t("hero_title_a")}<span class="accent">{t("hero_title_b")}</span></div>'
        f'  <div class="hero-sub">{t("hero_sub")}</div>'
        f'  <div class="hero-meta">'
        f'    <span class="hero-meta-item">{t("hero_product")} <b>{product.name}</b></span>'
        f'    <span class="hero-meta-item">{t("hero_roadmap")} '
        f'      <a href="{product.repo_url}" style="color:inherit"><b>{product.repo}</b></a> '
        f'      · <b>{len(issues)}</b> issues</span>'
        f'    <span class="hero-meta-item">{t("hero_signals")} <b>{len(reviews)}</b> {t("hero_reviews_word")}</span>'
        f'    <span class="hero-meta-item">{t("hero_considered")} <b>{len(candidates)}</b> {t("hero_candidates_word")}</span>'
        f'  </div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    cited = len({rid for g in gaps for rid in g.get('evidence_review_ids', [])})
    verdicts = [g['verdict'] for g in gaps]
    mix = " · ".join(f"{v.split('-')[0][:3].title()} {verdicts.count(v)}" for v in dict.fromkeys(verdicts))
    upheld = sum(1 for pg in (ruling or {}).get('per_gap', []) if pg.get('ruling') == 'UPHELD')

    stats = [
        (f"{len(gaps)}", t('stat_needs')),
        (f"{cited}", t('stat_cited')),
        (mix or "—", t('stat_verdicts')),
    ]
    if latency:
        if latency['never_count']:
            stats.append((f"{latency['never_count']}/{len(gaps)}", t('stat_never')))
        if latency['worst_latency_label']:
            stats.append((latency['worst_latency_label'], t('stat_worst_latency')))
    if ruling and ruling.get('per_gap'):
        stats.append((f"{upheld}/{len(ruling['per_gap'])}", t('stat_upheld')))

    st.markdown(
        '<div class="strip">' + "".join(
            f'<div class="stat"><div class="stat-val">{v}</div><div class="stat-key">{k}</div></div>'
            for v, k in stats
        ) + '</div>',
        unsafe_allow_html=True,
    )


def render_timeline(tl: dict):
    """When users voiced the need vs when (or whether) the roadmap answered."""
    never = tl['status'] == 'never'
    left_when = f"{month_label(tl['first_signal'])} – {month_label(tl['last_signal'])}"
    left_what = t('tl_users_voiced', n=tl['n_signals'])

    if never:
        line_color, dot_r = '#e11d48', '#e11d48'
        track = (f'<div style="border-top:2px dashed {line_color}55;height:0"></div>')
        latency = t('tl_never')
        latency_sub = (t('tl_closest_only', number=tl['closest_number'],
                         sim=f"{tl['closest_similarity']:.2f}", when=month_label(tl['closest_created']))
                       if tl['closest_number'] else '')
        right_when = t('tl_no_ticket')
        right_what = ''
    else:
        status_color = {'open': '#ea580c', 'resolved': '#059669', 'declined': '#e11d48'}
        dot_r = status_color.get(tl['status'], '#6b7280')
        line_color = '#ea580c' if (tl['latency_days'] or 0) > 365 else '#0891b2'
        track = (f'<div style="border-top:2px solid {line_color}55;height:0"></div>')
        latency = tl['latency_label'] or '—'
        latency_sub = t('tl_roadmap_silent')
        right_when = month_label(tl['issue_created'])
        if tl['status'] == 'open':
            right_what = t('tl_opened_still_open', number=tl['issue_number'])
        elif tl['status'] == 'declined':
            right_what = t('tl_declined', number=tl['issue_number'])
        else:
            right_what = t('tl_resolved_in', number=tl['issue_number'], span=tl['resolution_label'] or '—')

    st.markdown(
        f'<div class="tl">'
        f'  <div class="tl-node">'
        f'    <div class="tl-when">{left_when}</div><div class="tl-what">{left_what}</div>'
        f'  </div>'
        f'  <div class="tl-mid">'
        f'    <div class="tl-latency" style="color:{line_color}">{latency}</div>'
        f'    <div class="tl-track">'
        f'      <div class="tl-dot l" style="background:#0891b2"></div>{track}'
        f'      <div class="tl-dot r" style="background:{dot_r}"></div>'
        f'    </div>'
        f'    <div class="tl-latency-sub">{latency_sub}</div>'
        f'  </div>'
        f'  <div class="tl-node right">'
        f'    <div class="tl-when">{right_when}</div><div class="tl-what">{right_what}</div>'
        f'  </div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------ gap card
def render_gap_card(rank, gap, reviews_by_id, issues_by_number, total_reviews, gap_ruling, tl):
    color = VERDICT_COLORS.get(gap['verdict'], '#6b7280')
    conf = gap['confidence']
    ev = [reviews_by_id[i] for i in gap.get('evidence_review_ids', []) if i in reviews_by_id]
    stars = [r['star'] for r in ev if r.get('star') is not None]

    with st.container(border=True):
        head, right = st.columns([6.2, 2], vertical_alignment="top")
        with head:
            st.markdown(
                f'<div class="gap-head"><div class="rank">{rank}</div>'
                f'<div class="need">{gap["need_text"]}</div></div>',
                unsafe_allow_html=True,
            )
        with right:
            badges = pill(t(VERDICT_SHORT_KEYS.get(gap['verdict'], 'verdict_short_ignored')), color)
            if gap_ruling and gap_ruling.get('ruling'):
                rc = RULING_COLORS.get(gap_ruling['ruling'], '#6b7280')
                badges += " " + pill(t('ruling_' + str(gap_ruling['ruling']).lower()), rc, outline=True)
            st.markdown(f'<div style="text-align:right">{badges}</div>', unsafe_allow_html=True)

        st.markdown(
            f'<div class="conf">'
            f'<div class="conf-top"><span class="conf-key">{t("confidence_label")}</span>'
            f'<span class="conf-val">{conf:.0f}<span style="font-size:0.9rem;opacity:0.6">%</span></span></div>'
            f'<div class="conf-track"><div class="conf-fill" '
            f'style="width:{conf:.0f}%;background:{conf_gradient(conf)}"></div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        share = 100.0 * len(ev) / total_reviews if total_reviews else 0
        chips = [
            f'<span class="chip"><span class="k">{t("chip_users")}</span><span class="v">{len(ev)}</span></span>',
            f'<span class="chip"><span class="k">{t("chip_share")}</span><span class="v">{share:.1f}%</span></span>',
        ]
        if stars:
            chips.append(f'<span class="chip"><span class="k">{t("chip_avg_rating")}</span>'
                         f'<span class="v">{statistics.mean(stars):.1f}★</span></span>')
        if gap.get('matched_issue_number'):
            chips.append(f'<span class="chip"><span class="k">{t("chip_roadmap")}</span>'
                         f'<span class="v mono">#{gap["matched_issue_number"]}</span></span>')
        else:
            chips.append(f'<span class="chip"><span class="k">{t("chip_roadmap")}</span>'
                         f'<span class="v">{t("chip_no_issue")}</span></span>')
        st.markdown(f'<div class="chips">{"".join(chips)}</div>', unsafe_allow_html=True)

        render_timeline(tl)

        if gap_ruling and gap_ruling.get('note'):
            st.caption(f"⚖️ {gap_ruling['note']}")

        st.write("")
        c1, c2 = st.columns(2)

        with c1:
            with st.expander(t('evidence_trace', n=len(ev))):
                for r in ev:
                    st.markdown(
                        f'<div class="quote"><div class="quote-meta">'
                        f'<span class="rid">{r["id"]}</span><span>{"★" * int(r.get("star") or 0)}</span>'
                        f'</div>{r["review_text"]}</div>',
                        unsafe_allow_html=True,
                    )

        with c2:
            with st.expander(t('why_this_score')):
                comp = gap.get('confidence_components', {})
                rows = [
                    (t('evidence_volume'), comp.get('evidence_count_norm', 0), t('evidence_volume_help')),
                    (t('rating_spread'), comp.get('rating_spread', 0), t('rating_spread_help')),
                    (t('consistency'), comp.get('cross_signal_consistency', 0), t('consistency_help')),
                    (t('gap_certainty'),
                     comp.get('effective_gap_certainty', comp.get('roadmap_gap_certainty', 0)),
                     t('gap_certainty_help')),
                ]
                st.markdown("".join(
                    f'<div class="comp-row"><div><div class="comp-name">{n}</div>'
                    f'<div class="comp-hint">{h}</div></div>'
                    f'<div class="comp-val">{v:.2f}</div></div>'
                    for n, v, h in rows
                ), unsafe_allow_html=True)

                st.write("")
                reasoning = gap.get('reasoning', '')
                if '| Roadmap check:' in reasoning:
                    a, b = reasoning.split('| Roadmap check:', 1)
                    st.markdown(f"**{t('why_latent')}** {a.strip()}")
                    st.markdown(f"**{t('roadmap_check')}** {b.strip()}")
                elif reasoning:
                    st.markdown(reasoning)

                if not gap.get('matched_issue_number'):
                    cl = issues_by_number.get(gap.get('closest_issue_number'))
                    sim = gap.get('closest_issue_similarity')
                    if cl:
                        st.caption(t('closest_below_threshold', number=cl['number'], title=cl['title'],
                                     url=cl['html_url'], sim=f"{sim:.2f}" if sim is not None else "?"))

        if gap.get('matched_issue_number'):
            iss = issues_by_number.get(gap['matched_issue_number'])
            if iss:
                st.caption(t('closest_issue', number=iss['number'], title=iss['title'],
                             url=iss['html_url'], state=iss['state'],
                             milestone=iss.get('milestone_title') or t('none_milestone')))


# ------------------------------------------------------------------ chat
def render_chat(gaps, candidates, reviews, issues, clusters):
    st.markdown(f'<div class="sec-title">{t("chat_header")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sec-sub">{t("chat_caption")}</div>', unsafe_allow_html=True)

    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []

    if not st.session_state['chat_history']:
        cols = st.columns(3)
        for col, q in zip(cols, [t('chat_q1'), t('chat_q2'), t('chat_q3')]):
            if col.button(q, width="stretch", key=f"sg_{q[:24]}"):
                st.session_state['pending_question'] = q
                st.rerun()

    for turn in st.session_state['chat_history']:
        with st.chat_message(turn['role']):
            st.markdown(turn['content'])

    question = st.chat_input(t('chat_placeholder'))
    if 'pending_question' in st.session_state:
        question = st.session_state.pop('pending_question')

    if question:
        st.session_state['chat_history'].append({'role': 'user', 'content': question})
        with st.chat_message('user'):
            st.markdown(question)
        with st.chat_message('assistant'):
            with st.spinner(t('chat_thinking')):
                try:
                    ctx = build_context(gaps, candidates, reviews, issues, clusters)
                    answer = ProjectChat().ask(question, ctx, st.session_state['chat_history'][:-1])
                except Exception as e:
                    answer = t('chat_error', error=str(e))
                st.markdown(answer)
        st.session_state['chat_history'].append({'role': 'assistant', 'content': answer})

    if st.session_state['chat_history'] and st.button(t('chat_clear')):
        st.session_state['chat_history'] = []
        st.rerun()


# ------------------------------------------------------------------ panel
def render_panel(debate, gaps):
    if not debate:
        st.info(t('panel_none'))
        return

    if 'transcript' not in debate:
        st.markdown(f'<div class="stale">{t("panel_stale")}</div>', unsafe_allow_html=True)
        return

    panel = debate.get('panel', {})
    roster = "".join(
        f'<div class="roster-item"><span>{v["emoji"]}</span>'
        f'<span>{agent_label(key, v["label"])}</span></div>'
        for key, v in panel.items()
    ) + (f'<div class="roster-item"><span>⚖️</span>'
         f'<span>{agent_label("judge", "Judge")}</span></div>')
    st.markdown(f'<div class="roster">{roster}</div>', unsafe_allow_html=True)

    r = debate.get('rulings', {})
    if r.get('headline'):
        st.markdown(f'<div class="headline">⚖️ {r["headline"]}</div>', unsafe_allow_html=True)
        st.write("")

    per_gap = r.get('per_gap', [])
    if per_gap:
        cols = st.columns(len(per_gap))
        for col, pg in zip(cols, per_gap):
            rank = pg.get('rank')
            rc = RULING_COLORS.get(pg.get('ruling'), '#6b7280')
            ruling_pill = pill(t('ruling_' + str(pg.get('ruling', '')).lower()), rc, outline=True)
            with col:
                st.markdown(
                    f'<div style="text-align:center">'
                    f'<div style="font-size:0.72rem;color:rgba(140,140,150,0.9);margin-bottom:0.3rem">'
                    f'{t("panel_gap_n", n=rank)}</div>'
                    f'{ruling_pill}</div>',
                    unsafe_allow_html=True,
                )
        st.write("")

    a, b = st.columns(2)
    with a:
        if r.get('must_prepare_for'):
            st.markdown(f"**{t('panel_must_prepare')}**")
            for m in r['must_prepare_for']:
                st.markdown(f"- {m}")
    with b:
        if r.get('disputes'):
            st.markdown(f"**{t('panel_disputes')}**")
            for d in r['disputes']:
                st.markdown(f"- {d}")

    st.write("")
    st.markdown(f"**{t('panel_transcript')}**")
    rounds = {}
    for e in debate['transcript']:
        rounds.setdefault(e['round'], []).append(e)

    phase_names = {1: t('phase_opening'), 2: t('phase_cross'), 3: t('phase_interrogation'),
                   4: t('phase_rebuttal'), 5: t('phase_ruling')}
    for rnd in sorted(rounds):
        with st.expander(f"{t('round_n', n=rnd)} — {phase_names.get(rnd, '')}"):
            for e in rounds[rnd]:
                st.markdown(
                    f'<div class="speaker"><div class="speaker-emoji">{e["emoji"]}</div>'
                    f'<div><div class="speaker-name">{agent_label(e["agent"], e["label"])}</div>'
                    f'<div class="speaker-role">{phase_names.get(e["round"], "")}</div></div></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(e['statement'])
                st.divider()


# ------------------------------------------------------------------ analyst
def render_candidates_table(candidates):
    rows = [{
        t('candidates_col_top5'): '★' if c['in_top5'] else '',
        t('candidates_col_need'): c['need_text'],
        t('candidates_col_verdict'): c['verdict'],
        t('candidates_col_confidence'): c['confidence'],
        t('candidates_col_evidence_count'): len(c['evidence_review_ids']),
        t('candidates_col_matched_issue'): f"#{c['matched_issue_number']}" if c.get('matched_issue_number') else '—',
    } for c in candidates]
    st.dataframe(
        pd.DataFrame(rows), width="stretch", hide_index=True,
        column_config={t('candidates_col_confidence'): st.column_config.ProgressColumn(
            t('candidates_col_confidence'), format="%.1f%%", min_value=0, max_value=100)},
    )


def render_cluster_chart(clusters):
    if not clusters:
        return
    df = pd.DataFrame(clusters).sort_values('review_count', ascending=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(y=df['label'], x=df['issue_count'], name=t('chart_issues'),
                         orientation='h', marker_color='#2563eb'))
    fig.add_trace(go.Bar(y=df['label'], x=df['review_count'], name=t('chart_reviews'),
                         orientation='h', marker_color='#059669'))
    fig.update_layout(
        barmode='group', height=max(320, 34 * len(df)), xaxis_title=t('chart_count_axis'),
        margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation='h', yanchor='bottom', y=1.02),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
    )
    st.plotly_chart(fig, width="stretch")


def render_analyst(issues, reviews, milestones, clusters, candidates, debate, gaps):
    tabs = st.tabs([t('adv_tab_candidates'), t('adv_tab_debate'),
                    t('adv_tab_clusters'), t('adv_tab_raw')])
    with tabs[0]:
        st.caption(t('candidates_caption'))
        render_candidates_table(candidates)
    with tabs[1]:
        st.caption(t('debate_caption'))
        render_panel(debate, gaps)
    with tabs[2]:
        st.caption(t('clusters_caption'))
        render_cluster_chart(clusters)
    with tabs[3]:
        sub = st.tabs([t('tab_issues'), t('tab_reviews'), t('tab_milestones')])
        lbl = {c['id']: c['label'] for c in clusters}
        with sub[0]:
            if issues:
                df = pd.DataFrame(issues)
                df['cluster'] = df['cluster_id'].map(lbl)
                st.dataframe(
                    localise_columns(df[['number', 'title', 'state', 'milestone_title',
                                         'cluster', 'reactions_plus1', 'html_url']]),
                    width="stretch", hide_index=True)
        with sub[1]:
            if reviews:
                df = pd.DataFrame(reviews)
                df['cluster'] = df['cluster_id'].map(lbl)
                st.dataframe(
                    localise_columns(df[['id', 'star', 'review_date', 'cluster', 'review_text']]),
                    width="stretch", hide_index=True)
        with sub[2]:
            if milestones:
                st.dataframe(localise_columns(pd.DataFrame(milestones)),
                             width="stretch", hide_index=True)


# ------------------------------------------------------------------ main
def main():
    if 'lang' not in st.session_state:
        st.session_state['lang'] = 'en'

    with st.sidebar:
        opts = {'English': 'en', 'Русский': 'ru'}
        cur = 'English' if st.session_state['lang'] == 'en' else 'Русский'
        st.session_state['lang'] = opts[st.selectbox(
            t('language_label'), list(opts), index=list(opts).index(cur))]

        st.divider()
        catalogue = list_products()
        if catalogue:
            names = [p.name for p in catalogue]
            default_idx = next((i for i, p in enumerate(catalogue)
                                if p.package_name == CURRENT.package_name), 0)
            chosen_name = st.selectbox(t('product_label'), names, index=default_idx,
                                       help=t('product_help'))
            product = next(p for p in catalogue if p.name == chosen_name)
        else:
            product = CURRENT
        n_stored = stored_gap_count(product.db_path)
        st.caption(
            f"{t('sidebar_roadmap')} `{product.repo}`  \n"
            f"{t('sidebar_signals')} `{product.source_id}`  \n"
            + (t('product_ready', n=n_stored) if n_stored else t('product_not_analysed'))
        )

        st.divider()
        analyst = st.toggle(t('advanced_mode'), value=False, help=t('advanced_mode_help'))
        st.divider()
        st.caption(t('sidebar_caption'))
        if st.button(t('run_button'), width="stretch"):
            run_pipeline(product)

    db = get_db(product.db_path)
    issues, reviews = db.get_issues(), db.get_reviews()
    milestones, clusters = db.get_milestones(), db.get_clusters()
    gaps, candidates = db.get_gaps(), db.get_candidates()
    debate = load_debate(product.debate_path)
    ruling = (debate or {}).get('rulings', {})
    ruling_by_rank = {pg.get('rank'): pg for pg in ruling.get('per_gap', [])}

    reviews_by_id = {r['id']: r for r in reviews}
    issues_by_number = {i['number']: i for i in issues}
    latency = corpus_summary(gaps, reviews_by_id, issues_by_number) if gaps else None

    render_hero(issues, reviews, gaps, candidates, ruling, latency, product)

    if not gaps:
        st.info(t('no_analysis_yet'))
        return

    st.write("")
    st.markdown(f'<div class="sec-title">{t("top_needs_header")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sec-sub">{t("top_needs_caption")}</div>', unsafe_allow_html=True)

    for i, gap in enumerate(gaps, 1):
        render_gap_card(i, gap, reviews_by_id, issues_by_number, len(reviews),
                        ruling_by_rank.get(i), latency['timelines'][i - 1])

    st.write("")
    st.divider()
    render_chat(gaps, candidates, reviews, issues, clusters)

    if analyst:
        st.divider()
        st.markdown(f'<div class="sec-title">{t("adv_header")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sec-sub">{t("adv_caption")}</div>', unsafe_allow_html=True)
        render_analyst(issues, reviews, milestones, clusters, candidates, debate, gaps)

    st.markdown(f'<div class="footer-note">{t("footer")}</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
