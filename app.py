import os
import streamlit as st
from pypdf import PdfReader
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env file
load_dotenv()

# Initialise the Groq client with our API key
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- PAGE SETUP ---

st.set_page_config(
    page_title="AI Resume Reviewer",
    page_icon="📄",
    layout="centered"
)

st.title("📄 AI Resume Reviewer")
st.write("Upload your CV and paste a job description. Get an honest, AI-powered review.")

st.divider()

# --- INPUT SECTION ---

st.subheader("1. Upload your CV")
uploaded_cv = st.file_uploader(
    "PDF only, max 5 MB",
    type=["pdf"],
    accept_multiple_files=False
)

st.subheader("2. Paste the job description")
job_description = st.text_area(
    "Copy the JD from LinkedIn, Naukri, or the company's careers page",
    height=200,
    placeholder="Paste the full job description here..."
)

st.subheader("3. Get your review")
analyze_clicked = st.button("🔍 Analyze my CV", type="primary", use_container_width=True)

st.divider()

# --- HELPER FUNCTIONS ---

def extract_text_from_pdf(pdf_file):
    """Read a PDF file object and return all its text as one string."""
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()


def analyze_cv_with_groq(cv_text: str, jd_text: str) -> str:
    """Send the CV and JD to Groq's LLM and return the analysis."""
    
    system_prompt = """You are an experienced technical recruiter and career coach 
who has reviewed thousands of CVs. Your job is to give honest, specific, actionable 
feedback on how well a candidate's CV matches a specific job description.

Be direct but constructive. Don't sugar-coat — if the candidate is missing critical 
skills, say so. If their CV has weak bullet points, point them out specifically.

Format your response in clear Markdown sections with these exact headers:

## 📊 Overall Match Score
Give a score out of 100 with one sentence explaining the rating.

## ✅ Strengths
List 3-5 specific things from the CV that match the job description well.

## ⚠️ Gaps & Missing Skills
List the most important skills, experiences, or qualifications from the JD that 
are missing or weak in the CV.

## ✏️ Bullet Points to Rewrite
Pick 2-3 weak bullet points from the CV (quote them exactly), then rewrite each 
one to be stronger and more aligned with the job description. Use action verbs 
and quantifiable outcomes where possible.

## 🎯 Top 3 Action Items
The three most important things this candidate should do before applying."""

    user_prompt = f"""Here is the candidate's CV:

---
{cv_text}
---

Here is the job description they want to apply for:

---
{jd_text}
---

Please analyse the CV against this job description following the format in your instructions."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,  # Lower = more focused, less creative
        max_tokens=2000
    )
    
    return response.choices[0].message.content


# --- MAIN LOGIC ---

if analyze_clicked:
    if uploaded_cv is None:
        st.error("⚠️ Please upload your CV first.")
    elif not job_description.strip():
        st.error("⚠️ Please paste a job description.")
    else:
        try:
            with st.spinner("📄 Reading your CV..."):
                cv_text = extract_text_from_pdf(uploaded_cv)
            
            with st.spinner("🤖 AI is reviewing your CV... (this takes 10-20 seconds)"):
                analysis = analyze_cv_with_groq(cv_text, job_description)
            
            st.success("✅ Analysis complete!")
            st.markdown(analysis)
            
            # Download button for the analysis
            st.download_button(
                label="⬇️ Download analysis as text",
                data=analysis,
                file_name="cv_analysis.md",
                mime="text/markdown"
            )
            
        except Exception as e:
            st.error(f"❌ Something went wrong: {str(e)}")
            st.info("If you see an authentication error, check that your GROQ_API_KEY is set correctly in the .env file.")