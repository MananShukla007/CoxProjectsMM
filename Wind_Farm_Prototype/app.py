import streamlit as st
from openai import OpenAI
import pdfplumber
from fpdf import FPDF
import time
from datetime import datetime
import os

# =========================================================
# =========================================================
OPENAI_KEY = ""  # <-- replace with your real key

# =========================================================
# App Config
# =========================================================
st.set_page_config(
    page_title="Delta Wind Farm • Sarah PM Bot",
    page_icon="🌬️",
    layout="wide",
)

# =========================================================
# Theme
# =========================================================
SMU_BLUE = "#0033A0"
ACCENT = "#2F6BFF"
BG = "#F4F7FF"
TEXT = "#0F172A"
MUTED = "#475569"

# =========================================================
# =========================================================
st.markdown(
    f"""
<style>
  /* App background */
  .stApp {{
    background: radial-gradient(1200px 600px at 20% 0%, #EAF0FF 0%, {BG} 55%, #F7FAFF 100%);
    color: {TEXT};
  }}

  /* DO NOT lock html/body to overflow hidden (this causes blank pages on Streamlit Cloud) */
  html, body {{
    height: 100%;
    overflow: auto !important;
  }}

  /* Lock Streamlit view container safely */
  div[data-testid="stAppViewContainer"] {{
    height: 100vh;
    overflow: hidden;
  }}

  /* Main block container */
  div[data-testid="stMainBlockContainer"] {{
    padding-top: 0.9rem;
    padding-bottom: 0.8rem;
    height: 100vh;
    overflow: hidden;
  }}

  /* Pane shells */
  .pane {{
    border: 1px solid rgba(0,0,0,0.06);
    background: linear-gradient(180deg, rgba(255,255,255,0.88) 0%, rgba(255,255,255,0.96) 100%);
    border-radius: 18px;
    box-shadow:
      0 10px 30px rgba(0, 18, 70, 0.10),
      0 2px 10px rgba(0, 18, 70, 0.06);
    height: calc(100vh - 2.2rem);
    overflow: hidden;
    position: relative;
    backdrop-filter: blur(8px);
  }}

  .pane-header {{
    padding: 14px 14px 12px 14px;
    border-bottom: 1px solid rgba(0,0,0,0.06);
    background: linear-gradient(90deg, rgba(0,51,160,0.10), rgba(47,107,255,0.06));
  }}

  .pane-body {{
    padding: 12px 14px;
    height: calc(100% - 58px);
    overflow-y: auto;
  }}

  /* Buttons */
  button[kind="primary"] {{
    background: linear-gradient(90deg, {SMU_BLUE}, {ACCENT}) !important;
    color: white !important;
    border: 0 !important;
    box-shadow: 0 12px 24px rgba(0,51,160,0.20);
  }}

  /* Notes / Cards */
  .note {{
    padding: 10px 12px;
    border-radius: 14px;
    border: 1px solid rgba(0,0,0,0.06);
    background: rgba(248,250,255,0.85);
    box-shadow: 0 8px 18px rgba(0, 18, 70, 0.05);
    white-space: pre-wrap;
  }}

  .muted {{
    color: {MUTED};
    font-size: 0.92rem;
  }}

  /* Chat */
  .chat-wrap {{
    display: flex;
    flex-direction: column;
    height: 100%;
  }}

  .chat-scroll {{
    height: calc(100% - 132px);
    overflow-y: auto;
    padding: 14px 14px;
  }}

  .bubble {{
    max-width: 82%;
    padding: 10px 12px;
    border-radius: 16px;
    margin: 8px 0;
    border: 1px solid rgba(0,0,0,0.06);
    box-shadow: 0 10px 24px rgba(0, 18, 70, 0.06);
    background: rgba(255,255,255,0.94);
    line-height: 1.35;
    white-space: pre-wrap;
  }}
  .bubble.user {{
    margin-left: auto;
    background: linear-gradient(180deg, rgba(47,107,255,0.14), rgba(255,255,255,0.96));
    border-color: rgba(47,107,255,0.18);
  }}
  .bubble.assistant {{
    margin-right: auto;
  }}

  .chat-inputbar {{
    border-top: 1px solid rgba(0,0,0,0.06);
    padding: 12px 14px;
    background: linear-gradient(180deg, rgba(255,255,255,0.65), rgba(255,255,255,0.95));
  }}

  .section-title {{
    font-weight: 900;
    margin: 6px 0 8px 0;
  }}
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# OpenAI client + retry wrapper
# =========================================================
def make_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key, timeout=45.0, max_retries=3)

def call_chat_completion(client: OpenAI, *, model: str, messages):
    last_err = None
    for attempt in range(1, 4):
        try:
            return client.chat.completions.create(model=model, messages=messages)
        except Exception as e:
            last_err = e
            time.sleep(0.6 * (2 ** (attempt - 1)))
    raise last_err

def friendly_connection_help(err: Exception) -> str:
    msg = str(err) or err.__class__.__name__
    return (
        "OpenAI API connection failed.\n\n"
        "Try:\n"
        "• Check internet\n"
        "• Disable VPN temporarily\n"
        "• Update SDK: `pip install -U openai`\n\n"
        f"Details: {msg}"
    )

# =========================================================
# Fixed Case Study Loader
# =========================================================
def load_case_text() -> str:
    """
    Looks for the PDF in common deploy locations:
    1) same folder as app.py
    2) ./data/
    3) /mnt/data/ (this environment)
    """
    candidates = [
        "The Delta Wind Farm Project.pdf",
        os.path.join("data", "The Delta Wind Farm Project.pdf"),
        "/mnt/data/The Delta Wind Farm Project.pdf",
    ]

    for path in candidates:
        try:
            if os.path.exists(path):
                text = ""
                with pdfplumber.open(path) as pdf:
                    for page in pdf.pages:
                        text += (page.extract_text() or "") + "\n"
                text = text.strip()
                if text:
                    return text
        except Exception:
            continue

    # Fallback excerpt if PDF isn't found
    return (
        "The Delta Wind Farm Project (fallback excerpt)\n\n"
        "Sarah Chen, Project Manager for Delta Renewables, must replan Phase II to meet "
        "a June 30 investor milestone. Phase II adds 50 turbines across onshore and offshore workstreams "
        "with coupled risks (A6↔A8) and a regulatory paperwork gate that can cause a +5 day halt. "
        "Team must pick ONE acceleration option (S1–S5)."
    )

# =========================================================
# Sarah- prompts
# =========================================================
def sarah_system_prompt(case_text: str) -> str:
    return f"""
