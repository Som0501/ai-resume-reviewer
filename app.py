import os
import re
import random
from datetime import datetime
from io import BytesIO

import streamlit as st
from pypdf import PdfReader
from dotenv import load_dotenv
from groq import Groq

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.pdfgen import canvas

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MAX_PDF_SIZE_MB = 5
MAX_JD_CHARS = 10_000
MIN_CV_CHARS = 200
LLM_MODEL = "llama-3.3-70b-versatile"

SAMPLE_JDS = [
    {
        "label": "Junior ML Engineer · Bangalore",
        "text": """We're hiring a Junior Machine Learning Engineer to join our Computer Vision team in Bangalore.

Responsibilities:
- Build and deploy deep learning models for image classification and object detection
- Work with PyTorch, TensorFlow, and modern transformer architectures (ViT, Swin)
- Collaborate with senior engineers on production ML pipelines
- Write clean, tested Python code and contribute to model evaluation frameworks

Required:
- Bachelor's or Master's in Computer Science, AI, or related field
- 0-2 years experience with Python and at least one deep learning framework
- Solid understanding of CNNs, transformers, and modern training techniques
- Familiarity with Git and Linux

Nice to have:
- Experience deploying models with Docker / FastAPI / cloud platforms (AWS/GCP)
- Published projects or open source contributions in CV/NLP
- Experience with LLMs, RAG, or generative AI

CTC: 8-14 LPA"""
    },
    {
        "label": "Computer Vision Engineer · AI Startup",
        "text": """Series-B AI startup hiring a Computer Vision Engineer for real-time video analytics.

What you'll do:
- Design and ship CV models for object tracking, action recognition, and pose estimation in production video pipelines
- Optimise model inference latency for edge deployment (Jetson, mobile)
- Own the full ML lifecycle from data curation to deployment
- Collaborate with product and engineering on customer-facing features

Required:
- 1-3 years hands-on with PyTorch or TensorFlow
- Strong CV fundamentals — detection, tracking, segmentation
- Experience with model optimisation (quantisation, TensorRT, ONNX)
- Comfortable with Linux, Docker, and CI/CD basics
- A portfolio of CV projects (GitHub, papers, or demos)

Bonus:
- Experience with video transformers (TimeSformer, VideoMAE)
- Familiarity with C++ and CUDA
- Past contributions to open-source CV libraries

CTC: 14-22 LPA + equity"""
    },
    {
        "label": "Data Scientist · Analytics Firm",
        "text": """Join our analytics consulting team as a Data Scientist working with Fortune 500 clients.

Role:
- Design and build predictive models for clients in retail, finance, and healthcare
- Translate business problems into data science problems and back
- Present findings to stakeholders — both technical and non-technical
- Work in cross-functional pods with engineers, analysts, and consultants

Must have:
- Bachelor's/Master's in Statistics, CS, Engineering, Economics, or Math
- 0-2 years experience with Python (pandas, scikit-learn, statsmodels)
- Strong SQL and data wrangling skills
- Ability to communicate insights clearly in writing and presentations
- Comfortable working on multiple projects simultaneously

Preferred:
- Exposure to ML beyond scikit-learn (XGBoost, deep learning)
- Tableau or Power BI for dashboards
- Cloud experience (AWS, Azure)
- Domain knowledge in BFSI or retail

CTC: 7-12 LPA"""
    },
    {
        "label": "GenAI Engineer · Well-funded Startup",
        "text": """We're a 30-person GenAI startup (recently raised our Series A) hiring our 5th ML engineer.

You'll work on:
- Building and fine-tuning LLM-powered features for our flagship product
- Designing RAG pipelines: vector DBs, retrieval, reranking, evals
- Prompt engineering, evaluation harnesses, and offline benchmarking
- Shipping fast — we deploy multiple times a day

Must have:
- Strong Python fundamentals
- 1+ year hands-on with LLMs (OpenAI, Anthropic, open models) in production or substantial side projects
- Experience with at least one LLM framework (LangChain, LlamaIndex, Haystack, or DIY)
- Comfortable with vector databases (Pinecone, Weaviate, Chroma, pgvector)
- Strong written communication — we write a lot of design docs

Nice to have:
- Fine-tuning experience (LoRA, QLoRA, full fine-tuning)
- Familiarity with eval frameworks (Ragas, DeepEval, custom)
- Frontend chops (React, Streamlit) to ship demos solo
- Open source contributions

CTC: 18-28 LPA + meaningful equity"""
    },
    {
        "label": "SDE-1 · Product Company",
        "text": """SDE-1 opening at a mid-stage product company building tools for developers.

You'll be responsible for:
- Writing production code in Python and TypeScript across our backend and internal tools
- Owning features end-to-end: design, implementation, testing, deployment, monitoring
- Code reviews and mentoring interns
- Working with PMs and designers to ship customer-facing features

Required:
- Bachelor's in CS or equivalent
- 0-2 years experience writing production code
- Strong fundamentals in data structures, algorithms, system design (entry-level)
- Comfortable with at least one of: Python, TypeScript, Go, Java
- Familiarity with Git, CI/CD, and basic Linux

Bonus:
- Experience with cloud (AWS or GCP)
- Past internship or full-time at a product company
- Side projects on GitHub
- Contributions to open source

CTC: 12-18 LPA"""
    },
    {
        "label": "AI Research Intern · Research Lab",
        "text": """6-month AI Research Internship at our applied research lab in Bengaluru / Hyderabad.

Research areas:
- Multimodal learning (vision + language)
- Efficient training and inference for large models
- Robustness and evaluation of generative models
- Applied research that turns into shipped product

What you'll do:
- Run experiments, write code, read papers
- Co-author internal reports and (where possible) external publications
- Collaborate with senior researchers and engineers
- Present your work at internal seminars

Required:
- Final-year undergrad / Master's / PhD in CS, AI, EE, Math, or Physics
- Strong PyTorch skills
- Comfortable reading and implementing recent ML papers
- A portfolio: research project, dissertation, paper, or substantial open source work

Preferred:
- Prior internship at a research lab or industry AI team
- First-author paper at a workshop or conference
- Specific interest in vision-language models or efficient ML

Stipend: 80k-1.2L per month + housing"""
    }
]


