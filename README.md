# 🎯 Resume Reality Check

> An AI-powered CV reviewer that gives honest, structured feedback on your resume against any job description. Two modes — pick your poison.

**🌐 [Live demo →](https://resume-reality-check.streamlit.app)**

---

## What it does

Upload your CV (PDF). Paste a job description. Pick a mode. Get a structured, evidence-based review in ~15 seconds.

The model is prompted to behave like a senior recruiter who has read 10,000+ CVs — specific, evidence-based, no platitudes. Every weak bullet gets quoted from your CV and rewritten. Every JD requirement that's missing gets flagged with the exact JD line referenced.

### Two modes

| Mode | Tone | When to use |
|---|---|---|
| **💬 Honest Feedback** | Constructive, specific, slightly dry. Recruiter-energy. | Before applying — get real, actionable feedback |
| **🔥 Roast Me** | Full nuclear comedy roast. Friend-energy. | When you want to laugh while learning what's wrong |

Both modes return the same structure: match score, strengths, gaps, bullet rewrites, and ranked action items. Roast mode just makes you laugh on the way down.

---

## Output structure

Every analysis returns:

1. **Match Score / 100** — colour-coded animated gauge with a verdict line
2. **The Verdict** — one-sentence rationale for the score
3. **What's Working / Things The CV Did Right** — 3–5 strengths mapped to specific JD requirements
4. **Where The Gaps Are / Where The CV Falls Apart** — 3–5 missing requirements, each quoting the JD
5. **Bullets That Need Work** — 2–3 weakest bullets quoted verbatim, then rewritten with strong verbs and metrics
6. **Action Items Before Applying** — exactly 3 ranked, specific actions, each doable in under a week

The full analysis can also be downloaded as a styled **PDF report** with metadata (mode, date, target role) at the top.

---

## Tech stack

- **Frontend & app framework:** [Streamlit](https://streamlit.io) (Python)
- **LLM:** [Llama 3.3 70B](https://ai.meta.com/blog/meta-llama-3-3/) via [Groq](https://groq.com)'s free inference API
- **PDF parsing:** [pypdf](https://pypdf.readthedocs.io)
- **PDF generation:** [ReportLab](https://www.reportlab.com)
- **Secrets:** `python-dotenv` locally, Streamlit Cloud Secrets in production
- **Hosting:** Streamlit Community Cloud (free tier)

### Why this stack

- **Groq + Llama 3.3 70B** gives strong reasoning at ~10× the speed of equivalent paid APIs, on a generous free tier (14,400 requests/day). No cost to operate.
- **Streamlit** trades some design flexibility for a 3-line UI → 1-line deploy story. Right tradeoff for a portfolio project — let me focus on the prompting and product, not the build pipeline.
- **ReportLab** has zero system dependencies (no headless Chrome, no LaTeX), so PDF generation works on Streamlit Cloud's locked-down build environment with no extra config.

---

## Key implementation details

### Prompt engineering

Two distinct system prompts (in `app.py`):

- **`HONEST_PROMPT`** enforces specificity rules: every claim must quote the CV or JD, no generic advice, calibrated score bands.
- **`ROAST_PROMPT`** lets the model be funny, but with explicit constraints — it can roast the *CV writing*, never the candidate's identity, credentials, or background.

Both prompts force a strict Markdown output format with fixed section headers, which makes the response reliably parseable for the score gauge and PDF generation.

### Score extraction

The LLM is instructed to emit `SCORE: XX/100` on its own line at the start of every response. A regex pulls this out, drives the animated gauge colour-coding, and then strips the line from the body before rendering.

### Cycling sample JDs

Six pre-written JDs covering different role types (Junior ML Engineer, CV Engineer, Data Scientist, GenAI Engineer, SDE-1, AI Research Intern). The "🎲 Sample" button cycles through them via `st.session_state`, with a badge showing which sample is currently loaded.

### Streamlit branding removed

Custom CSS hides the default Streamlit footer, menu, and "Made with" badge to give the app a portfolio-product feel rather than a demo feel.

---

## Run locally

```bash
# Clone the repo
git clone https://github.com/Som0501/ai-resume-reviewer.git
cd ai-resume-reviewer

# Install dependencies
pip install -r requirements.txt

# Add your Groq API key to a .env file
echo 'GROQ_API_KEY="your_groq_key_here"' > .env

# Run
streamlit run app.py
```

Get a free Groq API key at [console.groq.com](https://console.groq.com).

---

## Project structure
The whole app is one file. Intentional — fewer moving parts, easier to read for someone landing on the repo, no premature abstraction. If this grew (auth, persistence, multi-page), I'd split it.

---

## What I'd add next

If this were a product instead of a portfolio project:
- **Caching** — Streamlit's `@st.cache_data` on the LLM call to handle the same CV+JD pair without re-billing
- **Auth + persistent history** — log in, see past analyses, track score progression as the CV improves
- **Multi-CV comparison** — upload 2–3 CV versions side by side against the same JD
- **JD scraper** — paste a LinkedIn or Naukri URL instead of the JD text, scrape it server-side

These are all 1-2 day additions. Skipped for now because the goal was a focused demo, not a SaaS.

---

## About

Built by **[Som Kapoor](https://github.com/Som0501)** — AI practitioner specialising in deep learning and computer vision. Other projects on the [profile](https://github.com/Som0501).

If you found this useful or have feedback, feel free to open an issue or reach out.

---

## License

MIT — see [LICENSE](./LICENSE).