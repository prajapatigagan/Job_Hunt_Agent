import html

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, .stApp { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1100px; }

/* hero */
.hero h1 { font-size: 2.4rem; font-weight: 700; margin: 0; background: linear-gradient(90deg, #8b85ff, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.hero p { color: #9aa3b5; margin: 4px 0 18px 0; }

/* tabs */
.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid #232a3b; }
.stTabs [data-baseweb="tab"] { height: 42px; padding: 0 16px; font-weight: 500; }

/* cards */
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 14px; border-color: #232a3b; background: #131826; }

/* metrics */
[data-testid="stMetric"] { background: #131826; border: 1px solid #232a3b; padding: 14px 16px; border-radius: 14px; }
[data-testid="stMetricLabel"] { color: #9aa3b5; }

/* buttons */
.stButton > button, .stDownloadButton > button, .stLinkButton > a { border-radius: 10px; font-weight: 500; }
.stButton > button[kind="primary"] { background: linear-gradient(90deg, #6c63ff, #38bdf8); border: none; color: white; }

/* chips */
.chip { display: inline-block; padding: 2px 10px; margin: 2px 6px 2px 0; border-radius: 999px; font-size: 12px; font-weight: 500; }
.chip-gray { background: #1f2535; color: #aab3c5; }
.chip-blue { background: #14263f; color: #7cc4ff; }
.chip-green { background: #12301f; color: #4ade80; }
.chip-amber { background: #3a2c10; color: #fbbf24; }
.chip-red { background: #3a1616; color: #f87171; }
.chip-purple { background: #25194a; color: #b9a8ff; }
.muted { color: #6b7488; font-size: 0.85rem; }

/* job card */
.job-title { font-size: 1.05rem; font-weight: 600; color: #e8eaf0; }
.job-sub { color: #9aa3b5; font-size: 0.88rem; margin-bottom: 2px; }
.score { font-size: 1.9rem; font-weight: 700; text-align: right; color: #e8eaf0; line-height: 1; }
.score small { font-size: 0.8rem; color: #6b7488; font-weight: 500; }
.bar { height: 8px; background: #232a3b; border-radius: 99px; overflow: hidden; margin: 6px 0 10px 0; }
.bar > div { height: 100%; border-radius: 99px; }
.section-title { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em; color: #8b95ab; font-weight: 600; margin: 16px 0 8px 0; }

/* agent stepper */
.stepper { display: flex; gap: 8px; flex-wrap: wrap; margin: 6px 0 14px 0; }
.step { display: flex; align-items: center; gap: 8px; padding: 8px 14px; border-radius: 999px; background: #131826; border: 1px solid #232a3b; color: #6b7488; font-size: 0.88rem; }
.step span { width: 22px; height: 22px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; background: #1f2535; font-size: 0.75rem; }
.step.done { color: #4ade80; border-color: #1c4a2e; }
.step.done span { background: #12301f; }
.step.active { color: #e8eaf0; border-color: #6c63ff; }
.step.active span { background: #6c63ff; color: white; }
</style>
"""

VERDICT_KIND = {"apply": "green", "maybe": "amber", "skip": "gray"}

STATUS_KIND = {
    "shortlisted": "gray",
    "drafted": "blue",
    "approved": "purple",
    "applied": "green",
    "interview": "amber",
    "offer": "green",
    "rejected": "red",
    "withdrawn": "gray",
}


def load_css():
    st.markdown(CSS, unsafe_allow_html=True)


def chip(text, kind="gray"):
    return f'<span class="chip chip-{kind}">{html.escape(str(text))}</span>'


def chips(items, kind="gray"):
    if not items:
        return '<span class="muted">-</span>'
    return "".join(chip(item, kind) for item in items)


def score_bar(score):
    score = max(0.0, min(100.0, float(score)))
    if score >= 70:
        color = "#22c55e"
    elif score >= 50:
        color = "#f59e0b"
    else:
        color = "#6b7280"
    return f'<div class="bar"><div style="width:{score}%;background:{color}"></div></div>'


def hero(title, subtitle):
    st.markdown(
        f'<div class="hero"><h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p></div>',
        unsafe_allow_html=True,
    )


def section(title):
    st.markdown(f'<div class="section-title">{html.escape(title)}</div>', unsafe_allow_html=True)


def stepper(steps, active):
    # active = abhi chal raha step (0 se), len(steps) = sab ho gaye, -1 = abhi shuru nahi
    parts = []
    for i, name in enumerate(steps):
        if i < active:
            cls = "done"
        elif i == active:
            cls = "active"
        else:
            cls = ""
        parts.append(f'<div class="step {cls}"><span>{i + 1}</span>{html.escape(name)}</div>')
    st.markdown('<div class="stepper">' + "".join(parts) + "</div>", unsafe_allow_html=True)


def flash(message, kind="success"):
    # rerun ke baad bhi message dikhane ke liye
    st.session_state["flash"] = (kind, message)


def show_flash():
    item = st.session_state.pop("flash", None)
    if not item:
        return
    kind, message = item
    if kind == "error":
        st.error(message)
    elif kind == "info":
        st.info(message)
    else:
        st.success(message)