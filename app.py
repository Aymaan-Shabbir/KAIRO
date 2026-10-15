
import html
import re
from io import BytesIO

import streamlit as st

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
)

from pipeline import run_research_pipeline


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Kairo | AI Research",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# 2. PDF GENERATION
# ============================================================

def create_pdf(report_text, topic, feedback_text=""):
    """
    Create a downloadable PDF containing the research report
    and critic feedback.
    """

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.65 * inch,
        title=f"Kairo Research Report - {topic}",
        author="Kairo AI Research",
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="KairoTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#6D4AFF"),
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="KairoSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=15,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#666666"),
            spaceAfter=20,
        )
    )

    styles.add(
        ParagraphStyle(
            name="KairoHeading1",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=21,
            textColor=colors.HexColor("#5635C8"),
            spaceBefore=15,
            spaceAfter=8,
            keepWithNext=True,
        )
    )

    styles.add(
        ParagraphStyle(
            name="KairoHeading2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#303448"),
            spaceBefore=10,
            spaceAfter=6,
            keepWithNext=True,
        )
    )

    styles.add(
        ParagraphStyle(
            name="KairoBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#252936"),
            spaceAfter=8,
            splitLongWords=1,
        )
    )

    styles.add(
        ParagraphStyle(
            name="KairoBullet",
            parent=styles["KairoBody"],
            leftIndent=16,
            firstLineIndent=-10,
            spaceAfter=5,
        )
    )

    styles.add(
        ParagraphStyle(
            name="KairoCode",
            parent=styles["Code"],
            fontName="Courier",
            fontSize=8,
            leading=11,
            leftIndent=8,
            rightIndent=8,
            spaceAfter=8,
        )
    )

    story = []

    # Document title
    story.append(Paragraph("KAIRO", styles["KairoTitle"]))

    story.append(
        Paragraph(
            "AI RESEARCH REPORT",
            styles["KairoSubtitle"],
        )
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=1.2,
            color=colors.HexColor("#A78BFA"),
            spaceAfter=18,
        )
    )

    # Research topic
    story.append(
        Paragraph("Research Topic", styles["KairoHeading2"])
    )

    story.append(
        Paragraph(
            html.escape(str(topic)),
            styles["KairoBody"],
        )
    )

    story.append(Spacer(1, 10))

    story.append(
        Paragraph("Research Findings", styles["KairoHeading1"])
    )

    def render_markdown(content):
        """
        Convert common Markdown syntax into ReportLab paragraphs.
        Supports headings, paragraphs, bold, italic, code,
        bullets, numbered lists and horizontal rules.
        """

        lines = str(content).splitlines()
        paragraph_lines = []
        in_code_block = False
        code_lines = []

        def flush_paragraph():
            if not paragraph_lines:
                return

            text = " ".join(
                line.strip() for line in paragraph_lines
            )

            text = html.escape(text)

            # Basic inline Markdown formatting.
            text = re.sub(
                r"\*\*(.+?)\*\*",
                r"<b>\1</b>",
                text,
            )

            text = re.sub(
                r"(?<!\*)\*([^*]+)\*(?!\*)",
                r"<i>\1</i>",
                text,
            )

            text = re.sub(
                r"`([^`]+)`",
                r'<font name="Courier">\1</font>',
                text,
            )

            story.append(
                Paragraph(text, styles["KairoBody"])
            )

            paragraph_lines.clear()

        def flush_code():
            if not code_lines:
                return

            code_text = "<br/>".join(
                html.escape(line) if line else "&#160;"
                for line in code_lines
            )

            story.append(
                Paragraph(code_text, styles["KairoCode"])
            )

            code_lines.clear()

        for raw_line in lines:
            line = raw_line.strip()

            # Fenced code blocks.
            if line.startswith("```"):
                if in_code_block:
                    flush_code()
                    in_code_block = False
                else:
                    flush_paragraph()
                    in_code_block = True
                continue

            if in_code_block:
                code_lines.append(raw_line)
                continue

            # Empty lines separate paragraphs.
            if not line:
                flush_paragraph()
                continue

            # Horizontal rules.
            if line in ("---", "***", "___"):
                flush_paragraph()

                story.append(
                    HRFlowable(
                        width="100%",
                        thickness=0.5,
                        color=colors.HexColor("#D8D9E2"),
                        spaceBefore=5,
                        spaceAfter=10,
                    )
                )
                continue

            # Markdown headings.
            heading = re.match(r"^(#{1,3})\s+(.+)$", line)

            if heading:
                flush_paragraph()

                level = len(heading.group(1))
                heading_text = html.escape(heading.group(2))

                if level == 1:
                    style = styles["KairoHeading1"]
                else:
                    style = styles["KairoHeading2"]

                story.append(
                    Paragraph(heading_text, style)
                )
                continue

            # Bulleted lists.
            bullet = re.match(r"^[-*+]\s+(.+)$", line)

            if bullet:
                flush_paragraph()

                bullet_text = html.escape(bullet.group(1))

                story.append(
                    Paragraph(
                        f"&bull; {bullet_text}",
                        styles["KairoBullet"],
                    )
                )
                continue

            # Numbered lists.
            numbered = re.match(r"^(\d+)[.)]\s+(.+)$", line)

            if numbered:
                flush_paragraph()

                number = numbered.group(1)
                item_text = html.escape(numbered.group(2))

                story.append(
                    Paragraph(
                        f"{number}. {item_text}",
                        styles["KairoBullet"],
                    )
                )
                continue

            paragraph_lines.append(line)

        flush_paragraph()

        if in_code_block:
            flush_code()

    # Main report.
    render_markdown(report_text)

    # Critic feedback in the same PDF.
    if feedback_text:
        story.append(Spacer(1, 12))

        story.append(
            HRFlowable(
                width="100%",
                thickness=1,
                color=colors.HexColor("#A78BFA"),
                spaceBefore=8,
                spaceAfter=10,
            )
        )

        story.append(
            Paragraph("Critic Review", styles["KairoHeading1"])
        )

        render_markdown(feedback_text)

    # Footer and page numbers.
    def add_page_number(canvas, document):
        canvas.saveState()

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#777777"))

        canvas.drawCentredString(
            A4[0] / 2,
            0.35 * inch,
            f"Kairo AI Research | Page {document.page}",
        )

        canvas.restoreState()

    doc.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes


