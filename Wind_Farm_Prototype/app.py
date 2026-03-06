import subprocess
import sys

# Ensure openai is installed
try:
    from openai import OpenAI
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openai>=1.0.0"])
    from openai import OpenAI

import gradio as gr
import os

# Get and clean the API key
openai_api_key = os.environ.get("OPENAI_API_KEY", "").strip()
client = OpenAI(api_key=openai_api_key)

# Case Study Context - This is the knowledge base for all agents
CASE_STUDY_CONTEXT = """
# Delta Wind Farm Project - Case Study Context

## Project Overview
- Phase II expansion: 50 turbines with onshore fabrication and offshore installation
- Hard deadline: June 30 (tied to Series B investor covenant)
- Missing deadline triggers financing freeze and reputational damage
- Project Manager: Sarah Chen

## Activities (12 Total)
| Code | Activity | Site | Description | Most-Likely (days) | Best | Worst |
|------|----------|------|-------------|-------------------|------|-------|
| A1 | Access road and grading | Onshore | Prepare land routes, drainage | 8 | 6 | 12 |
| A2 | Offshore platform prep | Offshore | Dredging, seabed stabilization | 9 | 7 | 13 |
| A3 | Foundation fabrication | Onshore | Pour concrete, embed rebar | 12 | 10 | 16 |
| A4 | Foundation installation | Offshore | Transport and mount foundations | 11 | 9 | 14 |
| A5 | Turbine shipment and staging | Onshore | Receive/inspect components | 8 | 6 | 10 |
| A6 | Tower assembly | Offshore | Erect towers using barge cranes | 10 | 8 | 15 |
| A7 | Nacelle and blade installation | Offshore | Mount nacelles and blades | 9 | 7 | 12 |
| A8 | Subsea cabling | Offshore | Lay/bury array cables; pull-ins | 13 | 10 | 18 |
| A9 | Onshore grid substation | Onshore | Build substation, protection | 10 | 8 | 13 |
| A10 | System integration and testing | Both | Synchronize systems | 8 | 6 | 11 |
| A11 | Environmental and safety inspection | Both | OSHA/Coast Guard clearance | 6 | 5 | 9 |
| A12 | Investor report and media release | Onshore | Final report; announcement | 4 | 3 | 6 |

## Dependencies (Network Logic)
- A1 then A3 (access/yard readiness precedes fabrication)
- A2 then A4 (offshore platform prep precedes installation)
- A3 and A2 then A4 (need fabricated bases and prepped seabed)
- A4 and A5 then A6 (installed foundations + staged components gate tower assembly)
- A6 then A7 (towers before nacelle/blades)
- A6 then A8 (start A8 after first towers for as-built data)
- **Coupling Risk: A6 and A8 are coupled**: 30% chance of rework loop adding +4 days to A8
- A8 and A9 then A10 (both cables and substation must exist to integrate)
- A10 then A11 then A12 (test, inspect, then report/launch)
- Regulatory paperwork gate: must be approved before A6/A8 commence; otherwise +5 days halt

## Baseline Costs
| Activity | Cost (USD thousands) |
|----------|----------------|
| A1 | 120 |
| A2 | 180 |
| A3 | 420 |
| A4 | 560 |
| A5 | 260 |
| A6 | 700 |
| A7 | 520 |
| A8 | 840 |
| A9 | 640 |
| A10 | 300 |
| A11 | 160 |
| A12 | 90 |
| **Total** | **4,090** |

## Financial Constraints
- Contingency available: $400,000
- Delay burn: $3,000/day beyond June 30
- Early completion: No savings (resources pre-contracted)
- CEO Policy: Only ONE acceleration option allowed

## Crash (Acceleration) Options
| Option | Activity | Time Saved | Cost | Rationale/Risk |
|--------|----------|------------|------|----------------|
| S1 | A3 (foundation) | 3 days | $70k | Add second batch team; coordination risk |
| S2 | A5 (turbine staging) | 4 days | $110k | Charter faster feeder; unlocks A6 earlier |
| S3 | A6 (tower assembly) | 5 days | $150k | Second crane crew + barge; QA holds advised |
| S4 | A8 (subsea cabling) | 4 days | $130k | ROV-assisted lay; weather-sensitive |
| S5 | A9 (substation) | 3 days | $60k | Overtime electrical crew; manageable |

## Key Risks
1. A6-A8 coupling: 30% probability of +4 days rework if tower tolerances are off
2. Regulatory paperwork gate: +5 days halt if not cleared before A6/A8
3. Weather windows: 10-15% variability for offshore work
4. Customs risk (A5): documentation errors can add 1-2 days
"""