LOADING_MESSAGES_HONEST = [
    "Asking the AI to be honest but not mean...",
    "Quietly judging your bullet points...",
    "Cross-referencing 10,000 CVs in memory...",
    "Brewing some honest feedback...",
    "Reading between the lines so you don't have to...",
]

LOADING_MESSAGES_ROAST = [
    "Sharpening the knives...",
    "Loading maximum sass...",
    "Calling your bullet points to the principal's office...",
    "Asking ChatGPT's meaner cousin for help...",
    "Booking your CV a therapy appointment in advance...",
    "Warming up the comedy roast generator...",
]


st.set_page_config(
    page_title="Resume Reality Check",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)


if "sample_index" not in st.session_state:
    st.session_state.sample_index = 0


# === CSS ===

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"], .stMarkdown {
    font-family: 'Space Grotesk', sans-serif !important;
}

.stApp {
    background: 
        radial-gradient(ellipse at 75% 10%, rgba(0, 242, 254, 0.15) 0%, transparent 50%),
        radial-gradient(ellipse at 20% 90%, rgba(14, 165, 233, 0.08) 0%, transparent 50%),
        #050810;
}

.stApp::before {
    content: "";
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background-image:
        linear-gradient(rgba(0, 242, 254, 0.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 242, 254, 0.025) 1px, transparent 1px);
    background-size: 60px 60px;
    pointer-events: none;
    z-index: 0;
}
            
/* === HIDE STREAMLIT BRANDING === */
.stApp > footer {
    display: none !important;
}

[data-testid="stStatusWidget"],
[data-testid="stToolbar"],
.viewerBadge_container__1QSob,
.styles_viewerBadge__1yB5_,
.viewerBadge_link__1S137,
.viewerBadge_text__1JaDK {
    display: none !important;
}

#MainMenu {
    display: none !important;
    visibility: hidden !important;
}

.stDeployButton {
    display: none !important;
}

header[data-testid="stHeader"] {
    background: transparent !important;
    height: 0 !important;
}

a[href*="streamlit.io"] {
    display: none !important;
}            

.main .block-container {
    position: relative;
    z-index: 1;
    padding-top: 2rem !important;
    max-width: 1100px;
}

.hero-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(0, 242, 254, 0.06);
    border: 1px solid rgba(0, 242, 254, 0.2);
    padding: 0.4rem 1rem;
    border-radius: 100px;
    font-size: 0.78rem;
    color: #a8e8ff;
    font-family: 'JetBrains Mono', monospace;
}

.hero-pill .plus {
    color: #00f2fe;
    font-weight: 700;
}

.hero-title {
    font-size: 5rem;
    font-weight: 700;
    line-height: 1.05;
    letter-spacing: -2.5px;
    margin: 1.2rem 0 1rem 0;
    color: white;
    text-align: center;
}