You are Sarah Chen, Project Manager for Delta Renewables (Delta Wind Farm Project Phase II).

RULES:
- Always speak as Sarah (PM).
- Be practical and structured.
- Keep answers short + decision-oriented.
- Ask 1–2 questions back to the student to make them think.
- Only use facts from the case. If missing, say what you’d need.

CASE STUDY:
{case_text}
"""

def insights_prompt(case_text: str) -> str:
    return f"""
Return concise, high-signal insights (bullets):
- Critical path / gating dependencies
- What June 30 actually constrains (inspection/report)
- Hidden risks (regulatory gate, A6↔A8 loop, weather, customs)
- Implications of "choose ONE crash option"

Use only case facts. No fluff.

CASE:
{case_text}
"""

def problems_prompt(case_text: str) -> str:
    return f"""
Create a clean list:
1) Problems (current issues/slips)
2) Risks (uncertainties)
3) Constraints (policy, milestone, dependencies)

Each item 1 line. Only case facts.

CASE:
{case_text}
"""

def what_i_do_prompt(case_text: str) -> str:
    return f"""
You are Sarah Chen (PM). Explain in 8–12 crisp bullet points:
- What your job is in THIS case
- What you're accountable for by June 30
- What decisions you must make (schedule, crash option, compliance)
- What you need from stakeholders (Construction, Procurement, Engineering, Finance, Regulatory, CEO)

Only case facts.

