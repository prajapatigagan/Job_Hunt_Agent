import streamlit as st
from pydantic import ValidationError

from app import db
from app.config import UPLOAD_DIR
from app.llm import LLMError
from app.pdf_reader import PDFError
from app.profile_parser import parse_resume_pdf
from app.schemas import Preferences, UserProfile
from ui.styles import chips, flash, section


def csv_to_list(s):
    return [x.strip() for x in s.split(",") if x.strip()]


def show_profile_card(profile):
    with st.container(border=True):
        st.markdown(f"### {profile.name}")
        contact = " · ".join(x for x in [profile.email, profile.phone] if x)
        if contact:
            st.caption(contact)
        if profile.summary:
            st.write(profile.summary)
        section("Skills")
        st.markdown(chips(profile.skills, "blue"), unsafe_allow_html=True)

    if profile.experience:
        section("Experience")
    for exp in profile.experience:
        with st.container(border=True):
            st.markdown(f"**{exp.role}** · {exp.company}")
            for bullet in exp.bullets:
                st.write("- " + bullet)

    if profile.projects:
        section("Projects")
    for project in profile.projects:
        with st.container(border=True):
            st.markdown(f"**{project.name}**")
            st.markdown(chips(project.tech, "purple"), unsafe_allow_html=True)
            for bullet in project.bullets:
                st.write("- " + bullet)

    if profile.education:
        section("Education")
    for edu in profile.education:
        years = " - ".join(x for x in [edu.start, edu.end] if x)
        st.write(f"**{edu.degree or ''}** · {edu.institute} {'(' + years + ')' if years else ''}")


def show_profile_tab():
    left, right = st.columns([1, 1.5])

    with left:
        section("Resume upload")
        uploaded = st.file_uploader("Resume PDF", type=["pdf"], label_visibility="collapsed")

        if uploaded and st.button("Parse resume", type="primary"):
            pdf_path = UPLOAD_DIR / "resume.pdf"
            pdf_path.write_bytes(uploaded.getvalue())
            with st.spinner("Resume padh raha hoon..."):
                try:
                    st.session_state["draft"] = parse_resume_pdf(str(pdf_path))
                    st.success("Parse ho gaya. Check karke save karo.")
                except (PDFError, LLMError) as e:
                    st.error(str(e))

        st.caption("Text wala PDF use karo. Scanned image PDF nahi chalega.")

    current = st.session_state.get("draft") or db.load_profile()
    is_draft = "draft" in st.session_state

    with right:
        if current is None:
            st.info("Abhi koi profile nahi hai. Left side se resume upload karo.")
            return

        if is_draft:
            st.warning("Ye abhi save nahi hua. Neeche JSON me check karke Save profile dabao.")

        show_profile_card(current)

        with st.expander("Profile JSON edit karo", expanded=is_draft):
            edited = st.text_area(
                "Profile JSON",
                value=current.model_dump_json(indent=2),
                height=400,
                label_visibility="collapsed",
            )
            saved = False
            if st.button("Save profile", type="primary"):
                try:
                    db.save_profile(UserProfile.model_validate_json(edited))
                    st.session_state.pop("draft", None)
                    saved = True
                except ValidationError as e:
                    st.error(f"JSON galat hai:\n{e}")
            if saved:
                flash("Profile save ho gaya.")
                st.rerun()


def show_prefs_tab():
    p = db.load_preferences() or Preferences()
    levels = ["fresher", "0-2 years", "2-5 years", "5+ years"]

    with st.form("prefs_form"):
        col1, col2 = st.columns(2)
        with col1:
            roles = st.text_input("Target roles (comma separated)", ", ".join(p.target_roles))
            cities = st.text_input("Cities (comma separated)", ", ".join(p.cities))
            must = st.text_input("Must-have skills (comma separated)", ", ".join(p.must_have_skills))
        with col2:
            level = st.selectbox(
                "Experience level",
                levels,
                index=levels.index(p.experience_level) if p.experience_level in levels else 0,
            )
            salary = st.number_input(
                "Min salary (LPA)", min_value=0.0, value=float(p.min_salary_lpa or 0.0), step=0.5
            )
            black = st.text_input("Blacklist companies (comma separated)", ", ".join(p.blacklist_companies))
            remote = st.checkbox("Remote chalega", value=p.remote_ok)

        submitted = st.form_submit_button("Save preferences", type="primary")

    if submitted:
        db.save_preferences(
            Preferences(
                target_roles=csv_to_list(roles),
                cities=csv_to_list(cities),
                remote_ok=remote,
                min_salary_lpa=salary or None,
                experience_level=level,
                must_have_skills=csv_to_list(must),
                blacklist_companies=csv_to_list(black),
            )
        )
        flash("Preferences save ho gaye.")
        st.rerun()