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
        51: "Fog",
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


# -----------------------------
# Travel Intelligence Helper
# -----------------------------

def get_travel_model(origin):
    """
    Simulated travel model for MVP.
    Later this can be replaced with Google Maps, Mapbox, or NJ Transit APIs.
    """

    origin_data = {
        "Montclair": {
            "drive_now": 28,
            "drive_peak": 49,
            "transit": 44,
            "parking_risk": "High",
            "transit_reliability": "Medium",
            "reason": "Driving is fast now, but peak congestion near Route 3 and stadium exits can erase the advantage."
        },
        "Verona": {
            "drive_now": 24,
            "drive_peak": 42,
            "transit": 48,
            "parking_risk": "High",
            "transit_reliability": "Low",
            "reason": "Driving is still the fastest option, but the delay risk rises sharply closer to the event."
        },
        "Hoboken": {
            "drive_now": 31,
            "drive_peak": 61,
            "transit": 39,
            "parking_risk": "High",
            "transit_reliability": "High",
            "reason": "Transit is more predictable than driving from dense urban areas during event arrival windows."
        },
        "Jersey City": {
            "drive_now": 35,
            "drive_peak": 67,
            "transit": 45,
            "parking_risk": "High",
            "transit_reliability": "High",
            "reason": "Driving delay risk is high and transit provides a more reliable arrival window."
        },
        "NYC": {
            "drive_now": 42,
            "drive_peak": 78,
            "transit": 52,
            "parking_risk": "Very High",
            "transit_reliability": "High",
            "reason": "Cross-Hudson traffic and stadium-area congestion make transit the safer default."
        }
    }

    data = origin_data[origin]

    drive_delay = data["drive_peak"] - data["drive_now"]

    if data["transit"] < data["drive_peak"]:
        recommended_mode = "Transit"
    else:
        recommended_mode = "Drive early"

    if drive_delay >= 30:
        confidence = 86
    elif drive_delay >= 20:
        confidence = 78
    else:
        confidence = 70

    if data["parking_risk"] == "Very High":
        confidence += 5

    confidence = min(confidence, 92)

    return {
        **data,
        "drive_delay": drive_delay,
        "recommended_mode": recommended_mode,
        "confidence": confidence
    }


def generate_fan_brief(weather, travel):
    temp = weather.get("temperature")
    rain_prob = weather.get("rain_probability")
    wind = weather.get("wind_speed")
    condition = weather_condition_label(weather.get("weather_code"))

    if temp is None:
        weather_text = "Live weather is currently unavailable."
    else:
        weather_text = (
            f"Weather near MetLife is {condition.lower()} with temperature around "
            f"{round(temp)}°F."
        )

        if rain_prob is not None:
            weather_text += f" Rain risk is {rain_prob}%."

        if wind is not None:
            weather_text += f" Wind is around {round(wind)} mph."

    if travel["recommended_mode"] == "Transit":
        travel_text = (
            f"Travel intelligence recommends transit. Driving from this origin could rise "
            f"from {travel['drive_now']} minutes now to {travel['drive_peak']} minutes near event time."
        )
    else:
        travel_text = (
            f"Driving early is acceptable from this origin, but waiting could increase travel time "
            f"from {travel['drive_now']} minutes to {travel['drive_peak']} minutes."
        )

    brief = (
        f"{weather_text} {travel_text} "
        "The strongest fan-experience risk remains the arrival window, not the event itself."
    )

    recommendation = (
        f"Recommended mode: {travel['recommended_mode']}. "
        "Avoid peak arrival windows, make ticket decisions early, and give yourself buffer time near the stadium."
    )

    return {
        "headline": f"{travel['recommended_mode']} is the best current recommendation.",
        "brief": brief,
        "recommendation": recommendation,
        "confidence": f"{travel['confidence']}%"
    }


weather = get_metlife_weather()
condition_label = weather_condition_label(weather.get("weather_code"))
weather_tip = weather_recommendation(weather)
weather_score = calculate_weather_score(weather)


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

.reason-box {
    padding: 22px;
    border-radius: 20px;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    box-shadow: 0 10px 24px rgba(17,24,39,.06);
    margin-top: 20px;
}

.reason-box p {
    color: #374151;
    font-size: 17px;
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
# Global User Input
# -----------------------------

origin = st.selectbox(
    "Choose your origin for travel intelligence",
    ["Montclair", "Verona", "Hoboken", "Jersey City", "NYC"]
)

travel = get_travel_model(origin)
fan_brief = generate_fan_brief(weather, travel)


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
        st.markdown(f"""
        <div class="card">
            <h3>Recommended Mode</h3>
            <div class="metric-number">{travel["recommended_mode"]}</div>
            <p>Best current option from {origin}.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="card">
            <h3>Delay Risk</h3>
            <div class="metric-number">+{travel["drive_delay"]}</div>
            <p>Estimated additional driving minutes near event time.</p>
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

    col1, col2, col3 = st.columns(3)
    col1.metric("Drive now", f"{travel['drive_now']} mins")
    col2.metric("Drive near event", f"{travel['drive_peak']} mins")
    col3.metric("Transit estimate", f"{travel['transit']} mins")

    col4, col5, col6 = st.columns(3)
    col4.metric("Recommended mode", travel["recommended_mode"])
    col5.metric("Parking risk", travel["parking_risk"])
    col6.metric("Confidence", f"{travel['confidence']}%")

    st.markdown(f"""
    <div class="tip">
        Recommendation from <b>{origin}</b>: <b>{travel["recommended_mode"]}</b>.
        Driving delay risk is approximately <b>+{travel["drive_delay"]} minutes</b>
        near the event arrival window.
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="reason-box">
        <p><b>Why:</b> {travel["reason"]}</p>
        <p><b>Weather note:</b> {weather_tip}</p>
    </div>
    """, unsafe_allow_html=True)

elif page == "Signal Inputs":
    st.header("Signals we are watching")

    signals = pd.DataFrame({
        "Signal": ["Traffic", "Transit", "Parking", "Tickets", "Weather", "Watch parties"],
        "Status": [
            "Modeled",
            "Modeled",
            travel["parking_risk"],
            "Simulated",
            "Live",
            "Simulated"
        ],
        "Action": [
            f"Expect +{travel['drive_delay']} mins if driving late",
            f"Transit estimate from {origin}: {travel['transit']} mins",
            f"Parking risk is {travel['parking_risk'].lower()}",
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
        "Phase": ["V1", "V2", "V3", "V4", "V5"],
        "Build": [
            "Decision-support prototype",
            "Live weather integration",
            "Modeled travel intelligence",
            "Live traffic, ticket, and transit integrations",
            "Personalized AI recommendations"
        ],
        "PM Value": [
            "Validate user problem",
            "Replace first dummy signal with live data",
            "Turn static guidance into decision model",
            "Increase real-world usefulness",
            "Scale into fan copilot"
        ]
    })

    st.dataframe(roadmap, use_container_width=True, hide_index=True)