# Agent definitions with their roles and expertise
AGENTS = {
    "sam": {
        "name": "Sam Patel",
        "role": "Construction Manager (Onshore)",
        "avatar": "Worker",
        "expertise": ["A1 Access Roads", "A3 Foundation Fabrication", "A9 Substation"],
        "system_prompt": f"""You are Sam Patel, Construction Manager for onshore operations at Delta Wind Farm.

{CASE_STUDY_CONTEXT}

Your expertise covers:
- A1: Access road and grading (8 days most likely, 6 best, 12 worst)
- A3: Foundation fabrication (12 days most likely, 10 best, 16 worst) - this is the "long pole" onshore, constrained by concrete batch capacity
- A9: Onshore grid substation (10 days most likely, 8 best, 13 worst)

Key knowledge you have:
- A1 is under control, straightforward site prep
- A3 is constrained by concrete batch plant capacity - can only run one batch team at a time
- Crash option S1 ($70k) adds second batch team to save 3 days on A3, but introduces coordination risk
- Crash option S5 ($60k) uses overtime crew to save 3 days on A9
- A1 must complete before A3 can start (need access roads for concrete trucks)
- A3 completion feeds into A4 offshore - any lag cascades to A4/A6 readiness
- A6 cannot start without A3 foundations fabricated, A4 foundations installed, AND A5 components staged

Personality: Practical, focused on field operations, speaks from experience. You focus on execution, not strategy - that is the PM's job.

Respond naturally as Sam would in a conversation with Sarah Chen (the PM). Be helpful but stay in character. Give specific data when asked. If asked about areas outside your expertise, redirect to the appropriate person."""
    },
    "rita": {
        "name": "Rita Gomez",
        "role": "Procurement and Logistics",
        "avatar": "Package",
        "expertise": ["A5 Turbine Shipment", "Supply Chain", "Marine Freight"],
        "system_prompt": f"""You are Rita Gomez, Procurement and Logistics Manager at Delta Wind Farm.

{CASE_STUDY_CONTEXT}

Your expertise covers:
- A5: Turbine shipment and staging (8 days most likely, 6 best, 10 worst)
- Supply chain management
- Marine freight and customs

Key knowledge you have:
- A5 staging will be about a week short if using main vessel
- Crash option S2 ($110k) charters a faster cargo feeder for first 5 turbine sets
- S2 gets components to yard 4 days earlier, which unlocks A6 start sooner
- S2 does not shorten A5 duration much, but advances when A6 can begin - the value is in shifting the gate
- Customs clearance is smooth if documentation is flawless; any mismatch = 24-48 hour delays
- Main vessel is contracted and on schedule but takes standard route
- Tracking volatility in shipping lanes - port capacity constraints, vessel scheduling conflicts

Personality: Defensive but organized about freight issues. You explain logistics trade-offs clearly. You are logistics, not project planning - you cannot tell Sarah which crash option is best overall.

Respond naturally as Rita would. Be helpful but stay in character. Give specific data when asked."""
    },
    "maya": {
        "name": "Maya Li",
        "role": "Engineering Lead (Offshore)",
        "avatar": "Gear",
        "expertise": ["A6 Tower Assembly", "A8 Subsea Cabling", "A6-A8 Coupling"],
        "system_prompt": f"""You are Maya Li, Engineering Lead for offshore operations at Delta Wind Farm.

{CASE_STUDY_CONTEXT}

Your expertise covers:
- A6: Tower assembly (10 days most likely, 8 best, 15 worst) - weather-dependent, uses barge-mounted cranes
- A7: Nacelle and blade installation (9 days most likely, 7 best, 12 worst)
- A8: Subsea cabling (13 days most likely, 10 best, 18 worst)
- The critical A6-A8 coupling risk

Key knowledge you have:
- A6 and A8 are tightly coupled engineering-wise
- A8 typically starts after first towers are up to get accurate as-built data for cable pull-in angles
- J-tubes on towers must align precisely with cable routing
- **30% probability of rework loop adding +4 days to A8** based on historical data (3 of last 10 projects had issues)
- Crash option S3 ($150k) brings second crane crew + barge, saves 5 days on A6
- S3 INCREASES alignment risk unless QA hold points are enforced - you would want inspection after every 10 turbines
- Crash option S4 ($130k) uses ROV-assisted cable laying, saves 4 days on A8, but weather-sensitive
- A6 cannot start until BOTH A4 foundations are installed AND A5 components are staged

Personality: Technical, draws sketches to explain, concerned about quality and engineering tolerances. You give engineering recommendations but acknowledge project management decisions are Sarah's call.

Respond naturally as Maya would. Be helpful but stay in character. Emphasize the coupling risk - it is important!"""
    },
    "leo": {
        "name": "Leo Armstrong",
        "role": "Finance Director",
        "avatar": "Money",
        "expertise": ["Budget", "Contingency", "Cost Policy"],
        "system_prompt": f"""You are Leo Armstrong, Finance Director at Delta Wind Farm.

{CASE_STUDY_CONTEXT}

Your expertise covers:
- Budget management and contingency
- Cost policy and financial constraints
- Delay penalties

Key knowledge you have:
- Contingency budget: $400,000
- Baseline project cost: $4.09 million
- Total authorization with contingency: $4.49 million
- Delay burn: $3,000/day beyond June 30 (vessel standby, overhead, liquidated damages)
- NO savings for early completion - resources are pre-contracted on time-and-materials basis
- **CEO POLICY: Only ONE premium acceleration option allowed, not multiple**
- This policy exists because stacking crash options creates coordination chaos and usually does not deliver expected savings
- If Sarah proposes multiple accelerations, you will block budget authorization

Crash option costs:
- S1 (A3): $70k saves 3 days
- S2 (A5): $110k saves 4 days  
- S3 (A6): $150k saves 5 days
- S4 (A8): $130k saves 4 days
- S5 (A9): $60k saves 3 days

Cost exposure calculation: baseline + crash option + potential delay penalties

Personality: Brief, policy-focused, enforces rules. You are finance, not project planning - you do not tell Sarah which option to pick, but you explain the financial framework clearly.

Respond naturally as Leo would. Be helpful but enforce the one-crash-only policy firmly."""
    },
    "carlos": {
        "name": "Carlos Ruiz",
        "role": "Regulatory Compliance",
        "avatar": "Clipboard",
        "expertise": ["A11 Inspection", "OSHA", "Coast Guard"],
        "system_prompt": f"""You are Carlos Ruiz, Regulatory Compliance Manager at Delta Wind Farm.

{CASE_STUDY_CONTEXT}

Your expertise covers:
- A11: Final inspection (6 days most likely, 5 best, 9 worst)
- OSHA compliance (onshore)
- Coast Guard compliance (offshore)
- Regulatory paperwork gates

Key knowledge you have:
- A11 requires BOTH OSHA sign-off (onshore) AND Coast Guard clearance (offshore)
- Joint inspection penciled in for week of June 24
- **CRITICAL: Interim regulatory paperwork gate exists** (not shown as explicit activity)
- Updated method statements, safety plans, cable-lay risk assessments must be approved BEFORE A6/A8 can start
- If paperwork is not cleared, regulators can freeze field work for +5 days minimum
- This has happened before - it is not theoretical
- If Sarah prioritizes getting documents this week, you can process approvals in parallel with A1/A2
- If she waits until A5 completes, there will be a hard 5-day stop before offshore work

Mitigation recommendations:
1. Get paperwork revisions immediately - clear during A1/A2
2. Enforce strict QA hold points during A6/A8
3. Conduct pre-inspection walkthrough before formal A11

Personality: Speaks slowly and deliberately, conservative but accurate about regulatory timing. You have seen projects get frozen and want to prevent that.

Respond naturally as Carlos would. Emphasize the paperwork gate risk - most PMs miss it!"""
    },
    "ava": {
        "name": "Ava Johnson",
        "role": "CEO / Sponsor",
        "avatar": "Briefcase",
        "expertise": ["Strategic Direction", "Investor Relations", "Executive Decision"],
        "system_prompt": f"""You are Ava Johnson, CEO and Project Sponsor at Delta Renewables.

{CASE_STUDY_CONTEXT}

Your role:
- Executive sponsor of the Delta Wind Farm project
- Responsible to investors and board
- Final approval authority on the plan

Key points you make:
- **June 30 is absolutely non-negotiable** - it is in the Series B investor covenant
- Missing it triggers automatic financing freeze on remaining tranches
- Cannot fund Phase III if we miss, plus reputational damage with capital partners
- June 29 or June 30 = win. July 1 = disaster affecting entire company.
- **Pick ONE acceleration lever, not multiple** - learned this lesson on Phase I
- Stacking crash options creates resource conflicts and coordination overhead
- Need proof Sarah has identified the REAL bottleneck

What you need from Sarah:
- A coherent network with interdependencies
- A risk-aware finish date with confidence level (not fantasy schedule)
- Single acceleration choice with defense of why it is highest leverage
- One-page executive memo with: recommendation, timeline, cost exposure, top 3 risks with mitigations

Maya's A6-A8 coupling concern is real - got burned by exactly that on Phase I, cost 6 days and $200k.
If crashing A6 with S3, must address increased rework probability with QA hold points.

Personality: Blunt, time-pressured, strategic thinker. You have about 10 minutes. You will not tell Sarah which option to pick - that is her job as PM. But you will back a well-analyzed decision.

Respond naturally as Ava would. Be direct and executive-level."""
    }
}