CASE:
{case_text}
"""

# =========================================================
# =========================================================
def export_chat_to_pdf(title: str, chat_history):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    safe_title = title.encode("latin-1", "replace").decode("latin-1")
    pdf.cell(0, 10, safe_title, ln=True, align="C")

    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
    pdf.ln(8)

    pdf.set_font("Arial", "", 11)
    for msg in chat_history:
        who = "You" if msg["role"] == "user" else "Sarah"
        who = who.encode("latin-1", "replace").decode("latin-1")

        pdf.set_font("Arial", "B", 11)
        pdf.multi_cell(0, 7, f"{who}:")
        pdf.set_font("Arial", "", 11)

        content = (msg.get("content") or "").encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 6, content)
        pdf.ln(3)

    return pdf.output(dest="S").encode("latin-1", errors="replace")

# =========================================================
# Session State
# =========================================================
if "client" not in st.session_state:
    st.session_state.client = None
if "case_text" not in st.session_state:
    st.session_state.case_text = ""
if "view" not in st.session_state:
    st.session_state.view = "chat"  # chat | insights | problems | role
if "chat" not in st.session_state:
    st.session_state.chat = []
if "insights" not in st.session_state:
    st.session_state.insights = ""
if "problems" not in st.session_state:
    st.session_state.problems = ""
if "role_info" not in st.session_state:
    st.session_state.role_info = ""
if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None
if "pdf_filename" not in st.session_state:
    st.session_state.pdf_filename = ""

def reset_app():
    st.session_state.view = "chat"
    st.session_state.chat = []
    st.session_state.insights = ""
    st.session_state.problems = ""
    st.session_state.role_info = ""
    st.session_state.pdf_data = None
    st.session_state.pdf_filename = ""

# =========================================================
# Boot
# =========================================================
if not st.session_state.case_text:
    st.session_state.case_text = load_case_text()

key_ready = bool(OPENAI_KEY and OPENAI_KEY != "1234")
if st.session_state.client is None and key_ready:
    st.session_state.client = make_client(OPENAI_KEY)

# =========================================================
# 3-Pane Layout
# =========================================================
left, center, right = st.columns([1.05, 2.55, 1.20], gap="large")

# ---------------- LEFT PANE ----------------
with left:
    st.markdown("<div class='pane'>", unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="pane-header">
  <div style="display:flex;align-items:center;gap:10px;">
    <div style="width:34px;height:34px;border-radius:12px;background:linear-gradient(180deg,{SMU_BLUE},{ACCENT});
                display:flex;align-items:center;justify-content:center;color:white;font-weight:900;">🌬️</div>
    <div>
      <div style="font-weight:900;">Delta Wind Farm Bot</div>
      <div class="muted">You are Sarah (PM)</div>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='pane-body'>", unsafe_allow_html=True)

    if not key_ready:
        st.warning("OPENAI_KEY is still '1234'. Replace it in code to enable AI buttons.")
    else:
        st.success("OpenAI key loaded from code ✅")

    st.divider()

    st.markdown("**Navigation**")
    if st.button("💬 Chat (as Sarah)", use_container_width=True, type=("primary" if st.session_state.view == "chat" else "secondary")):
        st.session_state.view = "chat"
        st.rerun()

    if st.button("💡 Insights", use_container_width=True, type=("primary" if st.session_state.view == "insights" else "secondary")):
        st.session_state.view = "insights"
        st.rerun()

    if st.button("⚠️ Problems & Risks", use_container_width=True, type=("primary" if st.session_state.view == "problems" else "secondary")):
        st.session_state.view = "problems"
        st.rerun()

    if st.button("🧑‍💼 What's your role / what do you do?", use_container_width=True, type=("primary" if st.session_state.view == "role" else "secondary")):
        st.session_state.view = "role"
        st.rerun()

    st.divider()

    c1, c2 = st.columns(2)
    if c1.button("Reset", use_container_width=True):
        reset_app()
        st.rerun()

    export_disabled = not bool(st.session_state.chat)
    if c2.button("Export PDF", use_container_width=True, disabled=export_disabled):
        pdf_bytes = export_chat_to_pdf("Chat with Sarah (Delta Wind Farm)", st.session_state.chat)
        st.session_state.pdf_data = pdf_bytes
        st.session_state.pdf_filename = f"delta_windfarm_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    if st.session_state.pdf_data:
        st.download_button(
            label="Download PDF",
            data=st.session_state.pdf_data,
            file_name=st.session_state.pdf_filename,
            mime="application/pdf",
            use_container_width=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- RIGHT PANE ----------------
with right:
    st.markdown("<div class='pane'>", unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="pane-header">
  <div style="display:flex;align-items:center;gap:10px;">
    <div style="width:34px;height:34px;border-radius:12px;background:linear-gradient(180deg,#0B2B6F,{ACCENT});
                display:flex;align-items:center;justify-content:center;color:white;font-weight:900;">🧾</div>
    <div>
      <div style="font-weight:900;">Case Context</div>
      <div class="muted">Scrollable reference</div>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='pane-body'>", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>Quick reminders</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='note'>• Investor milestone due: June 30\n"
        "• One crash option only (S1–S5)\n"
        "• Regulatory paperwork gate can cause +5 day halt\n"
        "• A6↔A8 rework loop exists\n"
        "• Offshore weather window variability</div>",
        unsafe_allow_html=True,
    )

    st.write("")
    st.markdown("<div class='section-title'>Case text (scroll)</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='note' style='max-height:560px; overflow-y:auto;'>{st.session_state.case_text}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- CENTER PANE ----------------
with center:
    st.markdown("<div class='pane'>", unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="pane-header">
  <div style="display:flex;align-items:center;justify-content:space-between;">
    <div style="display:flex;align-items:center;gap:10px;">
      <div style="width:34px;height:34px;border-radius:12px;background:linear-gradient(180deg,{SMU_BLUE},{ACCENT});
                  display:flex;align-items:center;justify-content:center;color:white;font-weight:900;">💬</div>
      <div>
        <div style="font-weight:900;">Sarah Chen • Project Manager</div>
        <div class="muted">Center pane scrolls • page stays fixed</div>
      </div>
    </div>
    <div class="muted">{st.session_state.view.upper()}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='pane-body chat-wrap'>", unsafe_allow_html=True)

    client = st.session_state.client
    case_text = st.session_state.case_text
    ai_disabled = (not key_ready) or (client is None)

    # ---------- INSIGHTS ----------
    if st.session_state.view == "insights":
        st.markdown("<div class='section-title'>Insights</div>", unsafe_allow_html=True)

        if not st.session_state.insights:
            if st.button("Generate Insights", type="primary", use_container_width=True, disabled=ai_disabled):
                try:
                    with st.spinner("Generating insights…"):
                        resp = call_chat_completion(
                            client,
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "You produce crisp, decision-useful analysis."},
                                {"role": "user", "content": insights_prompt(case_text)},
                            ],
                        )
                        st.session_state.insights = resp.choices[0].message.content.strip()
                        st.rerun()
                except Exception as e:
                    st.error("Error: Connection error.")
                    st.caption(friendly_connection_help(e))
            if ai_disabled:
                st.info("Replace OPENAI_KEY in code to enable this button.")
        else:
            st.markdown(f"<div class='note'>{st.session_state.insights}</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    # ---------- PROBLEMS ----------
    if st.session_state.view == "problems":
        st.markdown("<div class='section-title'>Problems & Risks</div>", unsafe_allow_html=True)

        if not st.session_state.problems:
            if st.button("Generate Problems & Risks", type="primary", use_container_width=True, disabled=ai_disabled):
                try:
                    with st.spinner("Generating…"):
                        resp = call_chat_completion(
                            client,
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "You produce crisp, structured lists."},
                                {"role": "user", "content": problems_prompt(case_text)},
                            ],
                        )
                        st.session_state.problems = resp.choices[0].message.content.strip()
                        st.rerun()
                except Exception as e:
                    st.error("Error: Connection error.")
                    st.caption(friendly_connection_help(e))
            if ai_disabled:
                st.info("Replace OPENAI_KEY in code to enable this button.")
        else:
            st.markdown(f"<div class='note'>{st.session_state.problems}</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    # ---------- ROLE ----------
    if st.session_state.view == "role":
        st.markdown("<div class='section-title'>What Sarah Does (in this case)</div>", unsafe_allow_html=True)

        if not st.session_state.role_info:
            if st.button("Show Sarah’s Role", type="primary", use_container_width=True, disabled=ai_disabled):
                try:
                    with st.spinner("Writing Sarah’s role summary…"):
                        resp = call_chat_completion(
                            client,
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "Be concise and specific to the case."},
                                {"role": "user", "content": what_i_do_prompt(case_text)},
                            ],
                        )
                        st.session_state.role_info = resp.choices[0].message.content.strip()
                        st.rerun()
                except Exception as e:
                    st.error("Error: Connection error.")
                    st.caption(friendly_connection_help(e))
            if ai_disabled:
                st.info("Replace OPENAI_KEY in code to enable this button.")
        else:
            st.markdown(f"<div class='note'>{st.session_state.role_info}</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    # ---------- CHAT ----------
    st.markdown("<div class='chat-scroll'>", unsafe_allow_html=True)
    if not st.session_state.chat:
        st.markdown("<div class='muted'>Start: “Hi Sarah, what’s the situation and what’s blocking June 30?”</div>", unsafe_allow_html=True)
    else:
        for msg in st.session_state.chat:
            cls = "user" if msg["role"] == "user" else "assistant"
            st.markdown(f"<div class='bubble {cls}'>{msg.get('content','')}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='chat-inputbar'>", unsafe_allow_html=True)
    with st.form("chat_form", clear_on_submit=True):
        cols = st.columns([5.2, 1.0], gap="small")
        user_input = cols[0].text_input("Message", label_visibility="collapsed", placeholder="Ask Sarah…")
        send = cols[1].form_submit_button("Send", use_container_width=True, type="primary", disabled=ai_disabled)

        if send and user_input.strip():
            st.session_state.chat.append({"role": "user", "content": user_input.strip()})

            prompt = sarah_system_prompt(case_text)
            try:
                resp = call_chat_completion(
                    client,
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": prompt}] + st.session_state.chat,
                )
                reply = resp.choices[0].message.content.strip()
                st.session_state.chat.append({"role": "assistant", "content": reply})
                st.rerun()
            except Exception as e:
                st.error("Error: Connection error.")
                st.caption(friendly_connection_help(e))

    if ai_disabled:
        st.info("Replace OPENAI_KEY in code to enable chat.")

    st.markdown("</div>", unsafe_allow_html=True)  # inputbar
    st.markdown("</div>", unsafe_allow_html=True)  # pane-body
    st.markdown("</div>", unsafe_allow_html=True)  # pane