.hero-title .accent {
    background: linear-gradient(90deg, #00f2fe 0%, #0ea5e9 50%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-sub {
    font-size: 1.1rem;
    color: #94a3b8;
    margin: 0 auto;
    line-height: 1.55;
    text-align: center;
    width: 100%;
}

.mode-label {
    text-align: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #64748b;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin: 2rem 0 0.8rem 0;
}

.mode-helper {
    text-align: center;
    color: #94a3b8;
    font-size: 0.9rem;
    margin: 0.5rem auto 2rem auto;
    max-width: 580px;
}

.stElementContainer.st-key-mode_select {
    width: 100% !important;
    display: flex !important;
    justify-content: center !important;
    margin: 0 auto !important;
}

[data-testid="stRadio"] {
    width: auto !important;
}

[data-testid="stRadio"] > label {
    display: none !important;
}

[data-testid="stRadio"] > div {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    width: 100% !important;
}

div[role="radiogroup"] {
    display: inline-flex !important;
    flex-direction: row !important;
    gap: 0.5rem !important;
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(0, 242, 254, 0.15) !important;
    padding: 0.4rem !important;
    border-radius: 14px !important;
    margin: 0 auto !important;
}

div[role="radiogroup"] label {
    background: transparent !important;
    border-radius: 10px !important;
    padding: 0.5rem 1.2rem !important;
    transition: all 0.25s ease !important;
    cursor: pointer !important;
    margin: 0 !important;
}

div[role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(135deg, #0ea5e9, #00f2fe) !important;
    box-shadow: 0 4px 16px rgba(0, 242, 254, 0.3) !important;
}

div[role="radiogroup"] label p {
    color: #cbd5e1 !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
}

div[role="radiogroup"] label:has(input:checked) p {
    color: #050810 !important;
}

div[role="radiogroup"] input[type="radio"] {
    display: none !important;
}

.input-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 1.8px;
    margin-bottom: 0.6rem;
    font-family: 'JetBrains Mono', monospace;
}

.input-label .num {
    display: inline-block;
    background: linear-gradient(135deg, #0ea5e9, #00f2fe);
    color: #050810;
    width: 20px; height: 20px;
    line-height: 20px;
    border-radius: 50%;
    text-align: center;
    margin-right: 8px;
    font-size: 0.7rem;
    font-weight: 800;
}

[data-testid="stFileUploader"] section {
    background: rgba(255, 255, 255, 0.025);
    border: 1.5px dashed rgba(0, 242, 254, 0.2);
    border-radius: 14px;
    transition: all 0.25s ease;
    padding: 1.2rem !important;
}

[data-testid="stFileUploader"] section:hover {
    border-color: rgba(0, 242, 254, 0.6);
    background: rgba(0, 242, 254, 0.04);
}

[data-testid="stFileUploader"] button {
    background: rgba(0, 242, 254, 0.06) !important;
    border: 1px solid rgba(0, 242, 254, 0.2) !important;
    color: #00f2fe !important;
}

.stTextArea textarea {
    background: rgba(255, 255, 255, 0.025) !important;
    border: 1px solid rgba(0, 242, 254, 0.15) !important;
    border-radius: 14px !important;
    color: #ffffff !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.88rem !important;
    padding: 0.9rem !important;
}

.stTextArea textarea:focus {
    border-color: rgba(0, 242, 254, 0.6) !important;
    box-shadow: 0 0 0 3px rgba(0, 242, 254, 0.12) !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0ea5e9 0%, #00f2fe 100%);
    color: #050810;
    border: none;
    border-radius: 14px;
    padding: 0.95rem 2rem;
    font-weight: 700;
    font-size: 1.1rem;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 0.3px;
    transition: all 0.25s ease;
    box-shadow: 0 8px 28px rgba(0, 242, 254, 0.25);
}

.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 36px rgba(0, 242, 254, 0.4);
}

.stButton > button[kind="primary"]:active {
    transform: translateY(0);
}

.stButton > button[kind="secondary"] {
    background: rgba(0, 242, 254, 0.05);
    color: #a8e8ff;
    border: 1px solid rgba(0, 242, 254, 0.2);
    border-radius: 10px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    transition: all 0.2s ease;
}

.stButton > button[kind="secondary"]:hover {
    background: rgba(0, 242, 254, 0.12);
    border-color: rgba(0, 242, 254, 0.5);
    color: #00f2fe;
}

.sample-badge {
    display: inline-block;
    background: rgba(0, 242, 254, 0.08);
    border: 1px solid rgba(0, 242, 254, 0.2);
    color: #a8e8ff;
    padding: 0.3rem 0.8rem;
    border-radius: 100px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    margin: 0.4rem 0;
}

.feature-row {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 1rem;
    margin: 3rem 0 2rem 0;
}

.feature-card {
    background: rgba(255, 255, 255, 0.025);
    border: 1px solid rgba(0, 242, 254, 0.1);
    border-radius: 16px;
    padding: 1.5rem;
    transition: all 0.3s ease;
}

.feature-card:hover {
    border-color: rgba(0, 242, 254, 0.4);
    background: rgba(0, 242, 254, 0.04);
    transform: translateY(-2px);
}

.feature-icon {
    font-size: 1.6rem;
    margin-bottom: 0.8rem;
}

.feature-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: white;
    margin-bottom: 0.4rem;
}

.feature-desc {
    font-size: 0.85rem;
    color: #94a3b8;
    line-height: 1.5;
}

