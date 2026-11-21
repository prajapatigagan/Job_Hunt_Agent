import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from pydantic import ValidationError

from app import db
from app.config import UPLOAD_DIR
from app.llm import LLMError
from app.pdf_reader import PDFError
from app.profile_parser import parse_resume_pdf
from app.schemas import Preferences, UserProfile
from ui.jobs_tab import show_jobs_tab

st.set_page_config(page_title="Job Hunt Agent", layout="wide")
db.init_db()


def csv_to_list(s):
    return [x.strip() for x in s.split(",") if x.strip()]


st.title("Job Hunt Agent")
tab_profile, tab_prefs, tab_jobs = st.tabs(["Resume / Profile", "Preferences", "Jobs"])

with tab_profile:
    uploaded = st.file_uploader("Resume PDF upload karo", type=["pdf"])

    if uploaded and st.button("Parse resume"):
        pdf_path = UPLOAD_DIR / "resume.pdf"
        pdf_path.write_bytes(uploaded.getvalue())
        with st.spinner("Resume padh raha hoon..."):
            try:
                st.session_state["draft"] = parse_resume_pdf(str(pdf_path))
                st.success("Parse ho gaya. Neeche check karke save karo.")
            except (PDFError, LLMError) as e:
                st.error(str(e))

    current = st.session_state.get("draft") or db.load_profile()

    if current:
        st.subheader("Profile (edit kar sakte ho)")
        st.caption("JSON me galti ho to yahin theek karo, phir Save dabao.")
        edited = st.text_area("Profile JSON", value=current.model_dump_json(indent=2), height=450)

        if st.button("Save profile"):
            try:
                db.save_profile(UserProfile.model_validate_json(edited))
                st.session_state.pop("draft", None)
                st.success("Profile save ho gaya.")
            except ValidationError as e:
                st.error(f"JSON galat hai:\n{e}")
    else:
        st.info("Abhi koi profile nahi hai. Resume upload karo.")

with tab_prefs:
    p = db.load_preferences() or Preferences()
    with st.form("prefs_form"):
        roles = st.text_input("Target roles (comma separated)", ", ".join(p.target_roles))
        cities = st.text_input("Cities (comma separated)", ", ".join(p.cities))
        remote = st.checkbox("Remote chalega", value=p.remote_ok)
        salary = st.number_input("Min salary (LPA)", min_value=0.0, value=float(p.min_salary_lpa or 0.0), step=0.5)
        levels = ["fresher", "0-2 years", "2-5 years", "5+ years"]
        level = st.selectbox(
            "Experience level", levels, index=levels.index(p.experience_level) if p.experience_level in levels else 0
        )
        must = st.text_input("Must-have skills (comma separated)", ", ".join(p.must_have_skills))
        black = st.text_input("Blacklist companies (comma separated)", ", ".join(p.blacklist_companies))

        if st.form_submit_button("Save preferences"):
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
            st.success("Preferences save ho gaye.")
            
with tab_jobs:
    show_jobs_tab()