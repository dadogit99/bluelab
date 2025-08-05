"""
Edenic Telemetry Dashboard
==========================

This Streamlit application demonstrates how to fetch telemetry data from a
Bluelab Edenic device and display it in a simple dashboard. It polls
Edenic's REST API once per minute to retrieve the latest pH, electrical
conductivity (EC) and temperature readings from a device, appends these
values to a growing history and renders both the real‑time metrics and a
historical trend line.

Before running this script you must install the required dependencies:

    pip install streamlit streamlit-autorefresh pandas requests

You also need to provide your own API key and device ID. These values can
be generated from within the Edenic web application; see the Edenic API
documentation for instructions on creating API keys and obtaining your
device ID【147297304516579†L35-L54】. Place your key and ID in the
``API_KEY`` and ``DEVICE_ID`` variables below.

Run the dashboard with:

    streamlit run edenic_dashboard.py

The application will automatically refresh every 60 seconds (the minimum
allowed polling interval according to the API specification【662520216656674†L33-L41】) to
fetch new data. If a connection error occurs, the error will be displayed
in the interface.
"""

from __future__ import annotations

import datetime as _dt
import logging
from typing import Optional, Tuple

import pandas as pd
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Replace the values below with your own API key and device ID.  These can
# be obtained from your Edenic account under Account settings → API Keys.  The
# API key must be supplied in the ``Authorization`` header of every request
#【147297304516579†L46-L54】, and you must specify the device ID in the URL
# path when requesting telemetry【662520216656674†L33-L48】.
API_KEY: str = "YOUR_API_KEY_HERE"
DEVICE_ID: str = "YOUR_DEVICE_ID_HERE"

# The polling interval in seconds.  The API only allows one call per minute
# per device, so a 60 second interval honours this limitation【662520216656674†L33-L41】.
POLL_INTERVAL_SEC: int = 60

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_latest_telemetry(
    *, device_id: str, api_key: str
) -> Tuple[Optional[_dt.datetime], Optional[float], Optional[float], Optional[float]]:
    """Fetch the most recent telemetry values for pH, EC and temperature.

    Parameters
    ----------
    device_id: str
        The UUID of the Edenic device to query.
    api_key: str
        The secret API key used for authentication.

    Returns
    -------
    tuple
        A tuple ``(timestamp, ph, ec, temp)`` where ``timestamp`` is a
        ``datetime`` representing the time of the reading (or ``None`` if
        unavailable) and the remaining values are floats or ``None`` if no
        reading was returned.  The timestamp is computed from the epoch
        milliseconds returned by the API【662520216656674†L61-L86】.

    Raises
    ------
    requests.HTTPError
        If the HTTP request returns a non‑success status code.
    requests.RequestException
        If a network error occurs while performing the request.
    """
    url = f"https://api.edenic.io/api/v1/telemetry/{device_id}"
    params = {"keys": "ph,electrical_conductivity,temperature"}
    headers = {"Authorization": api_key}
    response = requests.get(url, params=params, headers=headers, timeout=15)
    response.raise_for_status()

    data = response.json()  # expected to be a dict of lists
    ts: Optional[_dt.datetime] = None
    ph: Optional[float] = None
    ec: Optional[float] = None
    temp: Optional[float] = None

    # Each key's value is a list of readings; take the first item (latest)
    if "ph" in data and data["ph"]:
        item = data["ph"][0]
        ph = float(item.get("value")) if item.get("value") is not None else None
        ts = _dt.datetime.fromtimestamp(item.get("ts") / 1000, tz=_dt.timezone.utc)
    if "electrical_conductivity" in data and data["electrical_conductivity"]:
        item = data["electrical_conductivity"][0]
        ec = float(item.get("value")) if item.get("value") is not None else None
        # If timestamp not yet set, use this reading's timestamp
        if ts is None and item.get("ts") is not None:
            ts = _dt.datetime.fromtimestamp(item.get("ts") / 1000, tz=_dt.timezone.utc)
    if "temperature" in data and data["temperature"]:
        item = data["temperature"][0]
        temp = float(item.get("value")) if item.get("value") is not None else None
        if ts is None and item.get("ts") is not None:
            ts = _dt.datetime.fromtimestamp(item.get("ts") / 1000, tz=_dt.timezone.utc)
    return ts, ph, ec, temp


def append_reading(df: pd.DataFrame, timestamp: Optional[_dt.datetime], ph: Optional[float], ec: Optional[float], temp: Optional[float]) -> pd.DataFrame:
    """Append a new telemetry row to a DataFrame if it does not already exist.

    Parameters
    ----------
    df: pd.DataFrame
        Existing DataFrame storing the history.  It should have columns
        ``["time", "pH", "EC", "temperature"]``.
    timestamp, ph, ec, temp: values to append

    Returns
    -------
    pd.DataFrame
        A new DataFrame containing the previous rows and the appended row.
    """
    if timestamp is None:
        # nothing to append if timestamp unknown
        return df
    # Only append if time is new
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

    # Initialise stateful storage for telemetry history
    if "history" not in st.session_state:
        # DataFrame with proper dtypes
        st.session_state["history"] = pd.DataFrame(
            columns=["time", "pH", "EC", "temperature"],
            dtype=float,
        )

    # Trigger autorefresh; this returns the number of times the page has been refreshed
    st_autorefresh(interval=POLL_INTERVAL_SEC * 1000, limit=None, key="auto_refresh")

    # Fetch latest telemetry
    try:
        ts, ph_val, ec_val, temp_val = get_latest_telemetry(device_id=DEVICE_ID, api_key=API_KEY)
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

    # Display the latest metrics if available
    if not history.empty:
        latest_row = history.iloc[-1]
        col1, col2, col3 = st.columns(3)
        col1.metric("pH", f"{latest_row['pH']:.2f}" if latest_row['pH'] is not None else "—")
        col2.metric("EC", f"{latest_row['EC']:.2f}" if latest_row['EC'] is not None else "—")
        col3.metric("Temperature (°C)", f"{latest_row['temperature']:.2f}" if latest_row['temperature'] is not None else "—")
    else:
        st.info("Waiting for first reading …")

    # Plot the history as a line chart if we have at least two points
    if len(history) > 1:
        history = history.set_index("time")
        # Convert timestamps to the user’s local timezone for display
        history.index = history.index.tz_convert(None)
        st.line_chart(history)
    elif len(history) == 1:
        st.write("Not enough data yet to plot a trend. Once more readings arrive, a line chart will appear.")

    # Add some documentation to help the user
    with st.expander("About this app", expanded=False):
        st.markdown(
            "This dashboard uses the public Edenic API to retrieve the latest telemetry\n"
            "data for a device. It polls the API once per minute, stores a history\n"
            "of readings in memory and plots a trend chart. The API endpoints support\n"
            "parameters for selecting specific telemetry keys and retrieving historical\n"
            "data at various intervals【662520216656674†L49-L86】. Refer to the official documentation\n"
            "for additional options.\n"
            "\n"
            "**Note:** The displayed timestamps are converted from the millisecond epoch\n"
            "times provided by the API【662520216656674†L61-L86】.",
        )


if __name__ == "__main__":
    main()