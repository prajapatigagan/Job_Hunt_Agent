import html
import uuid

import streamlit as st

from app.storage import db, job_db, tailored_db
from app.agent.graph import build_graph, start_run, resume_run, get_run_state
from ui.styles import chip, chips, flash, section, stepper

STEPS = ["Search", "Match", "Select", "Tailor", "Approval"]


@st.cache_resource
def get_graph():
    # the graph is built only once, otherwise a paused run would be lost
    return build_graph()


def send_decision(graph, run_id, decision):
    with st.spinner("The agent is continuing..."):
        try:
            resume_run(graph, run_id, decision)
        except Exception as e:
            flash(f"Agent error: {e}", "error")
    st.rerun()


def show_approval_card(graph, run_id, values):
    job_id = values["current_job_id"]
    jobs = {job.id: job for job in job_db.load_jobs()}
    job = jobs.get(job_id)
    doc = tailored_db.load_tailored(job_id)

    if job is None or doc is None:
        st.error("Draft or job not found. Press Start agent again.")
        return

    with st.container(border=True):
        st.markdown(
            f'<div class="job-title">{html.escape(job.title)}</div>'
            f'<div class="job-sub">{html.escape(job.company)} · {html.escape(job.location or "-")}</div>',
            unsafe_allow_html=True,
        )
        if doc.passed:
            badge = chip(f"Critic passed · attempt {doc.attempts}", "green")
        else:
            badge = chip("Critic found problems", "amber")
        remaining = len(values.get("queue", []))
        st.markdown(badge + chip(f"{remaining} more jobs queued", "gray"), unsafe_allow_html=True)

    if not doc.passed:
        st.warning("Read this carefully, the critic flagged the following:")
        for issue in doc.issues:
            st.write("- " + issue)

    left, right = st.columns(2)

    with left:
        section("Summary")
        st.write(doc.summary)
        section("Skills")
        st.markdown(chips(doc.skills_to_highlight, "blue"), unsafe_allow_html=True)
        section("Resume points")
        for b in doc.bullets:
            st.write("- " + b.text)

    with right:
        section("Cover letter (you can edit it)")
        letter = st.text_area(
            "Cover letter",
            value=doc.cover_letter,
            height=300,
            key=f"agent_cl_{job_id}",
            label_visibility="collapsed",
        )
        reason = st.text_input("Reject reason (optional)", key=f"agent_reason_{job_id}")

        b1, b2 = st.columns(2)
        with b1:
            if st.button("Approve", key=f"approve_{job_id}", type="primary"):
                decision = {"action": "approve"}
                if letter != doc.cover_letter:
                    decision["cover_letter"] = letter
                send_decision(graph, run_id, decision)
        with b2:
            if st.button("Reject", key=f"reject_{job_id}"):
                send_decision(graph, run_id, {"action": "reject", "reason": reason})

        if job.url:
            st.link_button("Open job link", job.url)


def show_agent_tab():
    graph = get_graph()

    if db.load_profile() is None or db.load_preferences() is None:
        st.warning("Save your profile and preferences first.")
        return

    top = st.columns([3, 1])
    with top[0]:
        do_search = st.checkbox("Also search for new jobs (uses a JSearch request)", value=False)
    with top[1]:
        start_clicked = st.button("Start agent", type="primary")

    if start_clicked:
        run_id = str(uuid.uuid4())
        st.session_state["run_id"] = run_id
        with st.spinner("The agent is running (match, tailor, critic)... this can take a while"):
            try:
                start_run(graph, run_id, do_search)
            except Exception as e:
                flash(f"Agent error: {e}", "error")
        st.rerun()

    run_id = st.session_state.get("run_id")
    if not run_id:
        stepper(STEPS, -1)
        st.info("Press Start agent. It will match jobs, write drafts and pause for your approval.")
        return

    next_nodes, values = get_run_state(graph, run_id)
    if not values:
        st.warning("No data found for this run. Press Start agent again.")
        return

    paused = next_nodes == ("approval",)

    if paused:
        stepper(STEPS, 4)
    elif next_nodes:
        stepper(STEPS, 3)
    else:
        stepper(STEPS, len(STEPS))

    with st.expander("Agent log", expanded=not paused):
        for line in values.get("log", []):
            st.write("- " + line)

    if paused:
        show_approval_card(graph, run_id, values)
    elif next_nodes:
        st.warning("The run stopped midway (an error probably occurred). Press Start agent again.")
    else:
        st.success("Run finished. Check the Tracker tab for statuses.")