"""
Design system for "Breaking the Link".

Visual direction: a fullscreen instrument-panel map (in the spirit of
Electricity Maps' live view), now in a light register — a soft grey void,
white glass HUD panels floating over the map, and a signal-teal accent
reserved for interactive chrome so it never competes with the Tapio
decoupling palette itself.

Spacing: the floating panels (topbar / sidepanel / timeline dock) are
positioned with CSS custom properties (--gap, --panel-w) instead of
independently-chosen pixel values, so the sidepanel's width and the
timeline dock's right-inset can never drift out of sync with each other.

IMPORTANT: all raw markup in this module goes through `st.html()`, not
`st.markdown(..., unsafe_allow_html=True)`. The latter still runs content
through the Markdown parser before the HTML passthrough — which mangles
multi-line indented CSS (interpreted as an indented code block) and eats
leading `*` characters (interpreted as a bullet-list marker). `st.html()`
inserts raw, sanitized HTML/CSS directly with no Markdown pass, which is
what dense CSS blocks like this need.
"""

import streamlit as st

# ─────────────────────────────────────────
# TOKENS — light theme
# ─────────────────────────────────────────

COLORS = {
    "void":          "#E9EBEC",   # page background — soft grey, not black
    "void_deep":     "#DEE1E3",
    "land":          "#D7DBDD",   # countries with no data
    "land_line":     "rgba(0,0,0,0.07)",
    "ocean":         "#C9D6DA",
    "panel":         "rgba(255,255,255,0.86)",   # glass panel fill
    "panel_solid":   "#FFFFFF",
    "panel_border":  "rgba(15,23,31,0.08)",
    "hairline":      "rgba(15,23,31,0.10)",
    "text":          "#1B2126",
    "text_dim":      "#5B6670",
    "text_faint":    "#8A939C",
    "accent":        "#1E8F82",   # signal teal — UI chrome only, never data
    "accent_dim":    "rgba(30,143,130,0.12)",
    "accent_line":   "rgba(30,143,130,0.40)",
    "warn":          "#B96A17",
    "shadow":        "rgba(15,23,31,0.14)",
}

FONT_DISPLAY = "'Space Grotesk', sans-serif"
FONT_BODY = "'Inter', sans-serif"
FONT_MONO = "'JetBrains Mono', monospace"

FONT_IMPORT_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Space+Grotesk:wght@400;500;600;700&"
    "family=Inter:wght@400;500;600&"
    "family=JetBrains+Mono:wght@400;500&display=swap"
)


