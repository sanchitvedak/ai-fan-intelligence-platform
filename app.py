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
            "rain_probability": rain_probability,
            "wind_speed": current.get("wind_speed_10m"),
            "weather_code": current.get("weather_code"),
            "source": "Live weather from Open-Meteo"
        }

    except Exception:
        return {
            "temperature": None,
            "rain_probability": None,
            "wind_speed": None,
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
        return "Weather data is currently unavailable."

    parts = []

    if rain_prob is not None and rain_prob >= 50:
        parts.append("Carry rain gear and allow extra travel time.")
    elif rain_prob is not None and rain_prob >= 25:
        parts.append("Pack a light jacket or umbrella just in case.")
    else:
        parts.append("Weather risk looks low right now.")

    if wind is not None and wind >= 20:
        parts.append("Wind may affect outdoor comfort near the stadium.")

    if temp >= 85:
        parts.append("Hydration will matter for fans arriving early.")
    elif temp <= 45:
        parts.append("Dress warmly, especially if using transit or walking.")

    return " ".join(parts)


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
# Google Routes API Helper
# -----------------------------

DESTINATION = "MetLife Stadium, East Rutherford, NJ"

ORIGINS = {
    "Montclair": "Montclair, NJ",
    "Verona": "Verona, NJ",
    "Hoboken": "Hoboken, NJ",
    "Jersey City": "Jersey City, NJ",
    "NYC": "Times Square, New York, NY"
}

TRANSIT_ESTIMATES = {
    "Montclair": 44,
    "Verona": 48,
    "Hoboken": 39,
    "Jersey City": 45,
    "NYC": 52
}


@st.cache_data(ttl=300)
def get_live_drive_time(origin_name):
    api_key = st.secrets.get("GOOGLE_MAPS_API_KEY", None)

    if not api_key:
        return {
            "available": False,
            "drive_now": None,
            "drive_static": None,
            "distance_miles": None,
            "traffic_delay": None,
            "source": "Google Maps API key missing"
        }

    url = "https://routes.googleapis.com/directions/v2:computeRoutes"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "routes.duration,routes.staticDuration,routes.distanceMeters"
    }

    payload = {
        "origin": {"address": ORIGINS[origin_name]},
        "destination": {"address": DESTINATION},
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_AWARE",
        "computeAlternativeRoutes": False,
        "languageCode": "en-US",
        "units": "IMPERIAL"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=12)
        response.raise_for_status()
        data = response.json()

        routes = data.get("routes", [])
        if not routes:
            raise ValueError("No route returned")

        route = routes[0]

        duration_seconds = int(route["duration"].replace("s", ""))
        static_seconds = int(route["staticDuration"].replace("s", ""))
        distance_meters = route.get("distanceMeters", 0)

        drive_now = round(duration_seconds / 60)
        drive_static = round(static_seconds / 60)
        traffic_delay = max(0, drive_now - drive_static)
        distance_miles = round(distance_meters / 1609.34, 1)

        return {
            "available": True,
            "drive_now": drive_now,
            "drive_static": drive_static,
            "distance_miles": distance_miles,
            "traffic_delay": traffic_delay,
            "source": "Live drive time from Google Routes API"
        }

    except Exception as e:
        return {
            "available": False,
            "drive_now": None,
            "drive_static": None,
            "distance_miles": None,
            "traffic_delay": None,
            "source": f"Google Routes unavailable: {str(e)}"
        }