# ============================================================
# 3. CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>
    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    :root {
        --bg: #0b0d12;
        --surface: #12151d;
        --surface-hover: #191d27;
        --border: #292e3a;
        --text: #f0f2f8;
        --muted: #929bad;
        --accent: #a78bfa;
        --accent-strong: #7c5cfa;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: var(--bg);
        color: var(--text);
    }

    .block-container {
        max-width: 1150px;
        padding: 2rem 2rem 3rem;
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* Brand */

    .brand {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 2rem;
    }

    .brand-icon {
        width: 44px;
        height: 44px;
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #a78bfa, #6d4aff);
        border-radius: 14px;
        font-size: 22px;
        font-weight: 800;
        color: white;
    }

    .brand-name {
        color: #f5f3ff;
        font-size: 23px;
        font-weight: 800;
        letter-spacing: -1px;
    }

    .brand-subtitle {
        color: var(--muted);
        font-size: 10px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }

    /* Hero */

    .hero {
        text-align: center;
        padding: 1.7rem 0 1rem;
    }

    .eyebrow {
        display: inline-block;
        padding: 7px 13px;
        border: 1px solid #38304e;
        background: #191528;
        color: #c4b5fd;
        border-radius: 30px;
        font-size: 11px;
        letter-spacing: 1px;
        font-weight: 600;
        margin-bottom: 18px;
    }

    .hero h1 {
        color: #f8f7ff;
        font-size: clamp(32px, 5vw, 54px);
        line-height: 1.16;
        letter-spacing: -1.8px;
        font-weight: 800;
        margin: 0 0 15px;
    }

    .gradient-text {
        background: linear-gradient(90deg, #c4b5fd, #8b7cff, #e9d5ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-description {
        color: var(--muted);
        max-width: 600px;
        margin: 0 auto;
        font-size: 14px;
        line-height: 1.8;
    }

    /* Agent cards */

    .agent-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 20px 8px;
        min-height: 140px;
        text-align: center;
        box-sizing: border-box;
        overflow-wrap: anywhere;
    }

    .agent-icon {
        font-size: 25px;
        margin-bottom: 11px;
    }

    .agent-title {
        color: var(--text);
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 7px;
    }

    .agent-description {
        color: var(--muted);
        font-size: 11px;
        line-height: 1.6;
    }

    /* Section headings */

    .section-heading {
        color: var(--text);
        font-size: 22px;
        font-weight: 750;
        letter-spacing: -0.5px;
        margin: 1rem 0 5px;
    }

    .section-caption {
        color: var(--muted);
        font-size: 13px;
        line-height: 1.7;
        margin-bottom: 16px;
    }

    /* Input */

    div[data-testid="stTextInput"] input {
        background: var(--surface);
        color: var(--text);
        border: 1px solid var(--border);
        border-radius: 11px;
        min-height: 46px;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: var(--accent);
        box-shadow: 0 0 0 1px var(--accent);
    }

    div[data-testid="stFormSubmitButton"] button {
        background: var(--accent-strong);
        color: white;
        border: 1px solid var(--accent-strong);
        border-radius: 11px;
        min-height: 46px;
        font-weight: 700;
    }

    div[data-testid="stFormSubmitButton"] button:hover {
        background: #9279ff;
        border-color: #9279ff;
    }

    /* Result panel */

    .result-panel {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 18px;
        margin: 12px 0;
        overflow-wrap: anywhere;
    }

    .result-label {
        color: #b8a7ff;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        margin-bottom: 10px;
    }

    .result-topic {
        color: var(--text);
        font-size: 18px;
        font-weight: 700;
        line-height: 1.6;
    }

    .status-pill {
        display: inline-block;
        background: #153326;
        border: 1px solid #24563c;
        color: #86efac;
        border-radius: 30px;
        padding: 6px 10px;
        font-size: 10px;
        font-weight: 700;
        margin-top: 12px;
    }

    /* Empty state */

    .empty-state {
        text-align: center;
        background: var(--surface);
        border: 1px dashed #343949;
        border-radius: 16px;
        padding: 35px 15px;
        margin-top: 18px;
    }

    .empty-icon {
        font-size: 34px;
        margin-bottom: 12px;
    }

    .empty-title {
        color: var(--text);
        font-size: 17px;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .empty-description {
        color: var(--muted);
        font-size: 13px;
        line-height: 1.8;
    }

    /* Markdown output */

    [data-testid="stMarkdownContainer"] {
        overflow-wrap: anywhere;
    }

    [data-testid="stMarkdownContainer"] pre {
        overflow-x: auto;
    }

    /* Tabs */

    button[data-baseweb="tab"] {
        font-size: 12px;
    }

    div[data-baseweb="tab-list"] {
        gap: 6px;
    }

    /* PDF download button */

    div[data-testid="stDownloadButton"] button {
        background: var(--surface-hover);
        color: var(--text);
        border: 1px solid var(--border);
        border-radius: 11px;
        min-height: 46px;
        font-weight: 600;
    }

    div[data-testid="stDownloadButton"] button:hover {
        border-color: var(--accent);
        color: #c4b5fd;
    }

    /* Footer */

    .footer {
        color: #70788a;
        text-align: center;
        font-size: 10px;
        letter-spacing: 0.8px;
        padding-top: 35px;
    }

    /* Mobile */

    @media (max-width: 640px) {
        .block-container {
            padding: 1rem 0.8rem 2rem;
        }

        .brand {
            margin-bottom: 1.1rem;
        }

        .hero {
            padding: 0.8rem 0 1rem;
        }

        .hero h1 {
            font-size: 34px;
            letter-spacing: -1px;
        }

        .hero-description {
            font-size: 12px;
        }

        .agent-card {
            padding: 15px 5px;
            min-height: 130px;
        }

        .agent-title {
            font-size: 11px;
        }

        .agent-description {
            font-size: 10px;
        }

        .agent-icon {
            font-size: 22px;
        }

        .section-heading {
            font-size: 20px;
        }

        .result-panel {
            padding: 14px;
        }

        button[data-baseweb="tab"] {
            font-size: 10px;
            padding-left: 5px;
            padding-right: 5px;
        }
    }

    @media (max-width: 360px) {
        .hero h1 {
            font-size: 29px;
        }

        .agent-card {
            padding: 12px 3px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 4. HEADER
# ============================================================

st.markdown(
    """
    <div class="brand">
        <div class="brand-icon">K</div>
        <div>
            <div class="brand-name">KAIRO</div>
            <div class="brand-subtitle">Intelligent Research</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 5. HERO
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">✦ MULTI-AGENT RESEARCH SYSTEM</div>
        <h1>
            Research deeper.<br>
            <span class="gradient-text">Understand better.</span>
        </h1>
        <p class="hero-description">
            Turn any research question into a structured report
            using AI-powered web search, content extraction,
            report writing and critical review.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 6. AGENT WORKFLOW
# ============================================================

agents = [
    ("🌐", "Search Agent", "Finds relevant web resources"),
    ("📖", "Reader Agent", "Extracts detailed page content"),
    ("✍️", "Writer", "Produces the research report"),
    ("🔍", "Critic", "Reviews quality and accuracy"),
]

columns = st.columns(4, gap="small")

for column, (icon, title, description) in zip(columns, agents):
    with column:
        st.markdown(
            f"""
            <div class="agent-card">
                <div class="agent-icon">{icon}</div>
                <div class="agent-title">{title}</div>
                <div class="agent-description">{description}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# 7. RESEARCH FORM
# ============================================================

st.markdown(
    '<div class="section-heading">Start your research</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="section-caption">
        Enter a topic. Your existing pipeline will handle the research.
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("research_form", clear_on_submit=False):
    topic = st.text_input(
        "Research topic",
        placeholder="e.g. Latest developments in AI agents",
        max_chars=500,
    )

    submitted = st.form_submit_button(
        "✦ Run Research",
        type="primary",
        use_container_width=True,
    )


# ============================================================
# 8. SESSION STATE
# ============================================================

if "research_result" not in st.session_state:
    st.session_state.research_result = None

if "research_topic" not in st.session_state:
    st.session_state.research_topic = ""


# ============================================================
# 9. RUN THE EXISTING PIPELINE
# ============================================================

if submitted:
    cleaned_topic = topic.strip()

    if not cleaned_topic:
        st.warning("Please enter a research topic first.")

    else:
        try:
            with st.spinner(
                "Your agents are researching, reading, writing "
                "and reviewing. Please wait..."
            ):
                result = run_research_pipeline(cleaned_topic)

            if not isinstance(result, dict):
                raise TypeError(
                    "run_research_pipeline() must return a dictionary."
                )

            st.session_state.research_result = result
            st.session_state.research_topic = cleaned_topic

            st.success("Research completed successfully.")

        except Exception as error:
            st.error(f"Research failed: {error}")
            st.info(
                "Check your .env API keys, internet connection, "
                "installed packages and terminal logs."
            )


# ============================================================
# 10. DISPLAY RESULTS
# ============================================================

result = st.session_state.research_result

if result is not None:

    report = result.get(
        "report",
        "No report was returned by the writer.",
    )

    feedback = result.get(
        "feedback",
        "No critic feedback was returned.",
    )

    search_results = result.get("search_results", "")
    scraped_content = result.get("scraped_content", "")
    research_topic = st.session_state.research_topic

    report_text = str(report)
    feedback_text = str(feedback)

    st.divider()

    st.markdown(
        '<div class="section-heading">Research results</div>',
        unsafe_allow_html=True,
    )

    safe_topic = html.escape(research_topic)

    st.markdown(
        f"""
        <div class="result-panel">
            <div class="result-label">Completed research</div>
            <div class="result-topic">{safe_topic}</div>
            <div>
                <span class="status-pill">● PIPELINE COMPLETED</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # GENERATE PDF AND DOWNLOAD
    # --------------------------------------------------------

    try:
        pdf_bytes = create_pdf(
            report_text=report_text,
            topic=research_topic,
            feedback_text=feedback_text,
        )

        safe_filename = re.sub(
            r"[^a-zA-Z0-9_-]+",
            "_",
            research_topic,
        ).strip("_")[:60]

        if not safe_filename:
            safe_filename = "research_report"

        st.download_button(
            label="⬇ Download Research Report (PDF)",
            data=pdf_bytes,
            file_name=f"kairo_{safe_filename}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    except Exception as error:
        st.error(f"Could not generate the PDF: {error}")

    st.write("")

    # --------------------------------------------------------
    # OUTPUT TABS
    # --------------------------------------------------------

    report_tab, critic_tab, search_tab, reader_tab = st.tabs(
        [
            "📄 Final Report",
            "🔎 Critic Review",
            "🌐 Search Results",
            "📖 Scraped Content",
        ]
    )

    with report_tab:
        st.markdown(
            '<div class="section-heading">Final research report</div>',
            unsafe_allow_html=True,
        )

        st.markdown(report_text)

    with critic_tab:
        st.markdown(
            '<div class="section-heading">Critic review</div>',
            unsafe_allow_html=True,
        )

        st.caption(
            "Review and improvement suggestions generated by your critic."
        )

        st.markdown(feedback_text)

    with search_tab:
        st.markdown(
            '<div class="section-heading">Web search results</div>',
            unsafe_allow_html=True,
        )

        st.caption(
            "Results collected by your Tavily-powered search agent."
        )

        if search_results:
            st.text(str(search_results))
        else:
            st.info("No search results were returned.")

    with reader_tab:
        st.markdown(
            '<div class="section-heading">Scraped page content</div>',
            unsafe_allow_html=True,
        )

        st.caption("Content extracted by your reader agent.")

        if scraped_content:
            st.text(str(scraped_content))
        else:
            st.info("No scraped content was returned.")

    st.caption(
        "Submit a new topic above to run another research pipeline."
    )

else:
    # --------------------------------------------------------
    # EMPTY STATE
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-icon">⌕</div>
            <div class="empty-title">
                Your next discovery starts here
            </div>
            <div class="empty-description">
                Enter a research topic above to launch all four stages.
                <br>
                Your report, search results and critic feedback will appear here.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 11. FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        KAIRO AI RESEARCH SYSTEM ·
        ENGINEER BY AYMAAN SHABBIR IBRAHIM · SOFTWARE ENGINEER @ TCS
    </div>
    """,
    unsafe_allow_html=True,
)
