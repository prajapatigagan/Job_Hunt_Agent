import uuid

import streamlit as st

from app import db, job_db, tailored_db
from app.agent_graph import build_graph, start_run, resume_run, get_run_state


@st.cache_resource
def get_graph():
    # graph ek hi baar banta hai, warna ruka hua run kho jayega
    return build_graph()


def send_decision(graph, run_id, decision):
    with st.spinner("Agent aage badh raha hai..."):
        try:
            resume_run(graph, run_id, decision)
        except Exception as e:
            st.error(f"Agent me error: {e}")
    st.rerun()


def show_approval_card(graph, run_id, values):
    job_id = values["current_job_id"]
    jobs = {job.id: job for job in job_db.load_jobs()}
    job = jobs.get(job_id)
    doc = tailored_db.load_tailored(job_id)

    if job is None or doc is None:
        st.error("Draft ya job nahi mili. Start agent dobara dabao.")
        return

    st.subheader(f"Approval chahiye: {job.title} - {job.company}")
    st.caption(f"Iske baad {len(values.get('queue', []))} jobs aur baaki hain.")
    st.markdown(f"[Job link]({job.url})")

    if doc.passed:
        st.success(f"Critic pass hua (attempt {doc.attempts}).")
    else:
        st.warning("Critic ne ye galtiyan pakdi. Dhyan se padho:")
        for issue in doc.issues:
            st.write("- " + issue)

    st.write("**Summary:** " + doc.summary)
    st.write("**Skills:** " + ", ".join(doc.skills_to_highlight))
    st.write("**Resume points:**")
    for b in doc.bullets:
        st.write(f"- {b.text}")

    letter = st.text_area(
        "Cover letter (edit kar sakte ho)", value=doc.cover_letter, height=260, key=f"agent_cl_{job_id}"
    )
    reason = st.text_input("Reject karne ka reason (optional)", key=f"agent_reason_{job_id}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Approve", key=f"approve_{job_id}"):
            decision = {"action": "approve"}
            if letter != doc.cover_letter:
                decision["cover_letter"] = letter
            send_decision(graph, run_id, decision)
    with col2:
        if st.button("Reject", key=f"reject_{job_id}"):
            send_decision(graph, run_id, {"action": "reject", "reason": reason})


def show_agent_tab():
    graph = get_graph()

    if db.load_profile() is None or db.load_preferences() is None:
        st.warning("Pehle profile aur preferences save karo.")
        return

    do_search = st.checkbox("Naye jobs bhi dhundo (JSearch ki request lagegi)", value=False)

    if st.button("Start agent"):
        run_id = str(uuid.uuid4())
        st.session_state["run_id"] = run_id
        with st.spinner("Agent chal raha hai (match, tailor, critic)... thoda time lagega"):
            try:
                start_run(graph, run_id, do_search)
            except Exception as e:
                st.error(f"Agent me error: {e}")

    run_id = st.session_state.get("run_id")
    if not run_id:
        st.info("Start agent dabao.")
        return

    next_nodes, values = get_run_state(graph, run_id)
    if not values:
        st.warning("Is run ka data nahi mila. Start agent dobara dabao.")
        return

    st.subheader("Agent log")
    for line in values.get("log", []):
        st.write("- " + line)

    if next_nodes == ("approval",):
        show_approval_card(graph, run_id, values)
    elif next_nodes:
        st.warning("Run beech me ruk gaya (shayad koi error aaya). Start agent dobara dabao.")
    else:
        st.success("Run khatam. Tracker tab me status dekho.")