from __future__ import annotations

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

def main() -> None:
    st.set_page_config(page_title="Edenic Telemetry Dashboard", layout="wide")
    st.title("Edenic Telemetry Dashboard")

    if "history" not in st.session_state:
        st.session_state["history"] = pd.DataFrame(
            columns=["time", "pH", "EC", "temperature"],
            dtype=float,
        )

    st_autorefresh(interval=POLL_INTERVAL_SEC * 1000, limit=None, key="auto_refresh")

    # Placeholder for telemetry fetch logic (not shown here)
    # Imagine here: st.session_state["history"] = append_reading(...)


    history = st.session_state["history"].copy()

    # Convert temperature from Celsius to Fahrenheit
    if not history.empty and "temperature" in history.columns:
        history["temperature"] = history["temperature"].apply(
            lambda c: round((c * 9 / 5) + 32, 1) if c is not None else None
        )


    # Display the latest metrics if available
    if not history.empty:
        latest_row = history.iloc[-1]
        col1, col2, col3 = st.columns(3)
        col1.metric("pH", f"{latest_row['pH']:.2f}" if latest_row['pH'] is not None else "—")
        col2.metric("EC", f"{latest_row['EC']:.2f}" if latest_row['EC'] is not None else "—")
        col3.metric("Water Temp (°F)", f"{latest_row['temperature']:.2f}" if latest_row['temperature'] is not None else "—")

if __name__ == "__main__":
    main()
