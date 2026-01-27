import streamlit as st
from datetime import datetime
from openai import OpenAI

# Page config - MUST be first
st.set_page_config(page_title="Delta Wind Farm Project", page_icon="🎯", layout="wide", initial_sidebar_state="collapsed")

# OpenAI
OPENAI_KEY = ""
client = OpenAI(api_key=OPENAI_KEY)

# Session state
if 'active_agent' not in st.session_state:
    st.session_state.active_agent = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = {}
if 'phase' not in st.session_state:
    st.session_state.phase = 'investigation'

# Data
STAKEHOLDERS = {
    "sam": {"name": "Sam Patel", "title": "Construction Manager (Onshore)", "emoji": "👷"},
    "rita": {"name": "Rita Gomez", "title": "Procurement & Logistics", "emoji": "📦"},
    "maya": {"name": "Maya Li", "title": "Engineering Lead (Offshore)", "emoji": "⚙️"},
    "leo": {"name": "Leo Armstrong", "title": "Finance Director", "emoji": "💰"},
    "carlos": {"name": "Carlos Ruiz", "title": "Regulatory Compliance", "emoji": "📋"},
    "ava": {"name": "Ava Johnson", "title": "CEO / Sponsor", "emoji": "👔"},
}

GREETINGS = {
    "sam": "Hey Sarah, yeah, let me pull up the field logs. What do you need to know about onshore operations?",
    "rita": "Sarah, I know you're going to ask about the freight delays. Let me explain what's happening with the marine shipping situation...",
    "maya": "Sarah, glad you're here. Let me sketch this out - A6 and A8 are more coupled than your baseline plan shows. This is important.",
    "leo": "Sarah, I'll keep this brief. Here's what you need to understand about budget constraints and policy.",
    "carlos": "Sarah. Let's talk about compliance requirements and what could potentially halt your project.",
    "ava": "Sarah, I have about 10 minutes before my next meeting. Tell me you have a coherent plan that doesn't miss June 30."
}

CASE_STUDY = """DELTA WIND FARM - PHASE II: 50 turbines, June 30 HARD deadline (investor covenant)
Budget: $4.09M + $400k contingency | Delay: $3k/day | NO early savings

ACTIVITIES (O/M/P days): A1 Access:6/8/12(Sam) | A2 Platform:7/9/14(Maya) | A3 Foundation:10/12/16(Sam,BOTTLENECK) | A4 Install:8/11/17(Maya) | A5 Ship:6/8/10(Rita) | A6 Tower:8/10/15(Maya) | A7 Nacelle:7/9/12(Maya) | A8 Cable:10/13/18(Maya) | A9 Substation:8/10/13(Sam) | A10 Integration:6/8/11 | A11 Inspection:5/6/9(Carlos) | A12 Handover:2/3/5

DEPS: A1→A3, A2→A4, A3&A2→A4, A4&A5→A6, A6→A7&A8, A8&A9→A10→A11→A12
RISKS: A6↔A8 coupling (30% rework +4d) | Regulatory gate (+5d halt if not cleared before A6/A8)
CRASH (ONE only): S1:A3-3d$70k | S2:A5-4d$110k | S3:A6-5d$150k | S4:A8-4d$130k | S5:A9-3d$60k"""

ROLE_PROMPTS = {
    "sam": "You are Sam Patel, Construction Manager. Handle A1(6/8/12d), A3(10/12/16d-BOTTLENECK), A9(8/10/13d). Offer S1: 2nd batch for A3(-3d,$70k). Deps: A1→A3→A4.",
    "rita": "You are Rita Gomez, Procurement. Handle A5(6/8/10d). Offer S2: faster cargo(-4d,$110k). A5 gates A6.",
    "maya": "You are Maya Li, Offshore Eng. Handle A2,A4,A6,A7,A8. CRITICAL: A6↔A8 30% rework(+4d). Offer S3: 2nd crane A6(-5d,$150k) or S4: ROV A8(-4d,$130k).",
    "leo": "You are Leo Armstrong, Finance. Budget $4.09M+$400k. Delay $3k/day. NO early savings. Rule: ONE crash only.",
    "carlos": "You are Carlos Ruiz, Compliance. Handle A11(5/6/9d). CRITICAL: paperwork before A6/A8 or +5d halt. Clear parallel with A1/A2.",
    "ava": "You are Ava Johnson, CEO. June 30 NON-NEGOTIABLE. Want: network, PERT date, ONE crash, risk plan, memo."
}

