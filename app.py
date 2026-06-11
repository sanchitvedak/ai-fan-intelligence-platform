import streamlit as st
import pandas as pd

st.set_page_config(page_title="Fan Intelligence Platform", layout="wide")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #fbfbff 0%, #fff7fb 45%, #f3f7ff 100%);
    color: #111827;
}

.block-container {
    padding-top: 2rem;
    max-width: 1250px;
}

.hero {
    padding: 54px 44px;
    border-radius: 34px;
    background: linear-gradient(135deg, #ffffff 0%, #f5efff 52%, #e9f7ff 100%);
    border: 1px solid #e5e7eb;
    box-shadow: 0 24px 70px rgba(124,58,237,.13);
    margin-bottom: 24px;
}

.badge {
    display: inline-block;
    padding: 10px 18px;
    border-radius: 999px;
    background: #ede9fe;
    color: #6d28d9;
    font-weight: 800;
    font-size: 15px;
    margin-bottom: 34px;
}

.hero h1 {
    font-size: 58px;
    line-height: 1.05;
    margin: 0 0 28px 0;
    color: #111827;
    font-weight: 900;
    letter-spacing: -1.8px;
}

.hero p {
    font-size: 22px;
    line-height: 1.65;
    color: #4b5563;
    max-width: 960px;
}

/* Full-width top navigation */
div[data-testid="stSegmentedControl"] {
    width: 100% !important;
    background: rgba(255,255,255,.94);
    border: 1px solid #e5e7eb;
    border-radius: 22px;
    padding: 8px;
    box-shadow: 0 14px 34px rgba(17,24,39,.08);
    margin-bottom: 34px;
}

div[data-testid="stSegmentedControl"] > div {
    width: 100% !important;
    display: flex !important;
}

div[data-testid="stSegmentedControl"] button {
    flex: 1 !important;
    min-height: 64px;
    border-radius: 16px !important;
    font-size: 18px !important;
    font-weight: 800 !important;
}

.action-panel {
    padding: 30px;
    border-radius: 28px;
    background: linear-gradient(135deg, #ecfeff 0%, #f5f3ff 100%);
    border: 1px solid #ddd6fe;
    box-shadow: 0 16px 38px rgba(79,70,229,.10);
    margin-bottom: 24px;
}

.action-panel h2 {
    color: #111827;
    font-size: 32px;
    margin-bottom: 12px;
}

.action-panel p {
    color: #374151;
    font-size: 19px;
    line-height: 1.55;
}

.card {
    padding: 26px;
    border-radius: 24px;
    background: rgba(255,255,255,.92);
    border: 1px solid #e5e7eb;
    box-shadow: 0 12px 30px rgba(17,24,39,.08);
    min-height: 165px;
}

.card h3 {
    color: #111827;
    margin-bottom: 8px;
    font-size: 20px;
}

.card p {
    color: #4b5563;
    font-size: 16px;
}

.metric-number {
    font-size: 38px;
    font-weight: 900;
    color: #7c3aed;
    margin: 10px 0;
}

.tip {
    padding: 20px 24px;
    border-radius: 20px;
    background: #fff7ed;
    border: 1px solid #fed7aa;
    color: #7c2d12;
    font-size: 18px;
    margin-top: 20px;
}

.soft-panel {
    background: white;
    border: 1px solid #ebe7dd;
    border-radius: 22px;
    padding: 30px;
    box-shadow: 0 12px 28px rgba(23,43,77,.07);
}

h1, h2, h3, p, label, div {
    color: #111827;
}

[data-testid="stMetricValue"] {
    color: #111827;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <div class="badge">✨ PM Showcase · AI Decision Product</div>
    <h1>🎟️ Fan Intelligence Platform</h1>
    <p>
    A simple decision engine for major live events. It tells fans what to do next:
    leave now, take transit, buy tickets, or pick a better watch spot.
    </p>
</div>
""", unsafe_allow_html=True)

page = st.segmented_control(
    "Navigation",
    [
        "Overview",
        "Decision Engine",
        "Signal Inputs",
        "AI Brief",
        "Product Roadmap"
    ],
    default="Overview",
    label_visibility="collapsed"
)

if page == "Overview":
    st.markdown("""
    <div class="action-panel">
        <h2>Today’s Recommendation: Take transit and leave early 🚆</h2>
        <p>
        The main risk is not the event itself — it is the arrival window.
        Fans who wait too long may face avoidable traffic delays.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="card">
            <h3>Fan Score</h3>
            <div class="metric-number">82</div>
            <p>Good overall experience expected.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="card">
            <h3>Main Risk</h3>
            <div class="metric-number">Traffic</div>
            <p>Peak arrival may create delays.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="card">
            <h3>Best Action</h3>
            <div class="metric-number">Transit</div>
            <p>Most reliable option today.</p>
        </div>
        """, unsafe_allow_html=True)

elif page == "Decision Engine":
    st.header("Should I leave now?")

    city = st.selectbox(
        "Where are you traveling from?",
        ["Montclair", "Verona", "Hoboken", "Jersey City", "NYC"]
    )

    travel_times = {
        "Montclair": 28,
        "Verona": 24,
        "Hoboken": 31,
        "Jersey City": 35,
        "NYC": 42
    }

    current_time = travel_times[city]
    peak_time = int(current_time * 1.75)
    delay = peak_time - current_time

    col1, col2, col3 = st.columns(3)
    col1.metric("Now", f"{current_time} mins")
    col2.metric("Near event", f"{peak_time} mins")
    col3.metric("Delay risk", f"+{delay} mins")

    st.markdown(f"""
    <div class="tip">
        Recommendation: If you are coming from <b>{city}</b>, leave early or take transit.
        Waiting until peak arrival could add about <b>{delay} minutes</b>.
    </div>
    """, unsafe_allow_html=True)

elif page == "Signal Inputs":
    st.header("Signals we are watching")

    signals = pd.DataFrame({
        "Signal": ["Traffic", "Transit", "Tickets", "Weather", "Watch parties"],
        "Status": ["Rising", "Moderate", "High demand", "Low risk", "Busy"],
        "Action": [
            "Leave earlier",
            "Prefer transit",
            "Avoid last-minute buying",
            "No major concern",
            "Arrive early"
        ]
    })

    st.dataframe(signals, use_container_width=True, hide_index=True)

elif page == "AI Brief":
    st.markdown("""
    <div class="soft-panel">
        <h2>🧠 AI Brief</h2>
        <p>
        Traffic is the biggest fan-experience risk today. Transit is the safer option.
        Ticket demand remains high, and busy watch parties are expected in high-energy areas.
        </p>
        <p>
        Best fan action: leave early, avoid last-minute ticket decisions, and pick your venue before peak crowd buildup.
        </p>
    </div>
    """, unsafe_allow_html=True)

elif page == "Product Roadmap":
    st.header("PM Roadmap")

    roadmap = pd.DataFrame({
        "Phase": ["V1", "V2", "V3", "V4"],
        "Build": [
            "Decision-support prototype",
            "Live weather + event data",
            "Traffic, ticket, transit integrations",
            "Personalized AI recommendations"
        ],
        "PM Value": [
            "Validate user problem",
            "Replace dummy signals",
            "Increase usefulness",
            "Scale into fan copilot"
        ]
    })

    st.dataframe(roadmap, use_container_width=True, hide_index=True)