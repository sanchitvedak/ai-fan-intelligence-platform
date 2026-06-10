import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="NJ World Cup AI Fan Pulse", layout="wide")

st.title("🎟️ Fan Intelligence Platform")

st.markdown("""
### Make smarter event decisions

Get AI-powered recommendations for:
- 🚗 When to leave
- 🚆 Best transportation options
- 🎟️ Ticket buying opportunities
- 🍺 Watch party recommendations
- 📈 Crowd and demand forecasts
""")

data = pd.DataFrame({
    "Country": ["Argentina", "Brazil", "England", "France", "Mexico", "USA", "India", "Germany"],
    "Fans Estimated": [12000, 15000, 9000, 8500, 18000, 22000, 6000, 7000],
    "Avg Ticket Price": [920, 880, 760, 810, 690, 740, 620, 700],
    "Transit Usage %": [62, 58, 71, 64, 55, 68, 74, 69],
    "Fan Sentiment": [92, 89, 76, 81, 94, 84, 88, 79],
    "Pub/Event Mentions": [430, 510, 390, 360, 620, 700, 280, 310]
})

col1, col2, col3, col4 = st.columns(4)
col1.metric("Estimated Fans", f"{data['Fans Estimated'].sum():,}")
col2.metric("Avg Ticket Price", f"${int(data['Avg Ticket Price'].mean())}")
col3.metric("Avg Transit Usage", f"{int(data['Transit Usage %'].mean())}%")
col4.metric("Fan Happiness Score", f"{int(data['Fan Sentiment'].mean())}/100")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("🌎 Fan Nations Around NJ")
    fig = px.bar(data, x="Country", y="Fans Estimated", title="Estimated Fans by Country")
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("🎟️ Ticket Price Watch")
    fig = px.scatter(
        data,
        x="Fans Estimated",
        y="Avg Ticket Price",
        size="Pub/Event Mentions",
        color="Country",
        title="Ticket Price vs Fan Demand"
    )
    st.plotly_chart(fig, use_container_width=True)

left2, right2 = st.columns(2)

with left2:
    st.subheader("🚆 Transit Readiness")
    fig = px.bar(data, x="Country", y="Transit Usage %", title="Estimated Public Transit Usage")
    st.plotly_chart(fig, use_container_width=True)

with right2:
    st.subheader("🔥 Fan Energy Index")
    data["Fan Energy Index"] = (
        data["Fan Sentiment"] * 0.4 +
        data["Pub/Event Mentions"] / data["Pub/Event Mentions"].max() * 40 +
        data["Transit Usage %"] * 0.2
    )
    fig = px.bar(data.sort_values("Fan Energy Index", ascending=False), x="Country", y="Fan Energy Index")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("🤖 AI-Generated Insight")
top_country = data.sort_values("Fan Energy Index", ascending=False).iloc[0]
st.success(
    f"{top_country['Country']} currently has the highest Fan Energy Index. "
    f"This combines fan sentiment, event chatter, and expected public transit usage."
)

st.subheader("📍 Product Manager Angle")
st.write("""
This dashboard demonstrates how AI can combine messy public signals — travel behavior, event chatter,
ticket pricing, and fan sentiment — into a simple decision-support product for fans, venues, cities,
transit agencies, and local businesses.
""")