def get_travel_model(origin):
    live = get_live_drive_time(origin)

    fallback_drive_now = {
        "Montclair": 28,
        "Verona": 24,
        "Hoboken": 31,
        "Jersey City": 35,
        "NYC": 42
    }

    fallback_peak = {
        "Montclair": 49,
        "Verona": 42,
        "Hoboken": 61,
        "Jersey City": 67,
        "NYC": 78
    }

    parking_risk = {
        "Montclair": "High",
        "Verona": "High",
        "Hoboken": "High",
        "Jersey City": "High",
        "NYC": "Very High"
    }

    transit_reliability = {
        "Montclair": "Medium",
        "Verona": "Low",
        "Hoboken": "High",
        "Jersey City": "High",
        "NYC": "High"
    }

    if live["available"]:
        drive_now = live["drive_now"]
        drive_static = live["drive_static"]
        traffic_delay = live["traffic_delay"]

        if traffic_delay >= 12:
            peak_multiplier = 1.55
        elif traffic_delay >= 6:
            peak_multiplier = 1.4
        else:
            peak_multiplier = 1.25

        drive_peak = round(drive_now * peak_multiplier)
        data_source = "Live Google traffic"
    else:
        drive_now = fallback_drive_now[origin]
        drive_static = fallback_drive_now[origin]
        traffic_delay = None
        drive_peak = fallback_peak[origin]
        data_source = "Fallback model"

    transit = TRANSIT_ESTIMATES[origin]
    drive_delay = max(0, drive_peak - drive_now)

    if transit < drive_peak or parking_risk[origin] == "Very High":
        recommended_mode = "Transit"
    else:
        recommended_mode = "Drive early"

    if live["available"]:
        confidence = 88 if recommended_mode == "Transit" else 82
    else:
        confidence = 74

    if parking_risk[origin] == "Very High":
        confidence += 4

    confidence = min(confidence, 94)

    if recommended_mode == "Transit":
        reason = (
            f"Live driving time is {drive_now} minutes, but event-window driving could reach "
            f"{drive_peak} minutes. Transit is estimated around {transit} minutes and avoids parking risk."
        )
    else:
        reason = (
            f"Driving is currently {drive_now} minutes and remains competitive if you leave before "
            f"the peak arrival window. Waiting could increase drive time to around {drive_peak} minutes."
        )

    return {
        "live_available": live["available"],
        "drive_now": drive_now,
        "drive_static": drive_static,
        "drive_peak": drive_peak,
        "distance_miles": live["distance_miles"],
        "traffic_delay_live": traffic_delay,
        "transit": transit,
        "drive_delay": drive_delay,
        "recommended_mode": recommended_mode,
        "parking_risk": parking_risk[origin],
        "transit_reliability": transit_reliability[origin],
        "confidence": confidence,
        "reason": reason,
        "source": data_source,
        "raw_source": live["source"]
    }


# -----------------------------
# Personalization Helper
# -----------------------------

def get_personalized_match_plan(fan_type, travel_group, primary_goal, origin, travel, weather_score):
    score = 78
    reasons = []
    actions = []

    recommended_mode = travel["recommended_mode"]

    if fan_type == "Local NJ Fan":
        reasons.append("You likely know the area, so timing matters more than navigation complexity.")
        actions.append("Leave before the peak arrival window.")
        score += 4

    elif fan_type == "NYC Commuter":
        recommended_mode = "Transit"
        reasons.append("Cross-Hudson traffic and stadium parking make transit the safer default.")
        actions.append("Use transit and avoid post-event rideshare surge.")
        score += 5

    elif fan_type == "US Fan Traveling to NJ":
        reasons.append("You may be less familiar with stadium-area traffic, so extra buffer matters.")
        actions.append("Arrive at least 75 minutes before kickoff.")
        score += 2

    elif fan_type == "International Visitor":
        recommended_mode = "Transit"
        reasons.append("Transit reduces unfamiliar parking, routing, and post-match driving complexity.")
        actions.append("Arrive 90 minutes early and pre-plan your return route.")
        score += 6

    if travel_group == "Solo":
        reasons.append("Solo travel gives you more flexibility to adjust timing.")
        actions.append("Use the fastest available option and monitor live traffic.")
        score += 3

    elif travel_group == "Partner":
        reasons.append("Traveling with a partner balances flexibility with comfort.")
        actions.append("Pick a clear meeting point before arriving.")
        score += 2

    elif travel_group == "Family":
        reasons.append("Family travel increases the importance of predictability, comfort, and buffer time.")
        actions.append("Add extra time for walking, snacks, bathrooms, and security.")
        score -= 2

    elif travel_group == "Friends":
        reasons.append("Group coordination makes transit and early arrival more valuable.")
        actions.append("Choose a departure time everyone can commit to.")
        score += 1

    elif travel_group == "Corporate Group":
        reasons.append("Corporate groups need predictable arrival and lower coordination risk.")
        actions.append("Use a fixed departure time and share the route plan in advance.")
        score += 1

    if primary_goal == "Fastest Arrival":
        reasons.append("Your goal prioritizes speed over comfort or cost.")
        actions.append("Leave now if live drive time is favorable.")

    elif primary_goal == "Lowest Cost":
        recommended_mode = "Transit"
        reasons.append("Transit typically reduces parking and surge pricing exposure.")
        actions.append("Avoid stadium parking and post-event rideshare if possible.")

    elif primary_goal == "Least Stress":
        recommended_mode = "Transit"
        reasons.append("Predictability matters more than shaving off a few minutes.")
        actions.append("Use transit, leave early, and avoid tight arrival windows.")
        score += 4

    elif primary_goal == "Best Experience":
        reasons.append("A smoother experience depends on arriving early, not rushing.")
        actions.append("Arrive early enough to explore, eat, and avoid last-minute lines.")
        score += 3

    if travel["drive_delay"] >= 25:
        reasons.append(f"Driving delay risk is high at approximately +{travel['drive_delay']} minutes.")
        score -= 4
    elif travel["drive_delay"] >= 15:
        reasons.append(f"Driving delay risk is moderate at approximately +{travel['drive_delay']} minutes.")
        score -= 2

    if weather_score >= 80:
        reasons.append("Weather conditions are favorable.")
        score += 3
    elif weather_score < 65:
        reasons.append("Weather could create comfort issues.")
        actions.append("Pack weather protection and add walking buffer.")
        score -= 4

    score = max(45, min(score, 96))

    return {
        "recommended_mode": recommended_mode,
        "score": score,
        "reasons": reasons[:5],
        "actions": actions[:5]
    }


