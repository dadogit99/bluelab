
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
import pandas as pd
from datetime import datetime

# Read credentials securely from Streamlit secrets
API_KEY = st.secrets["general"]["api_key"]
DEVICE_ID = st.secrets["general"]["device_id"]

# Poll interval in milliseconds (60000ms = 1 minute)
st_autorefresh(interval=60000, key="refresh")

st.title("Edenic RDWC Dashboard")
st.caption("Live data refreshed every minute")

# Initialize session state
if "history" not in st.session_state:
    st.session_state["history"] = []

# Call Edenic API
headers = {"Authorization": f"Bearer {API_KEY}"}
url = f"https://api.edenic.io/v1/telemetry?device_id={DEVICE_ID}&keys=ph,electrical_conductivity,water_temperature"

try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()

    # Extract metrics
    timestamp = datetime.now()
    ph = data.get("ph", {}).get("value")
    ec = data.get("electrical_conductivity", {}).get("value")

    temp_c = data.get("water_temperature", {}).get("value")
    water_temp = round((temp_c * 9/5) + 32, 1) if temp_c is not None else None

    # Append to history
    st.session_state["history"].append({
        "time": timestamp,
        "pH": ph,
        "EC": ec,
        "Temp (°F)": water_temp
    })

    # Display live metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("pH", ph)
    col2.metric("EC (mS/cm)", ec)
    col3.metric("Water Temp (°F)", water_temp)

    # Display chart
    df = pd.DataFrame(st.session_state["history"])
    st.line_chart(df.set_index("time"))

except requests.RequestException as e:
    st.error(f"Error fetching data: {e}")
