import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Fan Intelligence Platform", layout="wide")


# -----------------------------
# Live Weather Helper
# -----------------------------

@st.cache_data(ttl=900)
def get_metlife_weather():
    latitude = 40.8135
    longitude = -74.0745

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        "&current=temperature_2m,precipitation,rain,weather_code,wind_speed_10m"
        "&hourly=precipitation_probability"
        "&temperature_unit=fahrenheit"
        "&wind_speed_unit=mph"
        "&timezone=America%2FNew_York"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        weather = response.json()

        current = weather.get("current", {})
        hourly = weather.get("hourly", {})

        rain_probability = None
        if "precipitation_probability" in hourly and hourly["precipitation_probability"]:
            rain_probability = hourly["precipitation_probability"][0]

        return {
            "temperature": current.get("temperature_2m"),
            "precipitation": current.get("precipitation"),
            "rain": current.get("rain"),
            "wind_speed": current.get("wind_speed_10m"),
            "rain_probability": rain_probability,
            "weather_code": current.get("weather_code"),
            "source": "Live weather from Open-Meteo"
        }

    except Exception:
        return {
            "temperature": None,
            "precipitation": None,
            "rain": None,
            "wind_speed": None,
            "rain_probability": None,
            "weather_code": None,
            "source": "Weather unavailable"
        }


def weather_condition_label(code):
    weather_map = {
        0: "Clear",
        1: "Mostly clear",
        2: "Partly cloudy",
        3: "Cloudy",
        45: "Fog",
        48: "Fog",
        51: "Light drizzle",
        53: "Drizzle",
        55: "Heavy drizzle",
        61: "Light rain",
        63: "Rain",
        65: "Heavy rain",
        71: "Light snow",
        73: "Snow",
        75: "Heavy snow",
        80: "Rain showers",
        81: "Rain showers",
        82: "Heavy rain showers",
        95: "Thunderstorm",
        96: "Thunderstorm with hail",
        99: "Thunderstorm with hail"
    }

    if code is None:
        return "Unavailable"

    return weather_map.get(code, "Mixed conditions")


def weather_recommendation(weather):
    temp = weather.get("temperature")
    rain_prob = weather.get("rain_probability")
    wind = weather.get("wind_speed")

    if temp is None:
        return "Weather data is currently unavailable. Use traffic and transit signals for now."

    recommendation_parts = []

    if rain_prob is not None and rain_prob >= 50:
        recommendation_parts.append("Carry rain gear and allow extra travel time.")
    elif rain_prob is not None and rain_prob >= 25:
        recommendation_parts.append("Pack a light jacket or umbrella just in case.")
    else:
        recommendation_parts.append("Weather risk looks low right now.")

    if wind is not None and wind >= 20:
        recommendation_parts.append("Wind may affect outdoor comfort near the stadium.")

    if temp >= 85:
        recommendation_parts.append("Hydration will matter for fans arriving early.")
    elif temp <= 45:
        recommendation_parts.append("Dress warmly, especially if using transit or walking.")

    return " ".join(recommendation_parts)


def calculate_weather_score(weather):
    temp = weather.get("temperature")
    rain_prob = weather.get("rain_probability") or 0
    wind = weather.get("wind_speed") or 0

    if temp is None:
        return 60

    score = 90

    if rain_prob >= 60:
        score -= 25
    elif rain_prob >= 30:
        score -= 12

    if wind >= 25:
        score -= 15
    elif wind >= 18:
        score -= 8

    if temp >= 90 or temp <= 35:
        score -= 18
    elif temp >= 85 or temp <= 45:
        score -= 8

    return max(40, min(score, 100))


def generate_fan_brief(weather):
    temp = weather.get("temperature")
    rain_prob = weather.get("rain_probability")
    wind = weather.get("wind_speed")
    condition = weather_condition_label(weather.get("weather_code"))

    if temp is None:
        return {
            "headline": "Use travel signals first today.",
            "brief": "Live weather is currently unavailable, so the platform is prioritizing traffic, transit, and arrival-window risk.",
            "recommendation": "Leave early and check transit before departing.",
            "confidence": "62%"
        }

    weather_score = calculate_weather_score(weather)

    if weather_score >= 80:
        weather_read = "Weather conditions are favorable for fans."
    elif weather_score >= 65:
        weather_read = "Weather conditions are manageable, but fans should prepare for minor comfort risks."
    else:
        weather_read = "Weather may create friction for fans arriving early or spending time outside."

    if rain_prob is None:
        rain_text = "Rain probability is unavailable."
    else:
        rain_text = f"Rain risk is currently {rain_prob}%."

    if wind is None:
        wind_text = "Wind data is unavailable."
    else:
        wind_text = f"Wind speed is around {round(wind)} mph."

    brief = (
        f"{weather_read} Current conditions near MetLife are {condition.lower()}, "
        f"with temperature around {round(temp)}°F. {rain_text} {wind_text} "
        "The bigger fan-experience risk remains arrival congestion rather than weather."
    )

    recommendation = (
        "Take transit where possible, leave before peak arrival windows, "
        "and avoid making last-minute ticket or venue decisions."
    )

    confidence = "82%" if weather_score >= 75 else "74%"

    return {
        "headline": "Leave early. Transit is still the safer default.",
        "brief": brief,
        "recommendation": recommendation,
        "confidence": confidence
    }