.vibe-check {
    text-align: center;
    padding: 2.5rem 2rem;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(0, 242, 254, 0.12);
    border-radius: 20px;
    margin: 2rem 0 1.5rem 0;
    animation: fadeIn 0.5s ease;
    backdrop-filter: blur(10px);
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.vibe-label-top {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #64748b;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 1rem;
}

.vibe-verdict {
    font-size: 2rem;
    font-weight: 700;
    margin-top: 1.5rem;
    font-style: italic;
}

.vibe-flavour {
    margin-top: 0.6rem;
    color: #cbd5e1;
    font-size: 1rem;
    max-width: 500px;
    margin-left: auto;
    margin-right: auto;
    line-height: 1.5;
}

.stMarkdown h2 {
    font-size: 1.4rem !important;
    font-weight: 700 !important;
    margin-top: 2rem !important;
    padding: 0.9rem 1.3rem !important;
    background: rgba(255, 255, 255, 0.04);
    border-left: 4px solid #00f2fe;
    border-radius: 8px;
    color: white !important;
}

.stMarkdown ul li, .stMarkdown ol li, .stMarkdown p {
    color: #cbd5e1 !important;
    line-height: 1.7;
}

.stMarkdown strong {
    color: #00f2fe !important;
}

.stDownloadButton > button {
    background: linear-gradient(135deg, #0ea5e9 0%, #00f2fe 100%) !important;
    color: #050810 !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.85rem 2rem !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    font-family: 'Space Grotesk', sans-serif !important;
    box-shadow: 0 6px 20px rgba(0, 242, 254, 0.2) !important;
    transition: all 0.25s ease !important;
}

.stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 28px rgba(0, 242, 254, 0.35) !important;
}

.made-by-footer {
    text-align: center;
    margin-top: 4rem;
    padding: 2rem 0;
    color: #475569;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
}

.made-by-footer a {
    color: #00f2fe;
    text-decoration: none;
}

.made-by-footer a:hover {
    color: #0ea5e9;
}

[data-testid="stCaptionContainer"], .stCaption {
    color: #64748b !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.75rem !important;
}
</style>
""", unsafe_allow_html=True)


# === HERO ===

st.markdown("""
<div style="text-align: center; padding: 2rem 0 1rem 0;">
    <span class="hero-pill"><span class="plus">+</span> AI Powered · Free to use</span>
    <h1 class="hero-title">Resume Reality <span class="accent">Check.</span></h1>
    <p class="hero-sub">
        Upload your CV, paste a JD, pick your poison. Get the feedback your friends won't give you.
    </p>
</div>
""", unsafe_allow_html=True)


# === MODE TOGGLE ===

st.markdown('<div class="mode-label">Choose Your Mode</div>', unsafe_allow_html=True)

mode = st.radio(
    "mode",
    ["💬  Honest Feedback", "🔥  Roast Me"],
    horizontal=True,
    label_visibility="collapsed",
    key="mode_select"
)

if "Honest" in mode:
    st.markdown(
        '<div class="mode-helper">Constructive, specific, actionable feedback from a senior recruiter persona.</div>',
        unsafe_allow_html=True
    )
else:
    st.markdown(
        '<div class="mode-helper">☠️  No mercy. Comedy roast from a friend who reads CVs for sport. You asked for this.</div>',
        unsafe_allow_html=True
    )


# === INPUTS ===

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown('<div class="input-label"><span class="num">1</span> Your CV</div>', unsafe_allow_html=True)
    uploaded_cv = st.file_uploader(
        f"PDF only, max {MAX_PDF_SIZE_MB} MB",
        type=["pdf"],
        accept_multiple_files=False,
        label_visibility="collapsed"
    )
    if uploaded_cv is not None:
        size_mb = uploaded_cv.size / (1024 * 1024)
        st.caption(f"📄  {uploaded_cv.name} · {size_mb:.2f} MB")

with col2:
    label_col, btn_col = st.columns([3, 1])
    with label_col:
        st.markdown('<div class="input-label"><span class="num">2</span> Job Description</div>', unsafe_allow_html=True)
    with btn_col:
        if st.button("🎲  Sample", use_container_width=True, help="Click for a different sample JD"):
            st.session_state.sample_index = (st.session_state.sample_index + 1) % len(SAMPLE_JDS)
            st.session_state["jd_text"] = SAMPLE_JDS[st.session_state.sample_index]["text"]
    
    job_description = st.text_area(
        "JD",
        height=180,
        placeholder="Paste the JD here. Or click 🎲 Sample to cycle through example roles.",
        label_visibility="collapsed",
        key="jd_text"
    )
    
    char_count = f"{len(job_description):,} / {MAX_JD_CHARS:,} characters"
    if job_description and job_description == SAMPLE_JDS[st.session_state.sample_index]["text"]:
        current_label = SAMPLE_JDS[st.session_state.sample_index]["label"]
        st.markdown(
            f'<span class="sample-badge">📋 Sample {st.session_state.sample_index + 1}/{len(SAMPLE_JDS)} · {current_label}</span>',
            unsafe_allow_html=True
        )
    st.caption(char_count)

st.write("")

button_label = "🎯  Analyze My CV" if "Honest" in mode else "🔥  Roast My CV"

analyze_clicked = st.button(
    button_label,
    type="primary",
    use_container_width=True
)


# === FEATURE CARDS ===

st.markdown("""
<div class="feature-row">
    <div class="feature-card">
        <div class="feature-icon">🎯</div>
        <div class="feature-title">JD Alignment</div>
        <div class="feature-desc">Match score calibrated against the specific role you're targeting — no generic checklist.</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">✏️</div>
        <div class="feature-title">Bullet Rewrites</div>
        <div class="feature-desc">Your weakest bullets, quoted exactly, then rewritten with strong verbs and metrics.</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🚀</div>
        <div class="feature-title">Action Items</div>
        <div class="feature-desc">Three specific things to do this week before you hit submit. Ranked by impact.</div>
    </div>
</div>
""", unsafe_allow_html=True)


# === HELPERS ===

def extract_text_from_pdf(pdf_file) -> str:
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += (page.extract_text() or "") + "\n"
    return text.strip()


def validate_inputs(cv_file, jd_text: str) -> tuple[bool, str]:
    if cv_file is None:
        return False, "You forgot the CV — kind of the main ingredient."
    size_mb = cv_file.size / (1024 * 1024)
    if size_mb > MAX_PDF_SIZE_MB:
        return False, f"PDF is {size_mb:.1f} MB — trim it under {MAX_PDF_SIZE_MB} MB."
    if not jd_text or not jd_text.strip():
        return False, "Need a job description too. Paste one in or hit Sample."
    if len(jd_text) > MAX_JD_CHARS:
        return False, f"JD too long ({len(jd_text):,} chars). Keep it under {MAX_JD_CHARS:,}."
    return True, ""


HONEST_PROMPT = """You are a senior technical recruiter who has reviewed 10,000+ CVs for AI, ML, and software engineering roles. You give candid, specific, evidence-based feedback. Slightly dry humour. Never mean, never sycophantic. Sound like a friend who happens to be a brutally honest recruiter.

STRICT RULES:
1. NEVER give generic advice. Every point must reference something specific from the CV or JD.
2. ALWAYS quote directly from the CV in double quotation marks when pointing out weak bullets.
3. ALWAYS reference specific JD requirements when noting gaps.
4. Scores: 90+ near-perfect, 70-89 strong with minor gaps, 50-69 partial, below 50 mismatch.
5. Bullet rewrites use action verbs, quantify outcomes, align with JD language.
6. Avoid corporate jargon like "leverage" or "synergy."

START with the score on its own line, EXACTLY this format:
SCORE: XX/100

Then format the rest in Markdown with these EXACT headers:

## 🎯 The Verdict
ONE punchy sentence explaining the score.

## ✅ What's Working
3-5 specific things from the CV that map to JD requirements.

## ⚠️ Where The Gaps Are
3-5 specific JD requirements missing or weak in the CV. Quote the JD then explain.

## ✏️ Bullets That Need Work
2-3 weakest bullets. For each: quote the original, one sentence why it's weak, then rewritten version.

## 🚀 Do These 3 Things Before You Apply
Exactly 3 ranked actions, each doable in under a week."""


ROAST_PROMPT = """You are a comedy roast generator wearing a recruiter costume. Your job is to read a CV against a job description and DRAG IT FOR THE LAUGHS — like a friend who loves the candidate enough to be brutally funny about their CV.

This is FULL NUCLEAR roast mode. Your style guide:
- Punch up on the CV's weaknesses with comedy: bad bullets get jokes, weak quantification gets called out theatrically, missing JD requirements get sarcasm
- Use comparisons, metaphors, hyperbole — "this bullet is so vague it could apply to a sandwich"
- Quote the worst bullets verbatim and roast them line by line
- Compare gaps to absurd things — "the JD asks for Docker. Your CV mentions Docker the same way I mention exercising — wishfully and never in practice"
- Be observational and specific — generic insults aren't funny, specific ones are
- The candidate is your friend — punch up on bad writing, never punch down on identity or background
- Still give real feedback underneath the jokes — every roast must contain a real critique

ABSOLUTE RULES YOU CANNOT BREAK:
1. NEVER mock education credentials, university name, immigration status, country, name, gender, religion, age, or appearance
2. NEVER imply the candidate is stupid, incompetent at life, or hopeless — only that their CV writing needs work
3. Every roast must be SPECIFIC to something quoted from the CV — no generic "your CV is bad" jokes
4. The score must still be calibrated honestly even if the verdict line is comedic
5. The Action Items section must give REAL useful advice, only lightly dressed in humour

START with the score on its own line, EXACTLY:
SCORE: XX/100

Then format in Markdown with these EXACT headers:

## 🔥 The Verdict (Brutal Edition)
ONE comedic punchy sentence summarising the carnage. Be specific.

## 💀 Things The CV Did Right (Begrudgingly)
3-5 specific strengths from the CV that match the JD, framed with reluctant comedy ("okay, fine, this one's actually good...").

## ☠️ Where The CV Falls Apart
3-5 specific JD requirements the CV is missing or weak on. Roast the gap, but make the gap clear. Quote the JD requirement.

## 🎭 Bullets That Deserve a Public Reading
2-3 worst bullets in the CV. For each:
- Quote the bullet exactly in double quotation marks
- Roast it specifically (one or two lines of comedy)
- Then provide a rewritten version that actually slaps

## 🚀 Three Things, Do Them This Week
Exactly 3 ranked actions. Real advice. Lightly comedic delivery. Each must be doable in under a week."""


def analyze_cv_with_groq(cv_text: str, jd_text: str, mode: str) -> str:
    system_prompt = ROAST_PROMPT if "Roast" in mode else HONEST_PROMPT
    temperature = 0.7 if "Roast" in mode else 0.4
    
    user_prompt = f"""## Candidate's CV

{cv_text}

## Target Job Description

{jd_text}

Review this CV against the JD. Be specific, quote directly, follow the format exactly."""

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature,
        max_tokens=2800
    )
    return response.choices[0].message.content


def extract_score(text: str):
    match = re.search(r"SCORE:\s*(\d{1,3})\s*/\s*100", text)
    if match:
        s = int(match.group(1))
        if 0 <= s <= 100:
            return s
    match = re.search(r"(\d{1,3})\s*/\s*100", text)
    if match:
        s = int(match.group(1))
        if 0 <= s <= 100:
            return s
    return None


def get_verdict_data(score: int, is_roast: bool):
    """Returns (colour_hex, verdict_text, flavour_text) for a given score and mode."""
    if is_roast:
        if score >= 90:
            return "#22c55e", "Stop showing off.", "This CV barely needs a roast. Submit it before someone catches on."
        elif score >= 80:
            return "#0ea5e9", "Annoyingly competent.", "Strong alignment. Hard to roast. Disappointing for me, great for you."
        elif score >= 70:
            return "#38bdf8", "Mid, but in a good way.", "You'll get past the screen. Still some bullets I'd burn down for sport."
        elif score >= 60:
            return "#eab308", "Workable. Barely.", "Real match here, but the gaps are louder than the strengths."
        elif score >= 50:
            return "#f97316", "We need to talk.", "Half the JD ignored you back. Fix the gaps or pick a different role."
        else:
            return "#ef4444", "Friend... no.", "This is not the role. Either re-target hard, or rebuild parts of the CV from scratch."
    else:
        if score >= 90:
            return "#22c55e", "Apply right now.", "Cleanest match I've seen all day."
        elif score >= 80:
            return "#0ea5e9", "Press send.", "Strong alignment. Small gaps you can address in a cover letter."
        elif score >= 70:
            return "#38bdf8", "Pretty solid.", "You'll get past the screen. Sharpen the bullets before submitting."
        elif score >= 60:
            return "#eab308", "Workable.", "Real match, but the gaps are doing heavy lifting against you."
        elif score >= 50:
            return "#f97316", "Needs surgery.", "Half the boxes are checked. Address the gaps or expect a polite no."
        else:
            return "#ef4444", "Wrong fit.", "This role probably isn't the one. Re-target or rebuild parts of the CV."


def render_score_gauge(score: int, is_roast: bool):
    colour, verdict, flavour = get_verdict_data(score, is_roast)
    
    circ = 565
    offset = circ - (score / 100) * circ
    label = "🔥 Roast Score" if is_roast else "🎯 Match Score"
    
    html = f"""
    <div class="vibe-check">
        <div class="vibe-label-top">{label}</div>
        <div style="position: relative; width: 200px; height: 200px; margin: 0 auto;">
            <svg width="200" height="200" viewBox="0 0 200 200">
                <circle cx="100" cy="100" r="90" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="14"/>
                <circle cx="100" cy="100" r="90" fill="none" stroke="{colour}" stroke-width="14"
                    stroke-linecap="round"
                    stroke-dasharray="{circ}"
                    stroke-dashoffset="{circ}"
                    transform="rotate(-90 100 100)"
                    style="animation: draw 1.5s ease-out forwards; filter: drop-shadow(0 0 12px {colour}55);"/>
            </svg>
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -55%); font-size: 3.5rem; font-weight: 700; color: {colour};">{score}</div>
            <div style="position: absolute; top: calc(50% + 28px); left: 50%; transform: translateX(-50%); font-size: 0.72rem; color: #64748b; font-family: 'JetBrains Mono', monospace;">/ 100</div>
        </div>
        <div class="vibe-verdict" style="color: {colour};">"{verdict}"</div>
        <div class="vibe-flavour">{flavour}</div>
        <style>
            @keyframes draw {{ to {{ stroke-dashoffset: {offset}; }} }}
        </style>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def strip_score_line(text: str) -> str:
    return re.sub(r"^SCORE:\s*\d{1,3}\s*/\s*100\s*\n?", "", text).strip()


