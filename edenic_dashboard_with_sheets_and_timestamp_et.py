
from __future__ import annotations

import datetime as _dt
import logging
from typing import Optional, Tuple

import pandas as pd
import requests
import streamlit as st
import pytz
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from streamlit_autorefresh import st_autorefresh

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_KEY: str = "ed_dzv4ddrw1oq9ca7sn75xjdyqejxq496ku8l6sk9u4i3pf5f86x8axv8bwq9r4unh"
DEVICE_ID: str = "2d9b5760-afe9-11ee-a8fb-b92f34d9b31d"
POLL_INTERVAL_SEC: int = 60

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_latest_telemetry(
    *, device_id: str, api_key: str
) -> Tuple[Optional[_dt.datetime], Optional[float], Optional[float], Optional[float]]:
    url = f"https://api.edenic.io/api/v1/telemetry/{device_id}"
    params = {"keys": "ph,electrical_conductivity,temperature"}
    headers = {"Authorization": api_key}
    response = requests.get(url, params=params, headers=headers, timeout=15)
    response.raise_for_status()

    data = response.json()
    ts = None
    ph = None
    ec = None
    temp = None

    if "ph" in data and data["ph"]:
        item = data["ph"][0]
        ph = float(item.get("value")) if item.get("value") is not None else None
        ts = _dt.datetime.fromtimestamp(item.get("ts") / 1000, tz=_dt.timezone.utc)
    if "electrical_conductivity" in data and data["electrical_conductivity"]:
        item = data["electrical_conductivity"][0]
        ec = float(item.get("value")) if item.get("value") is not None else None
        if ts is None and item.get("ts") is not None:
            ts = _dt.datetime.fromtimestamp(item.get("ts") / 1000, tz=_dt.timezone.utc)
    if "temperature" in data and data["temperature"]:
        item = data["temperature"][0]
        temp_c = float(item.get("value")) if item.get("value") is not None else None
        temp = (temp_c * 9/5) + 32 if temp_c is not None else None
        if ts is None and item.get("ts") is not None:
            ts = _dt.datetime.fromtimestamp(item.get("ts") / 1000, tz=_dt.timezone.utc)
    return ts, ph, ec, temp


def send_to_sheets(timestamp, ph, ec, temp_f):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("gcreds.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open("Edenic Telemetry Log").worksheet("Sheet1")
    sheet.append_row([str(timestamp), ph, ec, temp_f])


def append_reading(df: pd.DataFrame, timestamp: Optional[_dt.datetime], ph: Optional[float], ec: Optional[float], temp: Optional[float]) -> pd.DataFrame:
    if timestamp is None:
        return df
    if df.empty or df.iloc[-1]["time"] != timestamp:
        new_row = pd.DataFrame(
            {
                "time": [timestamp],
                "pH": [ph],
                "EC": [ec],
                "temperature": [temp],
            }
        )
        return pd.concat([df, new_row], ignore_index=True)
    return df

# ---------------------------------------------------------------------------
# Streamlit application
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="Edenic Telemetry Dashboard", layout="wide")
    st.title("Edenic Telemetry Dashboard")

    if "history" not in st.session_state:
        st.session_state["history"] = pd.DataFrame(
            columns=["time", "pH", "EC", "temperature"],
            dtype=float,
        )

    st_autorefresh(interval=POLL_INTERVAL_SEC * 1000, limit=None, key="auto_refresh")

    try:
        ts, ph_val, ec_val, temp_val = get_latest_telemetry(device_id=DEVICE_ID, api_key=API_KEY)
        
        if ts and ph_val is not None and ec_val is not None and temp_val is not None:
            temp_f = temp_val * 9 / 5 + 32
            send_to_sheets(ts, ph_val, ec_val, temp_f)

        st.session_state["history"] = append_reading(st.session_state["history"], ts, ph_val, ec_val, temp_val)
    except requests.HTTPError as http_err:
        logging.exception("HTTP error while fetching telemetry")
        st.error(f"HTTP error: {http_err}")
    except requests.RequestException as req_err:
        logging.exception("Network error while fetching telemetry")
        st.error(f"Network error: {req_err}")
    except Exception as err:
        logging.exception("Unexpected error while fetching telemetry")
        st.error(f"Unexpected error: {err}")

    history = st.session_state["history"].copy()


    if not history.empty:
        latest_row = history.iloc[-1]
        col1, col2, col3 = st.columns(3)
        col1.metric("pH", f"{latest_row['pH']:.2f}" if latest_row['pH'] is not None else "—")
        col2.metric("EC", f"{latest_row['EC']:.2f}" if latest_row['EC'] is not None else "—")
        
        import pytz
        eastern = pytz.timezone("US/Eastern")
        local_time = latest_row['time'].astimezone(eastern)
        st.markdown(f"**Last updated:** {local_time.strftime('%Y-%m-%d %I:%M:%S %p')} ET")

        col3.metric("Temperature (°F)", f"{latest_row['temperature']:.2f}" if latest_row['temperature'] is not None else "—")
    else:
        st.info("Waiting for first reading …")

    if len(history) > 1:
        history["time"] = pd.to_datetime(history["time"], errors="coerce")
        history = history[pd.notnull(history["time"])]
        history = history.set_index("time")
        history.index = history.index.tz_convert(None)
        st.line_chart(history)
    elif len(history) == 1:
        st.write("Not enough data yet to plot a trend. Once more readings arrive, a line chart will appear.")

    with st.expander("About this app", expanded=False):
        st.markdown(
            "This dashboard uses the Edenic API to poll for telemetry every 60 seconds. "
            "It stores recent readings and displays a 24-hour chart of pH, EC, and temperature."
        )

if __name__ == "__main__":
    main()