weather = get_metlife_weather()
condition_label = weather_condition_label(weather.get("weather_code"))
weather_tip = weather_recommendation(weather)
weather_score = calculate_weather_score(weather)
fan_brief = generate_fan_brief(weather)


# -----------------------------
# Styling
# -----------------------------

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

.live-card {
    padding: 24px;
    border-radius: 24px;
    background: linear-gradient(135deg, #ffffff 0%, #ecfeff 100%);
    border: 1px solid #bae6fd;
    box-shadow: 0 12px 30px rgba(14,165,233,.10);
    min-height: 165px;
}

.live-card h3 {
    color: #0f172a;
    font-size: 20px;
    margin-bottom: 8px;
}

.live-card p {
    color: #475569;
    font-size: 16px;
}

.live-badge {
    display: inline-block;
    padding: 7px 12px;
    border-radius: 999px;
    background: #dcfce7;
    color: #166534;
    font-weight: 800;
    font-size: 13px;
    margin-bottom: 12px;
}

.soft-panel {
    background: white;
    border: 1px solid #ebe7dd;
    border-radius: 22px;
    padding: 30px;
    box-shadow: 0 12px 28px rgba(23,43,77,.07);
}

.brief-card {
    padding: 34px;
    border-radius: 28px;
    background: linear-gradient(135deg, #ffffff 0%, #f8f5ff 60%, #eef9ff 100%);
    border: 1px solid #ddd6fe;
    box-shadow: 0 18px 42px rgba(124,58,237,.12);
}

.brief-card h2 {
    font-size: 34px;
    margin-bottom: 14px;
}

.brief-card p {
    color: #374151;
    font-size: 19px;
    line-height: 1.65;
}

.confidence-pill {
    display: inline-block;
    padding: 10px 16px;
    border-radius: 999px;
    background: #ecfdf5;
    color: #166534;
    font-weight: 900;
    margin-top: 10px;
}

h1, h2, h3, p, label, div {
    color: #111827;
}

[data-testid="stMetricValue"] {
    color: #111827;
}
</style>
""", unsafe_allow_html=True)


# -----------------------------
# Hero
# -----------------------------

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


# -----------------------------
# Navigation
# -----------------------------

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


# -----------------------------
# Pages
# -----------------------------

if page == "Overview":
    st.markdown(f"""
    <div class="action-panel">
        <h2>{fan_brief["headline"]}</h2>
        <p>{fan_brief["brief"]}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="card">
            <h3>Fan Experience Score</h3>
            <div class="metric-number">82</div>
            <p>Strong baseline, but arrival timing matters.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="card">
            <h3>Weather Impact Score</h3>
            <div class="metric-number">{weather_score}</div>
            <p>Live signal based on rain, wind, and temperature.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        temp_display = "Unavailable" if weather["temperature"] is None else f"{round(weather['temperature'])}°F"
        rain_display = "Unavailable" if weather["rain_probability"] is None else f"{weather['rain_probability']}%"
        st.markdown(f"""
        <div class="live-card">
            <div class="live-badge">LIVE SIGNAL</div>
            <h3>MetLife Weather</h3>
            <div class="metric-number">{temp_display}</div>
            <p>{condition_label} · Rain risk: {rain_display}</p>
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
        <br><br>
        Weather note: <b>{weather_tip}</b>
    </div>
    """, unsafe_allow_html=True)

elif page == "Signal Inputs":
    st.header("Signals we are watching")

    signals = pd.DataFrame({
        "Signal": ["Traffic", "Transit", "Tickets", "Weather", "Watch parties"],
        "Status": ["Simulated", "Simulated", "Simulated", "Live", "Simulated"],
        "Action": [
            "Leave earlier",
            "Prefer transit",
            "Avoid last-minute buying",
            weather_tip,
            "Arrive early"
        ]
    })

    st.dataframe(signals, use_container_width=True, hide_index=True)

elif page == "AI Brief":
    st.markdown(f"""
    <div class="brief-card">
        <h2>🧠 Today's Fan Intelligence Brief</h2>
        <p><b>{fan_brief["headline"]}</b></p>
        <p>{fan_brief["brief"]}</p>
        <p><b>Recommended action:</b> {fan_brief["recommendation"]}</p>
        <div class="confidence-pill">Recommendation confidence: {fan_brief["confidence"]}</div>
    </div>
    """, unsafe_allow_html=True)

elif page == "Product Roadmap":
    st.header("PM Roadmap")

    roadmap = pd.DataFrame({
        "Phase": ["V1", "V2", "V3", "V4"],
        "Build": [
            "Decision-support prototype",
            "Live weather integration",
            "Traffic, ticket, and transit integrations",
            "Personalized AI recommendations"
        ],
        "PM Value": [
            "Validate user problem",
            "Replace first dummy signal with live data",
            "Increase usefulness",
            "Scale into fan copilot"
        ]
    })

    st.dataframe(roadmap, use_container_width=True, hide_index=True)