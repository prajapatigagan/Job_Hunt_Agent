import html

import streamlit as st

from app.storage import db, job_db, match_db
from app.agent.tools.job_finder import find_jobs, JobSearchError
from app.llm import LLMError
from app.rag.matcher import match_jobs
from ui.styles import VERDICT_KIND, chip, chips, flash, score_bar, section
from ui.tailor_view import show_tailor_section


def show_match_card(m, job, profile):
    with st.container(border=True):
        left, right = st.columns([5, 1])
        with left:
            st.markdown(
                f'<div class="job-title">{html.escape(job.title)}</div>'
                f'<div class="job-sub">{html.escape(job.company)} · {html.escape(job.location or "-")}</div>',
                unsafe_allow_html=True,
            )
        with right:
            st.markdown(f'<div class="score">{m.final_score:.0f}<small>/100</small></div>', unsafe_allow_html=True)

        st.markdown(
            score_bar(m.final_score) + chip(m.verdict, VERDICT_KIND.get(m.verdict, "gray")),
            unsafe_allow_html=True,
        )

        with st.expander("Details"):
            llm_text = "-" if m.llm_score is None else f"{m.llm_score:.0f}"
            st.caption(
                f"LLM {llm_text} · Embedding {m.semantic_score:.0f} · Must-have skills {m.preference_score:.0f}"
            )
            section("Matched skills")
            st.markdown(chips(m.matched_skills, "green"), unsafe_allow_html=True)
            section("Missing skills")
            st.markdown(chips(m.missing_skills, "red"), unsafe_allow_html=True)
            section("Why")
            st.write(m.reason)

            if job.url:
                st.link_button("Open apply link", job.url)

            if profile is not None:
                show_tailor_section(profile, job, m)


def show_jobs_tab():
    prefs = db.load_preferences()
    profile = db.load_profile()

    if prefs is None:
        st.warning("Save your roles and cities in the Preferences tab first.")
        return

    top = st.columns([3, 1, 1])
    with top[0]:
        st.markdown(
            '<span class="muted">Roles</span> ' + chips(prefs.target_roles, "blue")
            + '<br><span class="muted">Cities</span> ' + chips(prefs.cities, "purple"),
            unsafe_allow_html=True,
        )
    with top[1]:
        find_clicked = st.button("Find jobs")
    with top[2]:
        match_clicked = st.button("Match jobs", type="primary")

    saved = job_db.load_jobs()

    # ---------- find jobs ----------
    if find_clicked:
        with st.spinner("Searching for jobs..."):
            try:
                found = find_jobs(prefs)
                new_count = job_db.save_jobs(found)
                flash(f"{len(found)} jobs found, {new_count} new saved.")
            except JobSearchError as e:
                flash(str(e), "error")
        st.rerun()

    # ---------- matching ----------
    if match_clicked:
        if profile is None:
            flash("Save your profile in the Resume / Profile tab first.", "error")
        elif not saved:
            flash("Run Find jobs first.", "error")
        else:
            progress = st.progress(0.0, text="Matching...")

            def update(done, total):
                progress.progress(done / total, text=f"{done}/{total} jobs scored")

            try:
                results = match_jobs(profile, prefs, saved, update)
                match_db.save_matches(results)
                flash(f"{len(results)} jobs scored.")
            except LLMError as e:
                flash(str(e), "error")
        st.rerun()

    # ---------- ranked results ----------
    matches = match_db.load_matches()
    jobs_by_id = {job.id: job for job in saved}

    section(f"Ranked matches ({len(matches)})")
    if not matches:
        st.info("No matches yet. Press Find jobs first, then Match jobs.")
    elif profile is None:
        st.info("Save your profile first to see the Tailor button.")

    for m in matches:
        job = jobs_by_id.get(m.job_id)
        if job is None:
            continue
        show_match_card(m, job, profile)

    # ---------- all saved jobs ----------
    with st.expander(f"All saved jobs ({len(saved)})"):
        for job in saved:
            st.markdown(f"**{job.title}** · {job.company} · {job.location}")
            if job.salary_min:
                st.caption(f"Salary: {int(job.salary_min):,} - {int(job.salary_max or job.salary_min):,}")
            st.caption(job.description[:300] + "...")
            if job.url:
                st.markdown(f"[Apply link]({job.url})")
            st.divider()

    if saved and st.button("Delete all jobs"):
        job_db.clear_jobs()
        match_db.clear_matches()
        flash("All jobs deleted.", "info")
        st.rerun()