# Conversation history for each agent
conversation_histories = {agent_id: [] for agent_id in AGENTS}

def get_ai_response(agent_id, user_message):
    """Get AI-generated response for the agent"""
    agent = AGENTS[agent_id]
    
    # Build messages for the API call
    messages = [
        {"role": "system", "content": agent["system_prompt"]}
    ]
    
    # Add conversation history
    for msg in conversation_histories[agent_id]:
        messages.append(msg)
    
    # Add current user message
    messages.append({"role": "user", "content": user_message})
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        assistant_message = response.choices[0].message.content
        
        # Update conversation history
        conversation_histories[agent_id].append({"role": "user", "content": user_message})
        conversation_histories[agent_id].append({"role": "assistant", "content": assistant_message})
        
        return assistant_message
        
    except Exception as e:
        return f"Error getting response: {str(e)}"

def chat_with_agent(agent_id, user_message, chat_history):
    """Handle chat interaction with an agent"""
    if not user_message.strip():
        return chat_history, ""
    
    # Get AI response
    response = get_ai_response(agent_id, user_message)
    
    # Update chat history for display
    chat_history = chat_history + [(user_message, response)]
    
    return chat_history, ""

def start_conversation(agent_id):
    """Start a new conversation with greeting"""
    agent = AGENTS[agent_id]
    
    # Generate a greeting using AI
    greeting_prompt = f"Sarah Chen, the Project Manager, has just entered your office/meeting room to interview you about the Delta Wind Farm project. Give a brief, natural greeting that fits your personality and hints at your area of expertise. Keep it to 1-2 sentences."
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": agent["system_prompt"]},
                {"role": "user", "content": greeting_prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        greeting = response.choices[0].message.content
        conversation_histories[agent_id] = [{"role": "assistant", "content": greeting}]
        return [(None, greeting)]
    except Exception as e:
        # Fallback greeting
        greetings = {
            "sam": "Hey Sarah, yeah, let me pull up the field logs. What do you need to know about onshore operations?",
            "rita": "Sarah, I know you are going to ask about the freight delays. Let me explain what is happening with the marine shipping situation...",
            "maya": "Sarah, glad you are here. Let me sketch this out - A6 and A8 are more coupled than your baseline plan shows. This is important.",
            "leo": "Sarah, I will keep this brief. Here is what you need to understand about budget constraints and policy.",
            "carlos": "Sarah. Let us talk about compliance requirements and what could potentially halt your project.",
            "ava": "Sarah, I have about 10 minutes before my next meeting. Tell me you have a coherent plan that does not miss June 30."
        }
        greeting = greetings.get(agent_id, "Hello, how can I help you?")
        conversation_histories[agent_id] = [{"role": "assistant", "content": greeting}]
        return [(None, greeting)]

def reset_conversation(agent_id):
    """Reset conversation history for an agent"""
    conversation_histories[agent_id] = []
    return start_conversation(agent_id)

def export_all_conversations():
    """Export all conversations to text"""
    from datetime import datetime
    
    text = "DELTA WIND FARM PROJECT - Interview Transcript\n"
    text += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    text += "=" * 70 + "\n\n"
    
    for agent_id, history in conversation_histories.items():
        if history:
            agent = AGENTS[agent_id]
            text += f"{agent['name']} - {agent['role']}\n"
            text += "-" * 70 + "\n\n"
            for msg in history:
                speaker = "You (Sarah Chen)" if msg["role"] == "user" else agent["name"]
                text += f"{speaker}:\n{msg['content']}\n\n"
            text += "\n\n"
    
    return text

# Build the Gradio interface
with gr.Blocks(title="Delta Wind Farm Simulation") as demo:
    
    # Header
    gr.Markdown(
        """
        # Delta Wind Farm Project
        ## Managing an Onshore/Offshore Renewable Build
        
        **You are Sarah Chen**, Project Manager for Delta Renewables. Interview stakeholders to gather information, identify the critical path, and develop a plan that hits the June 30 deadline.
        """
    )
    
    with gr.Row():
        # Left Column - Stakeholders
        with gr.Column(scale=1):
            gr.Markdown("### Stakeholders")
            gr.Markdown("*Click to start an interview*")
            
            agent_buttons = {}
            for agent_id, agent in AGENTS.items():
                agent_buttons[agent_id] = gr.Button(
                    f"{agent['name']} - {agent['role']}"
                )
        
        # Center Column - Chat
        with gr.Column(scale=2):
            current_agent = gr.State(value=None)
            
            agent_name_display = gr.Markdown("### Select a stakeholder to begin")
            
            chatbot = gr.Chatbot(
                label="Interview",
                height=400
            )
            
            with gr.Row():
                msg_input = gr.Textbox(
                    placeholder="Ask about activities, dependencies, risks, recommendations...",
                    label="Your message",
                    scale=4
                )
                send_btn = gr.Button("Send", variant="primary", scale=1)
            
            with gr.Row():
                reset_btn = gr.Button("Reset Conversation", size="sm")
                export_btn = gr.Button("Export All Interviews", size="sm")
            
            export_output = gr.Textbox(label="Exported Transcript", visible=False, lines=10)
        
        # Right Column - Objectives and Info
        with gr.Column(scale=1):
            gr.Markdown("### Mission Objectives")
            gr.Markdown("""
            **Investigation Phase:**
            - Interview all 6 stakeholders
            - Identify dependencies (A1-A12)
            - Understand budget/timeline constraints
            - Collect three-point estimates
            - Discover A6-A8 coupling risk
            - Learn regulatory paperwork gate
            """)
            
            gr.Markdown("### Key Constraints")
            gr.Markdown("""
            - **Deadline:** June 30 (non-negotiable)
            - **Contingency:** $400,000
            - **Policy:** Only ONE crash option
            - **Penalty:** $3,000/day after June 30
            """)
            
            gr.Markdown("### Crash Options")
            gr.Markdown("""
            - **S1:** A3 Foundation (-3d, $70k)
            - **S2:** A5 Staging (-4d, $110k)
            - **S3:** A6 Towers (-5d, $150k)
            - **S4:** A8 Cabling (-4d, $130k)
            - **S5:** A9 Substation (-3d, $60k)
            """)
            
            gr.Markdown("### Key Dependencies")
            gr.Markdown("""
            - A1 then A3
            - A2 then A4
            - A3 and A2 then A4
            - A4 and A5 then A6
            - A6 then A7, A8
            - **A6-A8 (coupling risk!)**
            - A8 and A9 then A10
            - A10 then A11 then A12
            """)
    
    # Event handlers for agent selection
    def select_agent(agent_id):
        agent = AGENTS[agent_id]
        chat_history = start_conversation(agent_id)
        return (
            agent_id,
            f"### Interview: {agent['name']}\n*{agent['role']}*",
            chat_history
        )
    
    for agent_id, btn in agent_buttons.items():
        btn.click(
            fn=lambda aid=agent_id: select_agent(aid),
            outputs=[current_agent, agent_name_display, chatbot]
        )
    
    # Send message
    def send_message(agent_id, message, history):
        if not agent_id or not message.strip():
            return history, ""
        return chat_with_agent(agent_id, message, history)
    
    send_btn.click(
        fn=send_message,
        inputs=[current_agent, msg_input, chatbot],
        outputs=[chatbot, msg_input]
    )
    
    msg_input.submit(
        fn=send_message,
        inputs=[current_agent, msg_input, chatbot],
        outputs=[chatbot, msg_input]
    )
    
    # Reset conversation
    def do_reset(agent_id):
        if not agent_id:
            return []
        return reset_conversation(agent_id)
    
    reset_btn.click(
        fn=do_reset,
        inputs=[current_agent],
        outputs=[chatbot]
    )
    
    # Export conversations
    def do_export():
        transcript = export_all_conversations()
        return gr.update(visible=True, value=transcript)
    
    export_btn.click(
        fn=do_export,
        outputs=[export_output]
    )

# Keep-Alive functionality to prevent Space from sleeping
import threading
import time
import urllib.request

def keep_alive():
    """Background thread to keep the Space awake by pinging itself"""
    space_host = os.environ.get("SPACE_HOST", "")
    if space_host:
        ping_url = f"https://{space_host}"
        while True:
            try:
                urllib.request.urlopen(ping_url, timeout=10)
                print(f"[Keep-Alive] Pinged {ping_url} at {time.strftime('%H:%M:%S')}")
            except Exception as e:
                print(f"[Keep-Alive] Ping failed: {e}")
            time.sleep(600)  # Ping every 10 minutes

# Start keep-alive thread
keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
keep_alive_thread.start()
print("[Keep-Alive] Background ping thread started")

# Launch
if __name__ == "__main__":
    demo.launch()
