import streamlit as st

from app import tailored_db
from app.tailor import make_tailored_doc
from ui.styles import chip, chips


def doc_to_text(job, doc):
    lines = [f"Tailored for: {job.title} at {job.company}", ""]
    lines.append("SUMMARY")
    lines.append(doc.summary)
    lines.append("")
    lines.append("SKILLS: " + ", ".join(doc.skills_to_highlight))
    lines.append("")
    lines.append("RESUME POINTS")
    for b in doc.bullets:
        lines.append("- " + b.text)
    lines.append("")
    lines.append("COVER LETTER")
    lines.append(doc.cover_letter)
    return "\n".join(lines)


def show_doc(doc, job):
    if doc.passed:
        st.markdown(chip(f"Critic pass · attempt {doc.attempts}", "green"), unsafe_allow_html=True)
    else:
        st.warning(f"{doc.attempts} try ke baad bhi critic ne ye galtiyan pakdi. Manual review karo:")
        for issue in doc.issues:
            st.write("- " + issue)

    tab_points, tab_letter = st.tabs(["Resume points", "Cover letter"])

    with tab_points:
        st.write(doc.summary)
        st.markdown(chips(doc.skills_to_highlight, "blue"), unsafe_allow_html=True)
        for b in doc.bullets:
            st.write("- " + b.text)
            st.markdown(chip("from: " + b.source, "gray"), unsafe_allow_html=True)

    with tab_letter:
        st.text_area(
            "Cover letter",
            value=doc.cover_letter,
            height=260,
            key=f"cl_{job.id}",
            label_visibility="collapsed",
        )
        st.download_button(
            "Download (.txt)",
            data=doc_to_text(job, doc),
            file_name="tailored_application.txt",
            key=f"dl_{job.id}",
        )


def show_tailor_section(profile, job, match):
    st.divider()

    if st.button("Tailor resume + cover letter", key=f"tailor_{job.id}"):
        with st.spinner("Likh raha hoon aur check kar raha hoon..."):
            try:
                doc = make_tailored_doc(profile, job, match)
                tailored_db.save_tailored(doc)
            except Exception as e:
                st.error(f"Tailoring fail hui: {e}")

    doc = tailored_db.load_tailored(job.id)
    if doc is not None:
        show_doc(doc, job)