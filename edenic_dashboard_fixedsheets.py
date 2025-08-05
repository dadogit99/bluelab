import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# Trigger auto-refresh every 60 seconds
st_autorefresh(interval=60 * 1000, key="datarefresh")

st.title("🌿 Edenic Telemetry Dashboard")

# Convert secrets to dict
creds_dict = dict(st.secrets["google_service_account"])
creds_json = json.dumps(creds_dict)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(creds_json), scope)
client = gspread.authorize(credentials)
sheet = client.open("Edenic Telemetry Log").sheet1  # Ensure this matches your sheet name

API_KEY = st.secrets["general"]["api_key"]
DEVICE_ID = st.secrets["general"]["device_id"]
EDENIC_API = f"https://api.edenic.io/api/v1/telemetry/{DEVICE_ID}?keys=ph%2Celectrical_conductivity%2Ctemperature"

def fetch_telemetry():
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.get(EDENIC_API, headers=headers)
    response.raise_for_status()
    return response.json()

def convert_c_to_f(c):
    return round((c * 9/5) + 32, 2)

def main():
    try:
        data = fetch_telemetry()
        ph = data.get("ph", {}).get("value", "N/A")
        ec = data.get("electrical_conductivity", {}).get("value", "N/A")
        temp_c = data.get("temperature", {}).get("value", "N/A")
        temp_f = convert_c_to_f(temp_c) if isinstance(temp_c, (int, float)) else "N/A"

        # Display current readings
        st.metric(label="pH", value=ph)
        st.metric(label="EC", value=ec)
        st.metric(label="Water Temp (°F)", value=temp_f)

        # Eastern Time timestamp
        now = datetime.now(pytz.timezone("US/Eastern"))
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        st.caption(f"Last updated: {now_str} ET")

        # Save to Google Sheet
        sheet.append_row([now_str, ph, ec, temp_f])

    except Exception as e:
        st.error(f"Error: {e}")

main()