def inject_base_css():
    css = f"""
<style>
@import url('{FONT_IMPORT_URL}');

:root {{
    --gap: 20px;              /* margin from viewport edge for every floating panel */
    --panel-w: 300px;         /* right-hand HUD panel width */
    --panel-gap: 16px;        /* space between the HUD panel and the timeline dock */
    --topbar-h: 64px;         /* approximate rendered height of the topbar row */
    --radius: 14px;
}}

/* ---------- reset the Streamlit chrome ---------- */
/* display:none (not visibility:hidden) so these elements stop reserving
   layout space entirely -- visibility:hidden was leaving a tall empty
   "banner" strip at the very top of the page, since Streamlit's header
   still occupied its normal box even though invisible. */
#MainMenu, footer, header, [data-testid="stHeader"] {{
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
}}
[data-testid="stToolbar"] {{ display: none !important; }}
[data-testid="stDecoration"] {{ display: none !important; }}
[data-testid="stStatusWidget"] {{ display: none !important; }}
[data-testid="stAppViewBlockContainer"] {{ padding-top: 0 !important; }}
.block-container {{
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
}}
/* a transform/filter/contain/perspective on any ancestor of our fixed HUD
   panels would make that ancestor -- not the viewport -- the containing
   block for position:fixed, throwing off every inset:0/top:.. calculation
   above. Neutralize that on Streamlit's own wrapper elements defensively. */
html, body,
div[data-testid="stAppViewContainer"],
section[data-testid="stMain"],
div[data-testid="stMainBlockContainer"],
div[data-testid="stApp"] {{
    transform: none !important;
    filter: none !important;
    perspective: none !important;
    contain: none !important;
    margin: 0 !important;
    padding: 0 !important;
    height: auto !important;
    min-height: 100vh !important;
}}
div[data-testid="stAppViewContainer"] {{ background: {COLORS['void']}; }}
section[data-testid="stMain"] {{ background: {COLORS['void']}; }}
body, html {{ background: {COLORS['void']}; }}

body, .stApp {{ font-family: {FONT_BODY}; color: {COLORS['text']}; }}
h1, h2, h3, .display-font {{ font-family: {FONT_DISPLAY}; }}
.mono {{ font-family: {FONT_MONO}; }}

div[data-testid="stVerticalBlock"] {{ gap: 0 !important; }}
div[data-testid="element-container"] {{ margin: 0 !important; }}

/* shared glass-panel shell, reused by every floating HUD element so they
   can never visually drift apart from each other */
.hud-panel, .st-key-topbar .brand-wrap, .st-key-navpill div[role="radiogroup"],
.st-key-sidepanel, .st-key-timeline {{
    background: {COLORS['panel']};
    backdrop-filter: blur(18px) saturate(140%);
    -webkit-backdrop-filter: blur(18px) saturate(140%);
    border: 1px solid {COLORS['panel_border']};
    box-shadow: 0 6px 24px {COLORS['shadow']};
}}

/* ---------- topbar ---------- */
.st-key-topbar {{
    position: fixed;
    top: var(--gap); left: var(--gap); right: var(--gap);
    z-index: 999;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    pointer-events: none;
}}
.st-key-topbar > div {{ pointer-events: auto; }}
.brand-wrap {{
    border-radius: var(--radius);
    padding: 10px 18px;
    display: inline-flex;
    flex-direction: column;
    line-height: 1.1;
    white-space: nowrap;
}}
.brand-title {{
    font-family: {FONT_DISPLAY};
    font-weight: 700;
    font-size: 1.05rem;
    color: {COLORS['text']};
    letter-spacing: -0.01em;
}}
.brand-sub {{
    font-size: 0.68rem;
    color: {COLORS['text_dim']};
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 2px;
}}

.st-key-navpill_align {{ display: flex; justify-content: center; }}

.st-key-navpill div[role="radiogroup"] {{
    border-radius: 999px;
    padding: 5px;
    display: flex;
    gap: 2px;
}}
.st-key-navpill label {{
    border-radius: 999px !important;
    padding: 7px 16px !important;
    transition: all 0.15s ease;
    margin: 0 !important;
}}
.st-key-navpill label:has(input:checked) {{ background: {COLORS['accent_dim']} !important; }}
.st-key-navpill label p {{
    font-family: {FONT_DISPLAY} !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    color: {COLORS['text_dim']} !important;
    letter-spacing: 0.01em;
}}
.st-key-navpill label:has(input:checked) p {{ color: {COLORS['accent']} !important; }}
.st-key-navpill [data-baseweb="radio"] > div:first-child {{ display: none; }}

/* ---------- right HUD panel ---------- */
.st-key-sidepanel {{
    position: fixed;
    top: calc(var(--gap) + var(--topbar-h) + var(--panel-gap));
    right: var(--gap);
    width: var(--panel-w);
    /* The sidepanel sits in the top-right corner; the timeline dock sits
       bottom-left/center and its right edge stops --panel-gap short of the
       sidepanel's left edge (see .st-key-timeline below) -- the two never
       share vertical space. There is no layout reason to reserve extra
       room at the bottom for the timeline, so the sidepanel's bottom
       margin should simply mirror its top gap, not an unrelated fixed
       pixel count. The old "- 190px" term was dead margin that truncated
       the legend / country trend chart earlier than necessary, forcing an
       unneeded scrollbar. */
    max-height: calc(100vh - var(--gap) - var(--topbar-h) - var(--panel-gap) - var(--gap));
    overflow-y: auto;
    overflow-anchor: none;   /* stop the browser auto-scrolling this box as
                                 Streamlit streams content into it */
    z-index: 998;
    border-radius: var(--radius);
    padding: 4px;
}}
.st-key-sidepanel::-webkit-scrollbar {{ width: 5px; }}
.st-key-sidepanel::-webkit-scrollbar-thumb {{ background: rgba(15,23,31,0.18); border-radius: 3px; }}
.st-key-sidepanel .hud-pad {{ padding: 0 16px; }}
.st-key-sidepanel [data-testid="stExpander"] {{ margin: 0 16px 16px 16px; }}
.st-key-country_select_wrap {{ padding: 0 16px; }}
.st-key-hud_kv_wrap {{ padding: 0 16px; }}

/* ---------- bottom timeline dock ---------- */
/* right-inset is derived from the same --panel-w/--gap tokens as the
   sidepanel, so the two can never drift out of alignment with each other */
.st-key-timeline {{
    position: fixed;
    bottom: var(--gap);
    left: var(--gap);
    right: calc(var(--panel-w) + var(--gap) + var(--panel-gap));
    z-index: 998;
    border-radius: var(--radius);
    padding: 12px 22px 6px 22px;
}}

/* ---------- fullbleed map holder ---------- */
.st-key-mapstage {{ position: fixed; inset: 0; z-index: 1; }}

/* ---------- generic HUD typography ---------- */
.hud-label {{
    font-size: 0.66rem;
    font-weight: 600;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: {COLORS['text_faint']};
}}
.hud-value {{ font-family: {FONT_MONO}; color: {COLORS['text']}; }}
.hud-divider {{ border: none; border-top: 1px solid {COLORS['hairline']}; margin: 10px 0; }}

/* sliders */
div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {{
    background-color: {COLORS['accent']} !important;
    box-shadow: 0 0 0 4px {COLORS['accent_dim']};
}}
div[data-testid="stSlider"] div[data-testid="stTickBar"] {{ display:none; }}
div[data-baseweb="slider"] > div > div {{ background: {COLORS['accent']} !important; }}
div[data-baseweb="slider"] > div {{ background: rgba(15,23,31,0.12) !important; }}

/* toggle switch */
div[data-testid="stToggle"] label div[data-checked="true"] {{ background-color: {COLORS['accent']} !important; }}

/* selectbox */
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
    background: rgba(15,23,31,0.03);
    border-color: {COLORS['hairline']};
    color: {COLORS['text']};
}}

/* expander */
details {{ background: transparent !important; }}

/* scrollbar (global) */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-thumb {{ background: rgba(15,23,31,0.18); border-radius: 3px; }}

/* ---------- narrower windows: shrink the panel instead of overlapping ---------- */
@media (max-width: 1150px) {{
    :root {{ --panel-w: 250px; --gap: 14px; }}
    .brand-sub {{ display: none; }}
}}
@media (max-width: 880px) {{
    :root {{ --panel-w: 210px; }}
    .st-key-timeline {{ padding: 8px 14px 4px 14px; }}
}}
</style>
"""
    st.html(css)


