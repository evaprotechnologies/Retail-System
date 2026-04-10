"""Shared Streamlit styling — visual layer only; no business logic."""

import streamlit as st

# Design tokens (aligned with .streamlit/config.toml)
_RS_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    :root {
        --rs-bg: #f1f5f9;
        --rs-surface: #ffffff;
        --rs-border: #e2e8f0;
        --rs-text: #0f172a;
        --rs-muted: #64748b;
        --rs-primary: #2563eb;
        --rs-primary-dark: #1d4ed8;
        --rs-sidebar: #0f172a;
        --rs-sidebar-muted: #94a3b8;
        --rs-success: #059669;
        --rs-radius: 12px;
        --rs-radius-sm: 8px;
        --rs-shadow: 0 1px 3px rgba(15, 23, 42, 0.06), 0 4px 12px rgba(15, 23, 42, 0.04);
    }

    .stApp {
        font-family: 'Inter', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif;
        color: var(--rs-text);
    }

    .main .block-container {
        padding-top: 1.25rem;
        padding-bottom: 2.5rem;
        max-width: 100%;
    }

    /* App chrome */
    header[data-testid="stHeader"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border-bottom: 1px solid var(--rs-border);
    }

    [data-testid="stAppViewContainer"] > .main {
        background: var(--rs-bg);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
        border-right: 1px solid #334155;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] .stMarkdown {
        color: #f8fafc;
    }
    [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] [data-testid="stCaption"] {
        color: var(--rs-sidebar-muted) !important;
    }
    [data-testid="stSidebar"] a {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: #334155;
    }

    /* Headings */
    .main h1, div[data-testid="stHeading"] h1 {
        font-weight: 700;
        letter-spacing: -0.02em;
        color: var(--rs-text);
        font-size: 1.65rem !important;
    }
    .main h2, .main h3 {
        font-weight: 600;
        color: var(--rs-text);
    }

    /* Page header block */
    .rs-page-header {
        background: var(--rs-surface);
        border: 1px solid var(--rs-border);
        border-radius: var(--rs-radius);
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: var(--rs-shadow);
    }
    .rs-page-header h1 {
        margin: 0 0 0.35rem 0 !important;
        font-size: 1.5rem !important;
        border: none;
    }
    .rs-page-header .rs-muted {
        margin: 0;
        color: var(--rs-muted);
        font-size: 0.95rem;
        line-height: 1.45;
    }

    /* Home hero */
    .rs-home-hero {
        background: linear-gradient(135deg, #1e3a5f 0%, #1e40af 55%, #2563eb 100%);
        color: #fff;
        border-radius: var(--rs-radius);
        padding: 1.75rem 1.75rem 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 40px rgba(37, 99, 235, 0.22);
    }
    .rs-home-hero h1 {
        color: #fff !important;
        font-size: 1.5rem !important;
        margin: 0.5rem 0 0.25rem 0 !important;
    }
    .rs-home-hero .rs-sub {
        margin: 0;
        opacity: 0.92;
        font-size: 1rem;
    }
    .rs-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .rs-badge--manager { background: rgba(16, 185, 129, 0.25); color: #6ee7b7; }
    .rs-badge--cashier { background: rgba(96, 165, 250, 0.25); color: #93c5fd; }

    .rs-feature-card {
        background: var(--rs-surface);
        border: 1px solid var(--rs-border);
        border-radius: var(--rs-radius-sm);
        padding: 1.25rem;
        height: 100%;
        box-shadow: var(--rs-shadow);
        border-left: 4px solid var(--rs-accent, var(--rs-primary));
    }
    .rs-feature-card h4, .rs-feature-card h5 {
        margin-top: 0;
        color: var(--rs-text);
    }
    .rs-feature-card p {
        color: var(--rs-muted);
        font-size: 0.9rem;
        margin-bottom: 0;
    }
    .rs-feature-card.muted {
        opacity: 0.72;
    }

    /* Login */
    .rs-login-wrap {
        max-width: 420px;
        margin: 0 auto;
    }
    .rs-login-card {
        background: var(--rs-surface);
        border: 1px solid var(--rs-border);
        border-radius: var(--rs-radius);
        padding: 2rem 2rem 1.75rem;
        box-shadow: 0 12px 40px rgba(15, 23, 42, 0.1);
    }
    .rs-login-brand {
        text-align: center;
        margin-bottom: 1.25rem;
    }
    .rs-login-brand .rs-logo {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 48px;
        height: 48px;
        border-radius: 12px;
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: #fff;
        font-weight: 700;
        font-size: 1.25rem;
        margin-bottom: 0.75rem;
    }
    .rs-login-brand h1 {
        font-size: 1.35rem !important;
        margin: 0 !important;
        color: var(--rs-text) !important;
    }
    .rs-login-brand .rs-tagline {
        color: var(--rs-muted);
        font-size: 0.9rem;
        margin: 0.35rem 0 0 0;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.25rem;
        background: var(--rs-surface);
        padding: 0.35rem;
        border-radius: var(--rs-radius-sm);
        border: 1px solid var(--rs-border);
        margin-bottom: 1rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        font-weight: 500;
    }

    /* Metrics */
    [data-testid="stMetric"] {
        background: var(--rs-surface);
        border: 1px solid var(--rs-border);
        border-radius: var(--rs-radius-sm);
        padding: 0.75rem 1rem;
        box-shadow: var(--rs-shadow);
    }

    /* Dataframes */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--rs-border);
        border-radius: var(--rs-radius-sm);
        overflow: hidden;
    }

    /* Alerts / info boxes */
    .stAlert {
        border-radius: var(--rs-radius-sm);
    }

    /* POS */
    .pos-container {
        background: var(--rs-surface);
        border: 1px solid var(--rs-border);
        border-radius: var(--rs-radius);
        padding: 1.25rem 1.35rem;
        margin-bottom: 0.5rem;
        box-shadow: var(--rs-shadow);
    }
    .total-display {
        background: linear-gradient(135deg, #0f766e 0%, #059669 100%);
        color: #fff;
        padding: 1.25rem 1rem;
        border-radius: var(--rs-radius-sm);
        text-align: center;
        font-size: 1.35rem;
        font-weight: 600;
        margin: 0.75rem 0 1rem;
        line-height: 1.5;
        box-shadow: 0 4px 14px rgba(5, 150, 105, 0.25);
    }

    /* Primary buttons emphasis */
    .stButton button[kind="primary"] {
        font-weight: 600;
        border-radius: 8px;
    }
</style>
"""


def inject_global_styles() -> None:
    """Inject global CSS once per run (safe to call from every page)."""
    st.markdown(_RS_CSS, unsafe_allow_html=True)


def render_page_heading(title: str, subtitle: str | None = None) -> None:
    """Consistent page title + optional description (display only)."""
    sub = f'<p class="rs-muted">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f'<div class="rs-page-header"><h1>{_html_escape(title)}</h1>{sub}</div>',
        unsafe_allow_html=True,
    )


def render_home_hero(role_title: str, full_name: str) -> None:
    """Landing hero when logged in (app home)."""
    r = str(role_title).lower()
    badge_class = "rs-badge--manager" if r == "manager" else "rs-badge--cashier"
    st.markdown(
        f"""
<div class="rs-home-hero">
  <span class="rs-badge {badge_class}">{role_title}</span>
  <h1>Welcome back</h1>
  <p class="rs-sub">{_html_escape(full_name)}</p>
</div>
""",
        unsafe_allow_html=True,
    )


def render_login_shell_start() -> None:
    """Opening markup for login card (paired with render_login_shell_end)."""
    st.markdown(
        '<div class="rs-login-wrap"><div class="rs-login-card">'
        '<div class="rs-login-brand"><div class="rs-logo">RS</div>'
        "<h1>Retail Management</h1>"
        '<p class="rs-tagline">Employee sign-in</p></div>',
        unsafe_allow_html=True,
    )


def render_login_shell_end() -> None:
    st.markdown("</div></div>", unsafe_allow_html=True)


def _html_escape(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
