import streamlit as st

from app import application_db, job_db
from app.config import STATUSES


def show_tracker_tab():
    applications = application_db.load_applications()
    if not applications:
        st.info("Abhi koi application nahi hai. Agent chalao.")
        return

    jobs = {job.id: job for job in job_db.load_jobs()}
    st.subheader(f"Applications ({len(applications)})")

    for row in applications:
        job = jobs.get(row.job_id)
        title = f"{job.title} - {job.company}" if job else row.job_id

        with st.expander(f"[{row.status}] {title}"):
            if job:
                st.markdown(f"[Apply link]({job.url})")
            if row.reason:
                st.write("Reject reason: " + row.reason)

            index = STATUSES.index(row.status) if row.status in STATUSES else 0
            new_status = st.selectbox("Status", STATUSES, index=index, key=f"status_{row.job_id}")
            notes = st.text_area("Notes", value=row.notes, key=f"notes_{row.job_id}")

            if st.button("Update", key=f"update_{row.job_id}"):
                application_db.set_status(row.job_id, new_status, notes=notes)
                st.success("Update ho gaya.")

            history = application_db.get_history(row.job_id)
            if history:
                st.caption("History: " + " -> ".join(status for status, _ in history))