def generate_fan_brief(weather, travel, match_plan, fan_type, travel_group, primary_goal):
    temp = weather.get("temperature")
    rain_prob = weather.get("rain_probability")
    wind = weather.get("wind_speed")
    condition = weather_condition_label(weather.get("weather_code"))

    if temp is None:
        weather_text = "Live weather is currently unavailable."
    else:
        weather_text = f"Weather near MetLife is {condition.lower()} with temperature around {round(temp)}°F."

        if rain_prob is not None:
            weather_text += f" Rain risk is {rain_prob}%."

        if wind is not None:
            weather_text += f" Wind is around {round(wind)} mph."

    if travel["live_available"]:
        travel_text = (
            f"Live Google traffic shows current driving time from the selected origin at "
            f"{travel['drive_now']} minutes. Event-window travel could rise to around "
            f"{travel['drive_peak']} minutes."
        )
    else:
        travel_text = (
            f"Traffic is currently modeled using fallback estimates. Driving now is estimated at "
            f"{travel['drive_now']} minutes and could rise to {travel['drive_peak']} minutes near event time."
        )

    profile_text = f"Profile: {fan_type}, traveling with {travel_group.lower()}, optimizing for {primary_goal.lower()}."

    recommendation = (
        f"Recommended mode: {match_plan['recommended_mode']}. "
        f"Top action: {match_plan['actions'][0] if match_plan['actions'] else 'Leave early and monitor conditions.'}"
    )

    return {
        "headline": f"{match_plan['recommended_mode']} is the best match plan for this profile.",
        "brief": f"{profile_text} {weather_text} {travel_text}",
        "recommendation": recommendation,
        "confidence": f"{match_plan['score']}%"
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

.profile-panel {
    padding: 24px;
    border-radius: 26px;
    background: rgba(255,255,255,.9);
    border: 1px solid #e5e7eb;
    box-shadow: 0 12px 30px rgba(17,24,39,.07);
    margin-bottom: 28px;
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

.brief-card p, .brief-card li {
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
# Match Plan Inputs
# -----------------------------

st.markdown('<div class="profile-panel">', unsafe_allow_html=True)
st.subheader("Build Your Match Plan")

col_a, col_b, col_c, col_d = st.columns(4)

with col_a:
    fan_type = st.selectbox(
        "Fan type",
        ["Local NJ Fan", "NYC Commuter", "US Fan Traveling to NJ", "International Visitor"]
    )

with col_b:
    travel_group = st.selectbox(
        "Traveling with",
        ["Solo", "Partner", "Family", "Friends", "Corporate Group"]
    )

with col_c:
    primary_goal = st.selectbox(
        "Primary goal",
        ["Fastest Arrival", "Lowest Cost", "Least Stress", "Best Experience"]
    )

with col_d:
    origin = st.selectbox(
        "Origin",
        list(ORIGINS.keys())
    )

st.markdown('</div>', unsafe_allow_html=True)

travel = get_travel_model(origin)
match_plan = get_personalized_match_plan(fan_type, travel_group, primary_goal, origin, travel, weather_score)
fan_brief = generate_fan_brief(weather, travel, match_plan, fan_type, travel_group, primary_goal)


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
            <h3>Match Plan Score</h3>
            <div class="metric-number">{match_plan["score"]}</div>
            <p>Personalized score based on profile, traffic, and weather.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        distance = "N/A" if travel["distance_miles"] is None else f"{travel['distance_miles']} mi"
        st.markdown(f"""
        <div class="card">
            <h3>Live Drive Time</h3>
            <div class="metric-number">{travel["drive_now"]} min</div>
            <p>{distance} · Source: {travel["source"]}</p>
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
    col2.metric("Projected event drive", f"{travel['drive_peak']} mins")
    col3.metric("Transit estimate", f"{travel['transit']} mins")

    col4, col5, col6 = st.columns(3)
    col4.metric("Recommended mode", match_plan["recommended_mode"])
    col5.metric("Parking risk", travel["parking_risk"])
    col6.metric("Match plan score", f"{match_plan['score']}")

    st.markdown(f"""
    <div class="tip">
        Recommendation from <b>{origin}</b>: <b>{match_plan["recommended_mode"]}</b>.
        Driving delay risk near the event window is approximately
        <b>+{travel["drive_delay"]} minutes</b>.
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="reason-box">
        <p><b>Profile:</b> {fan_type} traveling with {travel_group.lower()}, optimizing for {primary_goal.lower()}.</p>
        <p><b>Why:</b> {travel["reason"]}</p>
        <p><b>Weather note:</b> {weather_tip}</p>
        <p><b>Data source:</b> {travel["raw_source"]}</p>
    </div>
    """, unsafe_allow_html=True)

elif page == "Signal Inputs":
    st.header("Signals we are watching")

    signals = pd.DataFrame({
        "Signal": [
            "Fan type",
            "Travel group",
            "Primary goal",
            "Traffic",
            "Transit",
            "Parking",
            "Weather",
            "Tickets",
            "Watch parties"
        ],
        "Status": [
            fan_type,
            travel_group,
            primary_goal,
            "Live" if travel["live_available"] else "Fallback model",
            "Modeled",
            travel["parking_risk"],
            "Live",
            "Simulated",
            "Simulated"
        ],
        "Action": [
            "Personalizes recommendation logic",
            "Adjusts buffer and comfort assumptions",
            "Changes optimization priority",
            f"Drive now: {travel['drive_now']} mins; projected event drive: {travel['drive_peak']} mins",
            f"Transit estimate from {origin}: {travel['transit']} mins",
            f"Parking risk is {travel['parking_risk'].lower()}",
            weather_tip,
            "Avoid last-minute buying",
            "Arrive early"
        ]
    })

    st.dataframe(signals, use_container_width=True, hide_index=True)

elif page == "AI Brief":
    actions_html = "".join([f"<li>{action}</li>" for action in match_plan["actions"]])
    reasons_html = "".join([f"<li>{reason}</li>" for reason in match_plan["reasons"]])

    st.markdown(f"""
    <div class="brief-card">
        <h2>🧠 Today's Personalized Match Plan</h2>
        <p><b>{fan_brief["headline"]}</b></p>
        <p>{fan_brief["brief"]}</p>
        <p><b>Recommended action:</b> {fan_brief["recommendation"]}</p>

        <h3>Why this recommendation</h3>
        <ul>{reasons_html}</ul>

        <h3>Top actions</h3>
        <ul>{actions_html}</ul>

        <div class="confidence-pill">Match Plan Score: {match_plan["score"]}</div>
    </div>
    """, unsafe_allow_html=True)

elif page == "Product Roadmap":
    st.header("PM Roadmap")

    roadmap = pd.DataFrame({
        "Phase": ["V1", "V2", "V3", "V4", "V5", "V6"],
        "Build": [
            "Decision-support prototype",
            "Live weather integration",
            "Modeled travel intelligence",
            "Live Google traffic integration",
            "Fan personas and match planning",
            "World Cup insights page"
        ],
        "PM Value": [
            "Validate user problem",
            "Replace first dummy signal with live data",
            "Turn static guidance into decision model",
            "Make travel recommendation actionable",
            "Personalize recommendations by user context",
            "Create shareable insights and content"
        ]
    })

    st.dataframe(roadmap, use_container_width=True, hide_index=True)