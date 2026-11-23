import html
import uuid

import streamlit as st

from app.storage import db, job_db, tailored_db
from app.agent.graph import build_graph, start_run, resume_run, get_run_state
from ui.styles import chip, chips, flash, section, stepper

STEPS = ["Search", "Match", "Select", "Tailor", "Approval"]


@st.cache_resource
def get_graph():
    # graph ek hi baar banta hai, warna ruka hua run kho jayega
    return build_graph()


def send_decision(graph, run_id, decision):
    with st.spinner("Agent aage badh raha hai..."):
        try:
            resume_run(graph, run_id, decision)
        except Exception as e:
            flash(f"Agent me error: {e}", "error")
    st.rerun()


def show_approval_card(graph, run_id, values):
    job_id = values["current_job_id"]
    jobs = {job.id: job for job in job_db.load_jobs()}
    job = jobs.get(job_id)
    doc = tailored_db.load_tailored(job_id)

    if job is None or doc is None:
        st.error("Draft ya job nahi mili. Start agent dobara dabao.")
        return

    with st.container(border=True):
        st.markdown(
            f'<div class="job-title">{html.escape(job.title)}</div>'
            f'<div class="job-sub">{html.escape(job.company)} · {html.escape(job.location or "-")}</div>',
            unsafe_allow_html=True,
        )
        if doc.passed:
            badge = chip(f"Critic pass · attempt {doc.attempts}", "green")
        else:
            badge = chip("Critic ne galtiyan pakdi", "amber")
        remaining = len(values.get("queue", []))
        st.markdown(badge + chip(f"{remaining} jobs aur baaki", "gray"), unsafe_allow_html=True)

    if not doc.passed:
        st.warning("Dhyan se padho, critic ne ye pakda:")
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
        section("Cover letter (edit kar sakte ho)")
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
            st.link_button("Job link kholo", job.url)


def show_agent_tab():
    graph = get_graph()

    if db.load_profile() is None or db.load_preferences() is None:
        st.warning("Pehle profile aur preferences save karo.")
        return

    top = st.columns([3, 1])
    with top[0]:
        do_search = st.checkbox("Naye jobs bhi dhundo (JSearch ki request lagegi)", value=False)
    with top[1]:
        start_clicked = st.button("Start agent", type="primary")

    if start_clicked:
        run_id = str(uuid.uuid4())
        st.session_state["run_id"] = run_id
        with st.spinner("Agent chal raha hai (match, tailor, critic)... thoda time lagega"):
            try:
                start_run(graph, run_id, do_search)
            except Exception as e:
                flash(f"Agent me error: {e}", "error")
        st.rerun()

    run_id = st.session_state.get("run_id")
    if not run_id:
        stepper(STEPS, -1)
        st.info("Start agent dabao. Agent jobs match karega, draft likhega aur tere approval par ruk jayega.")
        return

    next_nodes, values = get_run_state(graph, run_id)
    if not values:
        st.warning("Is run ka data nahi mila. Start agent dobara dabao.")
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
        st.warning("Run beech me ruk gaya (shayad koi error aaya). Start agent dobara dabao.")
    else:
        st.success("Run khatam. Tracker tab me status dekho.")