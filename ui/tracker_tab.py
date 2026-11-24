import html

import streamlit as st

from app.storage import application_db, job_db
from app.config import STATUSES
from ui.styles import STATUS_KIND, chip, flash


def show_tracker_tab():
    applications = application_db.load_applications()
    if not applications:
        st.info("No applications yet. Run the agent.")
        return

    jobs = {job.id: job for job in job_db.load_jobs()}

    counts = {}
    for row in applications:
        counts[row.status] = counts.get(row.status, 0) + 1

    summary = "".join(
        chip(f"{status}: {count}", STATUS_KIND.get(status, "gray")) for status, count in counts.items()
    )
    st.markdown(summary, unsafe_allow_html=True)

    chosen = st.multiselect("Status filter", STATUSES, default=[])
    shown = [row for row in applications if not chosen or row.status in chosen]

    for row in shown:
        job = jobs.get(row.job_id)
        title = job.title if job else row.job_id
        company = job.company if job else ""

        with st.container(border=True):
            left, right = st.columns([5, 1])
            with left:
                st.markdown(
                    f'<div class="job-title">{html.escape(title)}</div>'
                    f'<div class="job-sub">{html.escape(company)}</div>',
                    unsafe_allow_html=True,
                )
            with right:
                st.markdown(chip(row.status, STATUS_KIND.get(row.status, "gray")), unsafe_allow_html=True)

            if row.reason:
                st.caption("Reject reason: " + row.reason)

            with st.expander("Update status / notes"):
                if job and job.url:
                    st.link_button("Open apply link", job.url, key=f"link_{row.job_id}")

                index = STATUSES.index(row.status) if row.status in STATUSES else 0
                new_status = st.selectbox("Status", STATUSES, index=index, key=f"status_{row.job_id}")
                notes = st.text_area("Notes", value=row.notes, key=f"notes_{row.job_id}")

                if st.button("Update", key=f"update_{row.job_id}", type="primary"):
                    application_db.set_status(row.job_id, new_status, notes=notes)
                    flash("Status updated.")
                    st.rerun()

                history = application_db.get_history(row.job_id)
                if history:
                    st.caption("History: " + " → ".join(status for status, _ in history))