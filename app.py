import streamlit as st
import pandas as pd

st.set_page_config(page_title="Fan Intelligence Platform", layout="wide")

st.title("🎟️ Fan Intelligence Platform")
st.caption("AI-powered event insights that help fans make smarter decisions.")

tabs = st.tabs([
    "🏠 Overview",
    "🚗 Matchday Advisor",
    "🍺 Watch Parties",
    "🎟 Ticket Intelligence",
    "🤖 Daily AI Insight"
])

with tabs[0]:
    st.header("Event Intelligence Overview")
    st.metric("Fan Experience Score", "82 / 100")
    st.metric("Crowd Risk", "Medium")
    st.metric("Transit Recommendation", "Use NJ Transit")

with tabs[1]:
    st.header("🚗 Matchday Advisor")

    city = st.selectbox(
        "Where are you traveling from?",
        ["Montclair", "Verona", "Hoboken", "Jersey City", "NYC"]
    )

    kickoff = st.selectbox(
        "Event Start Time",
        ["1:00 PM", "4:00 PM", "7:00 PM"]
    )

    travel_times = {
        "Montclair": 28,
        "Verona": 24,
        "Hoboken": 31,
        "Jersey City": 35,
        "NYC": 42
    }

    current_time = travel_times[city]
    predicted_time = int(current_time * 1.75)

    col1, col2 = st.columns(2)
    col1.metric("Current Travel Time", f"{current_time} mins")
    col2.metric("Predicted Travel Time Near Event", f"{predicted_time} mins")

    st.success(
        f"""
Recommended action: Leave at least 90 minutes before the event.

From {city}, travel time may increase from {current_time} mins to {predicted_time} mins near event time.

Best recommendation: Use transit if possible and avoid driving close to kickoff.
"""
    )

with tabs[2]:
    st.header("🍺 Watch Party Finder")

    watch_parties = pd.DataFrame({
        "Venue": ["Montclair Brewery", "Hoboken Biergarten", "Verona Inn", "Jersey City Barcade"],
        "Best For": ["Local fans", "High-energy crowd", "Low wait", "Group hangout"],
        "Crowd Forecast": ["Medium", "High", "Low", "Medium"],
        "Suggested Action": [
            "Arrive 45 mins early",
            "Reserve if possible",
            "Good backup option",
            "Best for groups"
        ]
    })

    st.dataframe(watch_parties, use_container_width=True)

with tabs[3]:
    st.header("🎟 Ticket Intelligence")

    st.metric("Current Ticket Demand", "High")
    st.metric("Predicted Direction", "⬆️ Rising")
    st.metric("Buy / Wait Recommendation", "Buy Early")

    st.warning(
        "Ticket demand is elevated. If this were live data, AI would compare current prices against historical movement and recommend whether to buy now or wait."
    )

with tabs[4]:
    st.header("🤖 Daily AI Insight")

    st.info(
        """
Today's Fan Intelligence Briefing:

Traffic risk is expected to rise closer to event time.

Fans traveling from Montclair, Verona, Hoboken, Jersey City, and NYC should plan for longer travel times.

Transit is currently the safer recommendation compared to driving.

Watch parties in Hoboken are expected to have the highest crowd energy.
"""
    )