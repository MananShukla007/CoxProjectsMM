import streamlit as st
from openai import OpenAI

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="SMU Cox AI Teaching Tools",
    layout="wide"
)

# --------------------------------------------------
# API KEY (TEMP DEMO KEY — REPLACE LATER)
# --------------------------------------------------
OPENAI_API_KEY = ""
client = OpenAI(api_key=OPENAI_API_KEY)

# --------------------------------------------------
# COLORS (SMU STYLE)
# --------------------------------------------------
SMU_BLUE = "#354CA1"
SMU_RED = "#CC0035"

# --------------------------------------------------
# GLOBAL STYLES
# --------------------------------------------------
st.markdown(
    f"""
    <style>
        body {{
            background-color: white;
        }}
        .main-title {{
            font-size: 44px;
            font-weight: 700;
            color: {SMU_BLUE};
            margin-bottom: 0.3em;
        }}
        .subtitle {{
            font-size: 20px;
            color: #444444;
            margin-bottom: 2em;
            max-width: 900px;
        }}
        .section-title {{
            font-size: 28px;
            font-weight: 600;
            color: {SMU_BLUE};
            margin-top: 1.8em;
        }}
        .info-box {{
            background-color: #F8F9FB;
            border-left: 6px solid {SMU_RED};
            padding: 1.5em;
            margin-top: 1.5em;
            max-width: 900px;
        }}
        .feature-title {{
            font-size: 20px;
            font-weight: 600;
            color: {SMU_BLUE};
            margin-bottom: 0.3em;
        }}
        .feature-text {{
            font-size: 16px;
            color: #333333;
            margin-bottom: 1.5em;
        }}
        .footer {{
            margin-top: 5em;
            font-size: 14px;
            color: #777777;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------
with st.sidebar:
    st.markdown("### SMU Cox AI Portal")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["Home", "Question Generator", "Rubric Generator"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.caption("SMU Cox School of Business")

# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------
if page == "Home":
    st.markdown('<div class="main-title">SMU Cox AI Teaching Tools</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="subtitle">'
        'This platform provides AI-powered tools designed to support faculty in course design, '
        'assessment development, and instructional planning. The tools are intended to enhance '
        'teaching workflows while maintaining academic rigor and institutional standards.'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="info-box">'
        '<div class="feature-title">Purpose</div>'
        '<div class="feature-text">'
        'These tools assist instructors in generating high-quality academic materials efficiently, '
        'allowing more time for meaningful engagement with students.'
        '</div>'

        '<div class="feature-title">Responsible Use</div>'
        '<div class="feature-text">'
        'AI-generated outputs are intended as starting points and should be reviewed and refined '
        'by faculty to ensure alignment with course objectives and academic standards.'
        '</div>'

        '<div class="feature-title">Available Tools</div>'
        '<div class="feature-text">'
        'Use the navigation menu on the left to access individual tools.'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

# --------------------------------------------------
# QUESTION GENERATOR
# --------------------------------------------------
if page == "Question Generator":
    st.markdown('<div class="main-title">Question Generator</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="subtitle">'
        'Generate academic questions aligned with course topics, learning depth, and assessment format.'
        '</div>',
        unsafe_allow_html=True
    )

    topic = st.text_input("Course topic", placeholder="e.g., Financial Risk Management")
    level = st.selectbox("Difficulty level", ["Introductory", "Intermediate", "Advanced"])
    q_type = st.selectbox("Question type", ["Multiple Choice", "Short Answer", "Essay"])
    num_questions = st.slider("Number of questions", 1, 10, 5)

    if st.button("Generate Questions"):
        with st.spinner("Generating questions..."):
            prompt = f"""
            Create {num_questions} {q_type} questions for a {level} level course.
            Topic: {topic}

            If multiple choice, include 4 options and clearly mark the correct answer.
            """

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )

            st.markdown("### Generated Questions")
            st.write(response.choices[0].message.content)

# --------------------------------------------------
# RUBRIC GENERATOR
# --------------------------------------------------
if page == "Rubric Generator":
    st.markdown('<div class="main-title">Rubric Generator</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="subtitle">'
        'Create structured grading rubrics that clearly define performance expectations and evaluation criteria.'
        '</div>',
        unsafe_allow_html=True
    )

    assignment = st.text_input("Assignment name", placeholder="e.g., Strategy Case Analysis")
    criteria = st.text_area(
        "Evaluation criteria (comma-separated)",
        placeholder="Clarity, Depth of Analysis, Organization, Use of Evidence"
    )
    scale = st.selectbox(
        "Grading scale",
        ["Excellent / Good / Fair / Poor", "4-point scale", "Percentage-based"]
    )

    if st.button("Generate Rubric"):
        with st.spinner("Generating rubric..."):
            prompt = f"""
            Create a grading rubric for the assignment titled "{assignment}".

            Evaluation criteria:
            {criteria}

            Use this grading scale:
            {scale}

            Format the rubric clearly with criteria and performance descriptions.
            """

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6
            )

            st.markdown("### Generated Rubric")
            st.write(response.choices[0].message.content)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown(
    '<div class="footer">© SMU Cox School of Business · Internal AI Tools Prototype</div>',
    unsafe_allow_html=True
)
