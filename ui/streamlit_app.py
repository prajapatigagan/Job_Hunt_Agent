import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from app.storage import application_db, db, job_db, match_db
from ui.agent_tab import show_agent_tab
from ui.jobs_tab import show_jobs_tab
from ui.setup_tabs import show_prefs_tab, show_profile_tab
from ui.styles import hero, load_css, show_flash
from ui.tracker_tab import show_tracker_tab

st.set_page_config(page_title="Job Hunt Agent", page_icon="🎯", layout="wide")
db.init_db()
load_css()


def show_sidebar(profile, prefs, jobs, matches, apps):
    with st.sidebar:
        st.markdown("### Job Hunt Agent")
        st.caption("From resume to application, in one place.")
        st.divider()

        steps = [
            ("Profile", profile is not None),
            ("Preferences", prefs is not None),
            (f"Jobs ({len(jobs)})", len(jobs) > 0),
            (f"Matched ({len(matches)})", len(matches) > 0),
            (f"Applications ({len(apps)})", len(apps) > 0),
        ]
        for name, done in steps:
            mark = "✅" if done else "⬜"
            st.write(f"{mark} {name}")

        if profile is not None:
            st.divider()
            st.caption(f"{profile.name} · {len(profile.skills)} skills · {len(profile.projects)} projects")


def show_metrics(jobs, matches, apps):
    to_apply = len([m for m in matches if m.verdict == "apply"])
    applied = len([a for a in apps if a.status in ("applied", "interview", "offer")])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jobs found", len(jobs))
    c2.metric("Matched", len(matches))
    c3.metric("Good fit", to_apply)
    c4.metric("Applied", applied)


profile = db.load_profile()
prefs = db.load_preferences()
jobs = job_db.load_jobs()
matches = match_db.load_matches()
apps = application_db.load_applications()

show_sidebar(profile, prefs, jobs, matches, apps)

hero("Job Hunt Agent", "Find jobs, match them, tailor your resume and track your applications.")
show_metrics(jobs, matches, apps)
show_flash()

tab_profile, tab_prefs, tab_jobs, tab_agent, tab_tracker = st.tabs(
    ["Resume / Profile", "Preferences", "Jobs", "Agent", "Tracker"]
)

with tab_profile:
    show_profile_tab()

with tab_prefs:
    show_prefs_tab()

with tab_jobs:
    show_jobs_tab()

with tab_agent:
    show_agent_tab()

with tab_tracker:
    show_tracker_tab()