OBJECTIVES = {
    'investigation': ['🔍 Interview all 6 stakeholders', '🔗 Identify dependencies (A1-A12)', '💰 Understand budget/timeline constraints', '📊 Collect three-point estimates', '⚠️ Discover A6↔A8 coupling risk', '📋 Learn regulatory paperwork gate'],
    'analysis': ['📈 Build network diagram', '🧮 Calculate PERT durations', '🎯 Identify critical path', '🔄 Model A6↔A8 rework loop', '📅 Calculate baseline completion', '⚡ Evaluate crash options'],
    'recommendation': ['✅ Select ONE crash option', '📆 Calculate revised completion', '💵 Estimate total cost exposure', '🛡️ Develop risk mitigation plan', '📄 Draft executive memo', '🎤 Defend your decision']
}

def get_ai_response(role_key, user_msg, history):
    try:
        msgs = [{"role": "system", "content": f"{ROLE_PROMPTS[role_key]}\n\nContext: Student (Sarah Chen, PM) interviewing you. Be helpful, specific numbers, 2-3 paragraphs.\n\n{CASE_STUDY}"}]
        for m in history:
            msgs.append({"role": "user" if m['role']=='user' else "assistant", "content": m['text']})
        msgs.append({"role": "user", "content": user_msg})
        resp = client.chat.completions.create(model="gpt-4o-mini", messages=msgs, max_tokens=500, temperature=0.7)
        return resp.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

def interviewed_count():
    return sum(1 for msgs in st.session_state.chat_history.values() if any(m['role']=='user' for m in msgs))

# CSS
st.markdown("""<style>
#MainMenu,footer,header,.stDeployButton,div[data-testid="stToolbar"],div[data-testid="stDecoration"],div[data-testid="stStatusWidget"]{display:none!important;}
section[data-testid="stSidebar"]{display:none!important;}
.main .block-container{padding:0!important;max-width:100%!important;}
.stApp{background:#f5f5f5;}
div[data-testid="stVerticalBlock"]{gap:0!important;}
div[data-testid="stHorizontalBlock"]{gap:0!important;}
div[data-testid="column"]{padding:0!important;}
</style>""", unsafe_allow_html=True)

# Layout
left_col, center_col, right_col = st.columns([1, 2.5, 1.2])

# LEFT PANEL
with left_col:
    st.markdown("""<div style="background:#354CA1;color:white;padding:16px;font-weight:bold;font-size:14px;">👥 Stakeholders</div>""", unsafe_allow_html=True)
    st.markdown("""<div style="padding:12px 16px;background:#F9F9F9;border-bottom:1px solid #e5e7eb;">
        <div style="color:#354CA1;font-weight:bold;font-size:14px;">You are Sarah Chen</div>
        <div style="color:#6b7280;font-size:12px;">Project Manager</div>
        <div style="color:#9ca3af;font-size:11px;margin-top:4px;">Click stakeholders to interview</div>
    </div>""", unsafe_allow_html=True)
    
    for aid, agent in STAKEHOLDERS.items():
        is_active = st.session_state.active_agent == aid
        msg_cnt = len([m for m in st.session_state.chat_history.get(aid, []) if m['role']=='user'])
        
        bg = '#E8F4F8' if is_active else '#f9fafb'
        border = '2px solid #59C3C3' if is_active else '1px solid #e5e7eb'
        badge = f' ({msg_cnt})' if msg_cnt > 0 else ''
        
        if st.button(f"{agent['emoji']} {agent['name']}{badge}", key=f"agent_{aid}", use_container_width=True):
            st.session_state.active_agent = aid
            if aid not in st.session_state.chat_history:
                st.session_state.chat_history[aid] = [{'role':'agent','text':GREETINGS[aid],'time':datetime.now().strftime('%H:%M:%S')}]
            st.rerun()
        st.caption(agent['title'])

