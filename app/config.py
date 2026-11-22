import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "app.db"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_MAX_RETRIES = 2
MAX_RESUME_CHARS = 12000

for _d in (DATA_DIR, UPLOAD_DIR):
    _d.mkdir(parents=True, exist_ok=True)



RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
JOB_COUNTRY = "in"
MAX_QUERIES = 2

EMBED_MODEL = "all-MiniLM-L6-v2"
TOP_N_FOR_LLM = 15      # embedding ke baad kitni jobs LLM se score karani hain
W_LLM = 0.5             # final score me LLM ka hissa
W_SEMANTIC = 0.3        # embedding similarity ka hissa
W_PREF = 0.2            # must-have skills ka hissa

MAX_TAILOR_ATTEMPTS = 3

TOP_K_JOBS = 3   # ek run me kitni jobs approval ke liye aayengi
STATUSES = ["shortlisted", "drafted", "approved", "applied", "interview", "offer", "rejected", "withdrawn"]