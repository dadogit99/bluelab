
import datetime as _dt
import logging
from typing import Optional, Tuple

import pandas as pd
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

API_KEY: str = "ed_dzv4ddrw1oq9ca7sn75xjdyqejxq496ku8l6sk9u4i3pf5f86x8axv8bwq9r4unh"
DEVICE_ID: str = "2d9b5760-afe9-11ee-a8fb-b92f34d9b31d"
POLL_INTERVAL_SEC: int = 60

def get_latest_telemetry(*, device_id: str, api_key: str):
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
        temp = float(item.get("value")) if item.get("value") is not None else None
        if ts is None and item.get("ts") is not None:
            ts = _dt.datetime.fromtimestamp(item.get("ts") / 1000, tz=_dt.timezone.utc)
    return ts, ph, ec, temp

def main():
    st.set_page_config(page_title="Edenic Telemetry Dashboard", layout="wide")
    st.title("Edenic Telemetry Dashboard")

    if "history" not in st.session_state:
        st.session_state["history"] = pd.DataFrame(columns=["time", "pH", "EC", "temperature"], dtype=float)

    st_autorefresh(interval=POLL_INTERVAL_SEC * 1000, limit=None, key="auto_refresh")

    try:
        ts, ph_val, ec_val, temp_val = get_latest_telemetry(device_id=DEVICE_ID, api_key=API_KEY)
        if ts is not None:
            df = st.session_state["history"]
            if df.empty or df.iloc[-1]["time"] != ts:
                df = pd.concat([
                    df,
                    pd.DataFrame([{"time": ts, "pH": ph_val, "EC": ec_val, "temperature": temp_val}])
                ], ignore_index=True)
                st.session_state["history"] = df
    except Exception as e:
        logging.exception("Telemetry fetch error")
        st.error(f"Error fetching data: {e}")

    history = st.session_state["history"].copy()

    # Convert to Fahrenheit and rename column
    history["temperature_f"] = history["temperature"].apply(
        lambda c: round((c * 9 / 5) + 32, 1) if c is not None else None
    )

    # Filter last 24 hours
    if not history.empty:
        now = _dt.datetime.utcnow()
        cutoff = now - _dt.timedelta(hours=24)
            if not history.empty:
        now = _dt.datetime.utcnow()
        cutoff = now - _dt.timedelta(hours=24)

        history = history[pd.notnull(history["time"])]
        history["time"] = pd.to_datetime(history["time"], errors="coerce")
        history = history[pd.notnull(history["time"])]
        history = history[history["time"] >= cutoff]

    # Display latest values
    if not history.empty:
        latest_row = history.iloc[-1]
        col1, col2, col3 = st.columns(3)
        col1.metric("pH", f"{latest_row['pH']:.2f}" if latest_row['pH'] is not None else "—")
        col2.metric("EC", f"{latest_row['EC']:.2f}" if latest_row['EC'] is not None else "—")
        col3.metric("Water Temp (°F)", f"{latest_row['temperature_f']:.2f}" if latest_row['temperature_f'] is not None else "—")
    else:
        st.info("Waiting for first reading …")

    # Plot chart of last 24h
    if len(history) > 1:
        history = history.set_index("time")
        history.index = history.index.tz_convert(None)
        st.line_chart(history[["pH", "EC", "temperature_f"]])
    elif len(history) == 1:
        st.write("Not enough data yet to plot a trend.")

if __name__ == "__main__":
    main()