def hud_kv(label: str, value: str, accent: bool = False):
    """One label/value row for the HUD panel."""
    color = COLORS["accent"] if accent else COLORS["text"]
    st.html(f"""
<div style="display:flex; justify-content:space-between; align-items:baseline; padding:3px 0;">
    <span class="hud-label">{label}</span>
    <span class="hud-value" style="font-size:0.82rem; color:{color};">{value}</span>
</div>
""")


def pin_sidepanel_scroll():
    """Belt-and-suspenders fix alongside the `overflow-anchor: none` CSS rule
    above: the sidepanel streams in several widgets (stat block, legend,
    expander) across a single rerun, and browsers can auto-scroll a fixed,
    scrollable container to keep a newly-focused or newly-inserted element
    in view -- which visually crops the top of the panel. Call this once,
    after the sidepanel's content is fully rendered, to force it back to the
    top a few times as those late elements (e.g. the Plotly chart) settle.
    """
    st.html("""
<script>
(function() {
    function pin() {
        var panel = document.querySelector('.st-key-sidepanel');
        if (panel) { panel.scrollTop = 0; }
    }
    pin();
    [50, 150, 300, 600, 1000].forEach(function(t) { setTimeout(pin, t); });
})();
</script>
""", unsafe_allow_javascript=True)
