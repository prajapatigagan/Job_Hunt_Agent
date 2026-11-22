import streamlit as st

from app import db, job_db, match_db
from app.job_finder import find_jobs, JobSearchError
from app.llm import LLMError
from app.matcher import match_jobs


def show_jobs_tab():
    prefs = db.load_preferences()
    profile = db.load_profile()

    if prefs is None:
        st.warning("Pehle Preferences tab me role aur city save karo.")
        return

    st.write("Roles:", ", ".join(prefs.target_roles) or "-")
    st.write("Cities:", ", ".join(prefs.cities) or "-")

    # ---------- jobs dhundhna ----------
    if st.button("Find jobs"):
        with st.spinner("Jobs dhundh raha hoon..."):
            try:
                jobs = find_jobs(prefs)
                new_count = job_db.save_jobs(jobs)
                st.success(f"{len(jobs)} jobs mili, {new_count} naye save hue.")
            except JobSearchError as e:
                st.error(str(e))

    saved = job_db.load_jobs()

    # ---------- matching ----------
    if st.button("Match jobs"):
        if profile is None:
            st.error("Pehle Resume / Profile tab me profile save karo.")
        elif not saved:
            st.error("Pehle Find jobs chalao.")
        else:
            progress = st.progress(0.0, text="Match kar raha hoon...")

            def update(done, total):
                progress.progress(done / total, text=f"{done}/{total} jobs score hue")

            try:
                results = match_jobs(profile, prefs, saved, update)
                match_db.save_matches(results)
                st.success(f"{len(results)} jobs score ho gayi.")
            except LLMError as e:
                st.error(str(e))

    # ---------- ranked results ----------
    matches = match_db.load_matches()
    jobs_by_id = {job.id: job for job in saved}

    st.subheader(f"Ranked matches ({len(matches)})")
    for m in matches:
        job = jobs_by_id.get(m.job_id)
        if job is None:
            continue

        label = f"{m.final_score:.0f}/100 [{m.verdict}] {job.title} - {job.company}"
        with st.expander(label):
            st.write(f"Location: {job.location}")
            llm_text = "-" if m.llm_score is None else f"{m.llm_score:.0f}"
            st.write(
                f"LLM: {llm_text} | Embedding: {m.semantic_score:.0f} | Must-have skills: {m.preference_score:.0f}"
            )
            st.write("Matched skills: " + (", ".join(m.matched_skills) or "-"))
            st.write("Missing skills: " + (", ".join(m.missing_skills) or "-"))
            st.write("Reason: " + m.reason)
            st.markdown(f"[Apply link]({job.url})")

    # ---------- saari saved jobs ----------
    st.subheader(f"Saari saved jobs ({len(saved)})")
    for job in saved:
        with st.expander(f"{job.title} - {job.company} ({job.location})"):
            if job.salary_min:
                st.write(f"Salary: {int(job.salary_min):,} - {int(job.salary_max or job.salary_min):,}")
            st.write(job.description[:500] + "...")
            st.markdown(f"[Apply link]({job.url})")

    if saved and st.button("Saari jobs hatao"):
        job_db.clear_jobs()
        match_db.clear_matches()
        st.rerun()