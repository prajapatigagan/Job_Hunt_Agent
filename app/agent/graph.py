import operator
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt

from app.storage import application_db, db, job_db, match_db, tailored_db
from app.config import TOP_K_JOBS
from app.agent.tools.job_finder import find_jobs
from app.rag.matcher import match_jobs
from app.agent.tailor import make_tailored_doc


# graph ka shared data. Sirf chhoti, simple cheezein rakhi hain.
# Profile, jobs wagairah har node DB se khud padh leta hai.
class AgentState(TypedDict):
    do_search: bool
    queue: list              # approval ke liye bachi hui job ids
    current_job_id: str      # abhi jis job ka approval chal raha hai
    log: Annotated[list, operator.add]


def search_node(state):
    if not state["do_search"]:
        return {"log": ["Search skip kiya, saved jobs use hongi."]}

    prefs = db.load_preferences()
    jobs = find_jobs(prefs)
    new_count = job_db.save_jobs(jobs)
    return {"log": [f"Search: {len(jobs)} jobs mili, {new_count} naye save hue."]}


def match_node(state):
    profile = db.load_profile()
    prefs = db.load_preferences()
    jobs = job_db.load_jobs()

    if profile is None or prefs is None or not jobs:
        return {"log": ["Match skip: profile, preferences ya jobs nahi mili."]}

    results = match_jobs(profile, prefs, jobs)
    match_db.save_matches(results)
    return {"log": [f"Match: {len(results)} jobs score hui."]}


def select_node(state):
    decided = application_db.decided_job_ids()
    saved_ids = set(job.id for job in job_db.load_jobs())

    queue = []
    for m in match_db.load_matches():
        if m.verdict == "skip":
            continue
        if m.job_id in decided:
            continue
        if m.job_id not in saved_ids:
            continue
        queue.append(m.job_id)
        if len(queue) == TOP_K_JOBS:
            break

    return {"queue": queue, "log": [f"Select: {len(queue)} jobs approval ke liye chuni."]}


def tailor_node(state):
    queue = list(state["queue"])
    job_id = queue.pop(0)

    profile = db.load_profile()
    jobs = {job.id: job for job in job_db.load_jobs()}
    matches = {m.job_id: m for m in match_db.load_matches()}
    job = jobs[job_id]

    try:
        doc = make_tailored_doc(profile, job, matches.get(job_id))
    except Exception as e:
        # ek job fail ho to poora run na ruke
        return {
            "queue": queue,
            "current_job_id": "",
            "log": [f"Tailor fail: {job.title} ({job.company}): {e}"],
        }

    tailored_db.save_tailored(doc)
    application_db.set_status(job_id, "drafted")
    return {
        "queue": queue,
        "current_job_id": job_id,
        "log": [f"Tailor: {job.title} ({job.company}) ka draft taiyar."],
    }


def approval_node(state):
    job_id = state["current_job_id"]
    if not job_id:
        return {"log": ["Approval skip: is job ka draft nahi bana."]}

    # graph yahin ruk jata hai, jab tak UI se decision na aaye
    # Dhyan: resume par ye node shuru se dobara chalta hai, isliye
    # DB me kuch bhi likhna interrupt ke BAAD hi hai.
    decision = interrupt({"job_id": job_id})

    # tune cover letter edit kiya ho to save kar do
    new_letter = decision.get("cover_letter")
    if new_letter:
        doc = tailored_db.load_tailored(job_id)
        if doc is not None:
            doc.cover_letter = new_letter
            tailored_db.save_tailored(doc)

    if decision.get("action") == "approve":
        application_db.set_status(job_id, "approved")
        message = "Approved"
    else:
        application_db.set_status(job_id, "rejected", reason=decision.get("reason", ""))
        message = "Rejected"

    return {"current_job_id": "", "log": [f"Approval: {message}"]}


def route_queue(state):
    # queue me jobs bachi hain to tailor par wapas, nahi to khatam
    if state["queue"]:
        return "tailor"
    return "end"


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("search", search_node)
    builder.add_node("match", match_node)
    builder.add_node("select", select_node)
    builder.add_node("tailor", tailor_node)
    builder.add_node("approval", approval_node)

    builder.add_edge(START, "search")
    builder.add_edge("search", "match")
    builder.add_edge("match", "select")
    builder.add_conditional_edges("select", route_queue, {"tailor": "tailor", "end": END})
    builder.add_edge("tailor", "approval")
    builder.add_conditional_edges("approval", route_queue, {"tailor": "tailor", "end": END})

    # InMemorySaver: ruka hua run memory me rehta hai (app band hone par chala jata hai)
    return builder.compile(checkpointer=InMemorySaver())


# ---------- UI ke liye chhote helpers ----------

def start_run(graph, run_id, do_search):
    config = {"configurable": {"thread_id": run_id}}
    start_state = {"do_search": do_search, "queue": [], "current_job_id": "", "log": []}
    graph.invoke(start_state, config)


def resume_run(graph, run_id, decision):
    config = {"configurable": {"thread_id": run_id}}
    graph.invoke(Command(resume=decision), config)


def get_run_state(graph, run_id):
    config = {"configurable": {"thread_id": run_id}}
    snapshot = graph.get_state(config)
    return snapshot.next, snapshot.values


if __name__ == "__main__":
    # bina UI ke terminal me test:  python -m app.agent.graph
    import uuid

    db.init_db()
    graph = build_graph()
    run_id = str(uuid.uuid4())
    start_run(graph, run_id, False)

    while True:
        next_nodes, values = get_run_state(graph, run_id)
        if next_nodes != ("approval",):
            break

        jobs = {job.id: job for job in job_db.load_jobs()}
        job = jobs[values["current_job_id"]]
        doc = tailored_db.load_tailored(job.id)

        print("\n--- APPROVAL ---")
        print(job.title, "|", job.company)
        print("Critic passed:", doc.passed, doc.issues)
        print(doc.cover_letter)

        choice = input("\nApprove (a) / Reject (r)? ").strip().lower()
        if choice == "a":
            resume_run(graph, run_id, {"action": "approve"})
        else:
            reason = input("Reject reason: ")
            resume_run(graph, run_id, {"action": "reject", "reason": reason})

    print("\nLOG:")
    for line in values.get("log", []):
        print("-", line)