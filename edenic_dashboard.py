from datetime import datetime, timedelta
import streamlit as st
import requests
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# Streamlit page config
st.set_page_config(page_title="Edenic Telemetry Dashboard", layout="wide")

# Load secrets
api_key = st.secrets["general"]["api_key"]
device_id = st.secrets["general"]["device_id"]

# Google Sheets credentials from secrets
creds_dict = st.secrets["google_service_account"]
creds_json = json.dumps(creds_dict)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(creds_json), scope)
gc = gspread.authorize(credentials)

# Open the spreadsheet
sheet = gc.open("Edenic Telemetry Log").sheet1

# API URL
url = f"https://api.edenic.io/v1/device/{device_id}/latest"

# Get data from Edenic API
headers = {"Authorization": f"Bearer {api_key}"}
response = requests.get(url, headers=headers)
data = response.json()

# Process API data
if "measurements" in data:
    measurements = data["measurements"]
    timestamp = datetime.strptime(data["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ")
    eastern_time = timestamp - timedelta(hours=4)  # Convert from UTC to ET manually

    # Extract and convert values
    ph = measurements.get("ph")
    ec = measurements.get("ec")
    temp_c = measurements.get("water_temperature")
    temp_f = round((temp_c * 9/5) + 32, 2) if temp_c is not None else None

    # Display current values
    st.title("🌱 Edenic Telemetry Dashboard")
    st.subheader(f"Last updated: {eastern_time.strftime('%Y-%m-%d %I:%M:%S %p')} ET")
    col1, col2, col3 = st.columns(3)
    col1.metric("pH", ph)
    col2.metric("EC", ec)
    col3.metric("Water Temp (°F)", temp_f)

    # Update Google Sheet
    now_str = eastern_time.strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([now_str, ph, ec, temp_f])

else:
    st.error("Failed to load telemetry data.")
