import streamlit as st


def apply_roboai_libs_theme():
    st.markdown(
        """
        <style>

        :root {
            --bg: #0c0d11;
            --sidebar: #111216;
            --surface: #131419;
            --surface-hover: #18191f;
            --border: #2b2d34;

            --text: #f2f2f4;
            --muted: #9698a3;

            --accent: #6257e8;
            --accent-hover: #7167f1;

            --radius: 10px;
        }


        /* ======================================================
           MAIN APP
           ====================================================== */

        .stApp {
            background: var(--bg);
            color: var(--text);
        }

        .block-container {
            max-width: 1180px;
            padding-top: 2rem;
            padding-bottom: 3rem;
            padding-left: 2.25rem;
            padding-right: 2.25rem;
        }


        /* ======================================================
           TYPOGRAPHY
           ====================================================== */

        h1 {
            font-size: 2.15rem !important;
            line-height: 1.15 !important;
            font-weight: 700 !important;
            letter-spacing: -0.035em !important;
            margin-bottom: 2.2rem !important;
            color: var(--text) !important;
        }

        h2 {
            font-size: 1.45rem !important;
            line-height: 1.25 !important;
            font-weight: 650 !important;
            letter-spacing: -0.025em !important;
            margin-top: 1.2rem !important;
            margin-bottom: 0.9rem !important;
            color: var(--text) !important;
        }

        h3 {
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            color: var(--text) !important;
        }

        p {
            color: var(--text);
        }

        [data-testid="stCaptionContainer"] {
            color: var(--muted) !important;
        }

        label {
            font-size: 0.9rem !important;
            font-weight: 500 !important;
        }


        /* ======================================================
           SIDEBAR
           ====================================================== */

        [data-testid="stSidebar"] {
            background: var(--sidebar);
            border-right: 1px solid #23252b;
        }

        [data-testid="stSidebarContent"] {
            padding-top: 0.75rem;
        }

        [data-testid="stSidebar"] hr {
            border-color: #25272d;
        }


        /* ======================================================
           ALERT / INFO BOX
           LIBS uses subtle dark cards, not bright blue.
           ====================================================== */

        [data-testid="stAlert"] {
            background: var(--surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius) !important;
            padding: 0.85rem 1rem !important;
            box-shadow: none !important;
        }

        [data-testid="stAlert"] > div {
            color: var(--text) !important;
        }

        [data-testid="stAlert"] svg {
            color: var(--accent) !important;
        }


        /* ======================================================
           INPUTS
           ====================================================== */

        [data-baseweb="input"] > div,
        [data-baseweb="select"] > div,
        [data-baseweb="textarea"] > div {
            background: #0e0f13 !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
            box-shadow: none !important;
        }

        [data-baseweb="input"] > div:focus-within,
        [data-baseweb="select"] > div:focus-within,
        [data-baseweb="textarea"] > div:focus-within {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 1px var(--accent) !important;
        }


        /* ======================================================
           BUTTONS
           ====================================================== */

        .stButton > button,
        .stDownloadButton > button {
            min-height: 38px !important;
            border-radius: 8px !important;

            background: var(--surface) !important;
            color: var(--text) !important;

            border: 1px solid var(--border) !important;

            font-weight: 550 !important;
            padding: 0.35rem 0.85rem !important;

            box-shadow: none !important;

            transition:
                background 0.15s ease,
                border-color 0.15s ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            background: var(--surface-hover) !important;
            border-color: #41434c !important;
        }

        .stButton > button[kind="primary"] {
            background: var(--accent) !important;
            border-color: var(--accent) !important;
            color: white !important;
        }

        .stButton > button[kind="primary"]:hover {
            background: var(--accent-hover) !important;
            border-color: var(--accent-hover) !important;
        }


        /* ======================================================
           FILE UPLOADER
           ====================================================== */

        [data-testid="stFileUploader"] {
            margin-top: 0.15rem !important;
        }

        [data-testid="stFileUploader"] section {
            background: #101116 !important;

            border: 1px dashed #30323a !important;
            border-radius: var(--radius) !important;

            min-height: 76px !important;

            padding: 0.75rem 1rem !important;

            box-shadow: none !important;
        }

        [data-testid="stFileUploader"] section:hover {
            border-color: #494b55 !important;
            background: #121318 !important;
        }

        [data-testid="stFileUploader"] button {
            border-radius: 8px !important;
            background: #14151b !important;
            border: 1px solid #30323a !important;
            min-height: 38px !important;
        }

        [data-testid="stFileUploader"] small {
            color: var(--muted) !important;
        }


        /* ======================================================
           EXPANDERS / CARD-LIKE AREAS
           ====================================================== */

        [data-testid="stExpander"] {
            background: var(--surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius) !important;
            box-shadow: none !important;
        }


        /* ======================================================
           TABS
           ====================================================== */

        [data-testid="stTabs"] [role="tablist"] {
            gap: 0.25rem;
        }

        [data-testid="stTabs"] [role="tab"] {
            height: 36px !important;

            background: transparent;
            border: 1px solid transparent;

            border-radius: 7px;

            padding: 0 0.8rem;

            color: var(--muted);
        }

        [data-testid="stTabs"] [aria-selected="true"] {
            background: #191922 !important;
            border-color: var(--border) !important;
            color: white !important;
        }


        /* ======================================================
           RADIO BUTTON GROUPS
           ====================================================== */

        [data-testid="stRadio"] > div {
            gap: 0.15rem !important;
        }

        [data-testid="stRadio"] label {
            border-radius: 7px !important;
        }


        /* ======================================================
           DATA / PLOTS
           ====================================================== */

        [data-testid="stDataFrame"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            overflow: hidden;
        }

        div.stPlotlyChart {
            border-radius: var(--radius);
            overflow: hidden;
        }


        /* ======================================================
           MISC
           ====================================================== */

        hr {
            border: none;
            border-top: 1px solid var(--border);
        }

        a {
            color: #8278f4 !important;
        }

        /* Reduce excessive Streamlit spacing */
        [data-testid="stVerticalBlock"] {
            gap: 0.85rem;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: var(--radius) !important;
        }
/* ======================================================
   ROBOAI LOGOS
   ====================================================== */

.roboai-main-logo {
    width: 100%;
    display: flex;
    justify-content: center;
    align-items: center;

    margin-top: 0.25rem;
    margin-bottom: 1.8rem;
}

.roboai-main-logo img {
    width: min(420px, 52vw);
    height: auto;

    /*
    Original logo is black.
    Convert it to white for the dark interface.
    */
    filter: invert(1);

    opacity: 0.96;
}


/* Sidebar logo */

.roboai-sidebar-logo {
    width: 100%;
    display: flex;
    align-items: center;

    margin-top: 0.35rem;
    margin-bottom: 0.5rem;
}

.roboai-sidebar-logo img {
    width: 185px;
    max-width: 88%;
    height: auto;

    filter: invert(1);
}

.sidebar-product-name {
    color: var(--text);

    font-size: 1rem;
    font-weight: 650;

    margin-top: 0.15rem;
    margin-bottom: 0.1rem;
}
        </style>
        """,
        unsafe_allow_html=True,
    )
