
import streamlit as st
import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import pytz

# Load secrets and setup Google Sheets client
creds_dict = dict(st.secrets["google_service_account"])
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)
sheet = client.open("Edenic Telemetry Log").sheet1  # Update sheet name if needed

# Display last updated time in Eastern Time
eastern = pytz.timezone("US/Eastern")
now_et = datetime.now(eastern)
st.markdown(f"**Last updated (ET):** {now_et.strftime('%Y-%m-%d %H:%M:%S')}")

# Fetch data from Edenic API
api_key = st.secrets["general"]["api_key"]
device_id = st.secrets["general"]["device_id"]
url = f"https://api.edenic.io/telemetry/latest?device_id={device_id}"
headers = {"Authorization": f"Bearer {api_key}"}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    ph = data.get("ph", "N/A")
    ec = data.get("ec", "N/A")
    temp_c = data.get("temperature", "N/A")
    temp_f = round((temp_c * 9/5) + 32, 2) if isinstance(temp_c, (int, float)) else "N/A"

    # Display metrics
    st.subheader("Edenic Telemetry Dashboard")
    st.metric(label="pH", value=ph)
    st.metric(label="EC", value=ec)
    st.metric(label="Water Temp (°F)", value=temp_f)

    # Log to Google Sheets
    timestamp_str = now_et.strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp_str, ph, ec, temp_f])

except Exception as e:
    st.error(f"Failed to retrieve or log telemetry data: {e}")