# === PDF GENERATION ===

def strip_emoji(text: str) -> str:
    """Remove all emoji and other pictographic characters from text."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # geometric shapes extended
        "\U0001F800-\U0001F8FF"  # supplemental arrows-c
        "\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
        "\U00002600-\U000026FF"  # miscellaneous symbols
        "\U00002700-\U000027BF"  # dingbats
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002B00-\U00002BFF"  # arrows
        "\U0000FE00-\U0000FE0F"  # variation selectors
        "\U0001F100-\U0001F1FF"  # enclosed alphanumeric supplement
        "]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub("", text)
    # Clean up double spaces left behind after emoji removal
    text = re.sub(r"  +", " ", text)
    return text.strip()


def clean_markdown_for_pdf(text: str) -> str:
    """Convert basic Markdown formatting to reportlab-compatible inline tags, strip emojis."""
    # Strip emojis first
    text = strip_emoji(text)
    # Bold: **text** → <b>text</b>
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Italic: *text* → <i>text</i> (but not **)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<i>\1</i>", text)
    return text


def detect_jd_label(jd_text: str) -> str:
    """If the JD matches one of the samples, return its label. Otherwise 'Custom JD'."""
    for sample in SAMPLE_JDS:
        if jd_text.strip() == sample["text"].strip():
            return sample["label"]
    return "Custom JD"


def generate_pdf(analysis_text: str, score: int, is_roast: bool, jd_text: str) -> bytes:
    """Generate a styled PDF report and return it as bytes."""
    
    buffer = BytesIO()
    
    # Document with custom margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18*mm,
        rightMargin=18*mm,
        topMargin=20*mm,
        bottomMargin=20*mm,
        title="Resume Reality Check — Analysis Report",
        author="Resume Reality Check"
    )
    
    # === STYLES ===
    styles = getSampleStyleSheet()
    
    # Brand colours
    accent_cyan = HexColor("#0ea5e9")
    accent_dark = HexColor("#0f172a")
    text_grey = HexColor("#334155")
    text_light = HexColor("#64748b")
    bg_light = HexColor("#f8fafc")
    
    colour_hex, verdict, flavour = get_verdict_data(score, is_roast)
    score_colour = HexColor(colour_hex)
    
    # Custom styles
    style_title = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        textColor=accent_dark,
        spaceAfter=6,
        alignment=TA_LEFT,
    )
    
    style_subtitle = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=text_light,
        spaceAfter=12,
        alignment=TA_LEFT,
    )
    
    style_meta = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=text_light,
        leading=14,
    )
    
    style_score_label = ParagraphStyle(
        "ScoreLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=text_light,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    
    style_score_number = ParagraphStyle(
        "ScoreNumber",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=56,
        textColor=score_colour,
        alignment=TA_CENTER,
        leading=60,
    )
    
    style_score_verdict = ParagraphStyle(
        "ScoreVerdict",
        parent=styles["Normal"],
        fontName="Helvetica-BoldOblique",
        fontSize=14,
        textColor=score_colour,
        alignment=TA_CENTER,
        spaceAfter=4,
        spaceBefore=8,
    )
    
    style_score_flavour = ParagraphStyle(
        "ScoreFlavour",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=text_grey,
        alignment=TA_CENTER,
        spaceAfter=10,
        leading=14,
    )
    
    style_h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=accent_dark,
        spaceBefore=16,
        spaceAfter=8,
        leading=18,
        borderColor=accent_cyan,
        borderPadding=(4, 8, 4, 8),
        leftIndent=0,
    )
    
    style_body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=text_grey,
        leading=15,
        spaceAfter=6,
    )
    
    style_bullet = ParagraphStyle(
        "Bullet",
        parent=style_body,
        leftIndent=14,
        bulletIndent=4,
        spaceAfter=4,
    )
    
    style_footer = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        textColor=text_light,
        alignment=TA_CENTER,
    )
    
    # === BUILD PDF ===
    story = []
    
# --- HEADER BAR ---
    mode_label = "Roast Mode" if is_roast else "Honest Feedback"
    date_str = datetime.now().strftime("%d %B %Y")
    jd_label = detect_jd_label(jd_text)
    
    story.append(Paragraph("Resume Reality Check", style_title))
    story.append(Paragraph("AI-powered CV analysis report", style_subtitle))
    
    # Metadata table — three columns
    meta_data = [
        [
            Paragraph(f"<b>Mode</b><br/>{mode_label}", style_meta),
            Paragraph(f"<b>Date</b><br/>{date_str}", style_meta),
            Paragraph(f"<b>Target Role</b><br/>{jd_label}", style_meta),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[55*mm, 45*mm, 70*mm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_light),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 16))
    
    # --- SCORE BLOCK ---
    score_data = [
        [Paragraph("MATCH SCORE", style_score_label)],
        [Paragraph(f"{score} / 100", style_score_number)],
        [Paragraph(f'"{verdict}"', style_score_verdict)],
        [Paragraph(flavour, style_score_flavour)],
    ]
    score_table = Table(score_data, colWidths=[174*mm])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_light),
        ("BOX", (0, 0), (-1, -1), 1, score_colour),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (0, 0), 16),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 16),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 20))
    
    # --- ANALYSIS BODY ---
    # Split the analysis into sections by H2 markers, render each
    lines = analysis_text.split("\n")
    current_paragraph_lines = []
    
    def flush_paragraph():
        nonlocal current_paragraph_lines
        if current_paragraph_lines:
            text = " ".join(current_paragraph_lines).strip()
            if text:
                story.append(Paragraph(clean_markdown_for_pdf(text), style_body))
            current_paragraph_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith("## "):
            # Section header — strip emoji from heading text too
            flush_paragraph()
            heading_text = strip_emoji(stripped[3:].strip())
            story.append(Spacer(1, 6))
            # Wrap heading in a styled table to get the cyan left border
            heading_table = Table(
                [[Paragraph(f"<b>{heading_text}</b>", ParagraphStyle(
                    "HeadingInner", parent=style_h2, fontSize=13, leading=16, textColor=accent_dark
                ))]],
                colWidths=[174*mm]
            )
            heading_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), bg_light),
                ("LINEBEFORE", (0, 0), (0, -1), 3, accent_cyan),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(heading_table)
            story.append(Spacer(1, 8))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            # Bullet point
            flush_paragraph()
            bullet_text = stripped[2:].strip()
            story.append(Paragraph(
                f"• {clean_markdown_for_pdf(bullet_text)}",
                style_bullet
            ))
        elif re.match(r"^\d+\.\s", stripped):
            # Numbered list item
            flush_paragraph()
            story.append(Paragraph(
                clean_markdown_for_pdf(stripped),
                style_bullet
            ))
        elif stripped == "":
            # Blank line — flush current paragraph
            flush_paragraph()
        else:
            # Regular text — accumulate
            current_paragraph_lines.append(stripped)
    
    flush_paragraph()
    
    # --- FOOTER ---
    story.append(Spacer(1, 30))
    story.append(Paragraph(
        "Generated by Resume Reality Check · github.com/Som0501/ai-resume-reviewer",
        style_footer
    ))
    
    # Build the PDF
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


# === MAIN LOGIC ===

if analyze_clicked:
    is_valid, error_msg = validate_inputs(uploaded_cv, job_description)
    if not is_valid:
        st.error(f"🙃  {error_msg}")
    else:
        try:
            is_roast = "Roast" in mode
            loading_pool = LOADING_MESSAGES_ROAST if is_roast else LOADING_MESSAGES_HONEST
            loading_msg = random.choice(loading_pool)
            
            with st.spinner("📄  Reading your CV..."):
                cv_text = extract_text_from_pdf(uploaded_cv)
            
            if len(cv_text) < MIN_CV_CHARS:
                st.error("❌  Couldn't extract text from this PDF. It might be scanned — re-export from Word/LaTeX as a real PDF.")
                st.stop()
            
            with st.spinner(f"🤖  {loading_msg}"):
                analysis = analyze_cv_with_groq(cv_text, job_description, mode)
            
            score = extract_score(analysis)
            if score is not None:
                render_score_gauge(score, is_roast)
                analysis_body = strip_score_line(analysis)
            else:
                # Fallback if score parsing fails — assign 50 so PDF still works
                score = 50
                analysis_body = analysis
            
            st.markdown(analysis_body)
            
            st.write("")
            
            # Generate PDF
            try:
                pdf_bytes = generate_pdf(analysis_body, score, is_roast, job_description)
                date_str = datetime.now().strftime("%Y-%m-%d")
                filename = f"cv_roast_{date_str}.pdf" if is_roast else f"cv_reality_check_{date_str}.pdf"
                
                st.download_button(
                    label="📄  Download PDF Report",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as pdf_err:
                st.warning(f"⚠️  PDF generation hit an issue: {str(pdf_err)}. Showing analysis above is still complete.")
            
        except Exception as e:
            st.error(f"❌  Something went wrong: {str(e)}")


# === FOOTER ===

st.markdown("""
<div class="made-by-footer">
    Made with caffeine and existential career anxiety by 
    <a href="https://github.com/Som0501" target="_blank">Som Kapoor</a> · 
    <a href="https://github.com/Som0501/ai-resume-reviewer" target="_blank">View source</a>
</div>
""", unsafe_allow_html=True)