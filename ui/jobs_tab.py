import streamlit as st

from app import db, job_db
from app.job_finder import find_jobs, JobSearchError


def show_jobs_tab():
    prefs = db.load_preferences()
    if prefs is None:
        st.warning("Pehle Preferences tab me role aur city save karo.")
        return

    st.write("Roles:", ", ".join(prefs.target_roles) or "-")
    st.write("Cities:", ", ".join(prefs.cities) or "-")

    if st.button("Find jobs"):
        with st.spinner("Jobs dhundh raha hoon..."):
            try:
                jobs = find_jobs(prefs)
                new_count = job_db.save_jobs(jobs)
                st.success(f"{len(jobs)} jobs mili, {new_count} naye save hue.")
            except JobSearchError as e:
                st.error(str(e))

    saved = job_db.load_jobs()
    st.subheader(f"Saved jobs ({len(saved)})")

    for job in saved:
        with st.expander(f"{job.title} - {job.company} ({job.location})"):
            if job.salary_min:
                st.write(f"Salary: {int(job.salary_min):,} - {int(job.salary_max or job.salary_min):,}")
            st.write(job.description[:500] + "...")
            st.markdown(f"[Apply link]({job.url})")

    if saved and st.button("Saari jobs hatao"):
        job_db.clear_jobs()
        st.rerun()