# CENTER PANEL
with center_col:
    # Header
    if st.session_state.active_agent:
        agent = STAKEHOLDERS[st.session_state.active_agent]
        st.markdown(f"""<div style="background:linear-gradient(to right,#354CA1,#CC0035);color:white;padding:16px;">
            <div style="font-weight:bold;font-size:16px;">💬 Interview: {agent['name']}</div>
            <div style="font-size:13px;opacity:0.9;margin-top:4px;">{agent['title']}</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div style="background:linear-gradient(to right,#354CA1,#CC0035);color:white;padding:16px;">
            <div style="font-weight:bold;font-size:16px;">💬 Select a stakeholder to begin</div>
        </div>""", unsafe_allow_html=True)
    
    # Content
    if not st.session_state.active_agent:
        st.markdown("""<div style="text-align:center;padding:60px 20px;">
            <div style="font-size:64px;margin-bottom:16px;">🎯</div>
            <h2 style="color:#354CA1;font-size:28px;font-weight:bold;margin-bottom:12px;">Delta Wind Farm Project</h2>
            <p style="color:#4b5563;margin-bottom:8px;">You are <strong>Sarah Chen</strong>, Project Manager for Delta Renewables</p>
            <div style="background:#F9F9F9;border-left:4px solid #59C3C3;padding:16px;max-width:600px;margin:16px auto;text-align:left;border-radius:4px;">
                <p style="margin-bottom:12px;"><strong>Situation:</strong> Phase II expansion (50 turbines) has run into turbulence. June 30 deadline is fixed by investor covenant. Missing it means financing freeze.</p>
                <p><strong>Your Mission:</strong> Interview stakeholders, gather information, identify the critical path, choose ONE acceleration option, and deliver a risk-aware plan that hits the deadline.</p>
            </div>
            <p style="color:#CC0035;font-weight:600;font-size:18px;margin-top:24px;">👈 Select a stakeholder to start your investigation</p>
        </div>""", unsafe_allow_html=True)
    else:
        # Chat messages
        agent = STAKEHOLDERS[st.session_state.active_agent]
        messages = st.session_state.chat_history.get(st.session_state.active_agent, [])
        
        chat_container = st.container(height=750)
        with chat_container:
            for msg in messages:
                if msg['role'] == 'user':
                    st.markdown(f"""<div style="display:flex;justify-content:flex-end;margin-bottom:16px;">
                        <div style="max-width:75%;padding:12px 16px;border-radius:12px;background:#354CA1;color:white;">
                            <div style="font-size:11px;opacity:0.7;margin-bottom:4px;">You • {msg['time']}</div>
                            <div style="font-size:14px;line-height:1.5;">{msg['text']}</div>
                        </div>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div style="display:flex;justify-content:flex-start;margin-bottom:16px;">
                        <div style="max-width:75%;padding:12px 16px;border-radius:12px;background:#f3f4f6;color:#1f2937;">
                            <div style="font-size:11px;opacity:0.7;margin-bottom:4px;">{agent['name']} • {msg['time']}</div>
                            <div style="font-size:14px;line-height:1.5;">{msg['text']}</div>
                        </div>
                    </div>""", unsafe_allow_html=True)
        
        # Input
        st.markdown("""<div style="padding:8px 0;border-top:1px solid #e5e7eb;background:#f9fafb;">""", unsafe_allow_html=True)
        
        input_col, btn_col = st.columns([5, 1])
        with input_col:
            user_input = st.text_input("Message", placeholder=f"Ask {agent['name']} about activities, dependencies, risks...", label_visibility="collapsed", key="chat_input")
        with btn_col:
            send_clicked = st.button("Send", key="send_btn", use_container_width=True)
        
        if send_clicked and user_input.strip():
            st.session_state.chat_history[st.session_state.active_agent].append({'role':'user','text':user_input.strip(),'time':datetime.now().strftime('%H:%M:%S')})
            with st.spinner(f"{agent['name']} is typing..."):
                response = get_ai_response(st.session_state.active_agent, user_input, st.session_state.chat_history[st.session_state.active_agent][:-1])
            st.session_state.chat_history[st.session_state.active_agent].append({'role':'agent','text':response,'time':datetime.now().strftime('%H:%M:%S')})
            st.rerun()
        
        st.markdown("""<div style="text-align:center;font-size:12px;color:#6b7280;margin-top:8px;">💡 <strong>Try asking:</strong> "Can you elaborate?" • "Why is that?" • "What do you recommend?"</div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# RIGHT PANEL
with right_col:
    st.markdown("""<div style="background:#F9C80E;color:#262626;padding:16px;font-weight:bold;font-size:14px;">🎯 Mission Objectives</div>""", unsafe_allow_html=True)
    
    # Phase selector
    st.markdown("""<div style="padding:12px;border-bottom:1px solid #e5e7eb;background:#f9fafb;">
        <div style="font-size:12px;color:#6b7280;margin-bottom:8px;">Current Phase:</div>
    </div>""", unsafe_allow_html=True)
    
    for p in ['investigation', 'analysis', 'recommendation']:
        is_active = st.session_state.phase == p
        if st.button(p.capitalize(), key=f"phase_{p}", use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state.phase = p
            st.rerun()
    
    # Objectives
    st.markdown("<div style='padding:16px;'>", unsafe_allow_html=True)
    for obj in OBJECTIVES[st.session_state.phase]:
        st.markdown(f"""<div style="display:flex;align-items:flex-start;gap:8px;font-size:13px;background:#f9fafb;padding:8px 12px;border-radius:4px;margin-bottom:8px;">
            <span style="color:#59C3C3;">✓</span><span>{obj}</span>
        </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Progress
    cnt = interviewed_count()
    pct = (cnt/6)*100
    st.markdown(f"""<div style="padding:16px;border-top:1px solid #e5e7eb;background:linear-gradient(to bottom right,#E8F4F8,#FFF9E6);">
        <div style="font-size:14px;font-weight:600;margin-bottom:8px;">📊 Your Progress</div>
        <div style="background:white;border-radius:9999px;height:12px;overflow:hidden;border:1px solid #e5e7eb;margin-bottom:8px;">
            <div style="height:100%;width:{pct}%;background:linear-gradient(to right,#354CA1,#59C3C3);"></div>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:12px;color:#374151;">
            <span>Interviewed: <strong>{cnt}/6</strong></span><span>{int(pct)}%</span>
        </div>
    </div>""", unsafe_allow_html=True)
    
    # Constraints
    st.markdown("""<div style="padding:16px;border-top:1px solid #e5e7eb;">
        <div style="font-size:14px;font-weight:600;margin-bottom:12px;">⚠️ Key Constraints</div>
        <div style="padding:8px 12px;border-radius:4px;font-size:12px;margin-bottom:8px;background:#FFE5E5;border-left:4px solid #CC0035;"><strong>Deadline:</strong> June 30 (non-negotiable)</div>
        <div style="padding:8px 12px;border-radius:4px;font-size:12px;margin-bottom:8px;background:#E8F0FF;border-left:4px solid #354CA1;"><strong>Contingency:</strong> $400,000</div>
        <div style="padding:8px 12px;border-radius:4px;font-size:12px;margin-bottom:8px;background:#FFFACD;border-left:4px solid #F9C80E;"><strong>Policy:</strong> Only ONE crash option</div>
        <div style="padding:8px 12px;border-radius:4px;font-size:12px;background:#E8F4F8;border-left:4px solid #59C3C3;"><strong>Penalty:</strong> $3,000/day after June 30</div>
    </div>""", unsafe_allow_html=True)
    
    # Export
    st.markdown("<div style='padding:16px;border-top:1px solid #e5e7eb;'>", unsafe_allow_html=True)
    if cnt > 0:
        export_text = "DELTA WIND FARM - Interview Transcript\n" + "="*50 + "\n\n"
        for aid, msgs in st.session_state.chat_history.items():
            if msgs:
                export_text += f"{STAKEHOLDERS[aid]['emoji']} {STAKEHOLDERS[aid]['name']}\n" + "-"*50 + "\n"
                for m in msgs:
                    speaker = "You" if m['role']=='user' else STAKEHOLDERS[aid]['name']
                    export_text += f"[{m['time']}] {speaker}: {m['text']}\n\n"
                export_text += "\n"
        st.download_button("📥 Export All Interviews", export_text, f"delta_wind_interviews.txt", use_container_width=True)
    else:
        st.button("📥 Export All Interviews", disabled=True, use_container_width=True)
        st.caption("Interview stakeholders to enable export")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Reference
    st.markdown("<div style='padding:16px;border-top:1px solid #e5e7eb;background:#f9fafb;'>", unsafe_allow_html=True)
    with st.expander("📐 PERT Formula"):
        st.code("Expected = (O + 4M + P) / 6")
        st.caption("O=Optimistic, M=Most-Likely, P=Pessimistic")
    with st.expander("⚡ Crash Options"):
        st.markdown("**S1:** A3 Foundation (-3d, $70k)\n\n**S2:** A5 Staging (-4d, $110k)\n\n**S3:** A6 Towers (-5d, $150k)\n\n**S4:** A8 Cabling (-4d, $130k)\n\n**S5:** A9 Substation (-3d, $60k)")
    with st.expander("🔗 Key Dependencies"):
        st.markdown("• A1 → A3\n• A2 → A4\n• A3 & A2 → A4\n• A4 & A5 → A6\n• A6 → A7, A8\n• **A6 ↔ A8 (coupling risk!)**\n• A8 & A9 → A10\n• A10 → A11 → A12")
    st.markdown("</div>", unsafe_allow_html=True)
