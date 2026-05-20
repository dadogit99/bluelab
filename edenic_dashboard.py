from __future__ import annotations

import datetime as _dt
import logging
from typing import Optional, Tuple

import gspread
import pandas as pd
import requests
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
from streamlit_autorefresh import st_autorefresh

POLL_INTERVAL_SEC: int = 60
SHEET_NAME: str = "Edenic Telemetry Log"
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


def get_latest_telemetry(
    *, device_id: str, api_key: str
) -> Tuple[Optional[_dt.datetime], Optional[float], Optional[float], Optional[float]]:
    url = f"https://api.edenic.io/api/v1/telemetry/{device_id}"
    params = {"keys": "ph,electrical_conductivity,temperature"}
    headers = {"Authorization": api_key}
    response = requests.get(url, params=params, headers=headers, timeout=15)
    response.raise_for_status()

    data = response.json()
    ts: Optional[_dt.datetime] = None
    ph: Optional[float] = None
    ec: Optional[float] = None
    temp: Optional[float] = None

    if data.get("ph"):
        item = data["ph"][0]
        ph = float(item["value"]) if item.get("value") is not None else None
        if item.get("ts") is not None:
            ts = _dt.datetime.fromtimestamp(item["ts"] / 1000, tz=_dt.timezone.utc)
    if data.get("electrical_conductivity"):
        item = data["electrical_conductivity"][0]
        ec = float(item["value"]) if item.get("value") is not None else None
        if ts is None and item.get("ts") is not None:
            ts = _dt.datetime.fromtimestamp(item["ts"] / 1000, tz=_dt.timezone.utc)
    if data.get("temperature"):
        item = data["temperature"][0]
        temp_c = float(item["value"]) if item.get("value") is not None else None
        temp = (temp_c * 9 / 5) + 32 if temp_c is not None else None
        if ts is None and item.get("ts") is not None:
            ts = _dt.datetime.fromtimestamp(item["ts"] / 1000, tz=_dt.timezone.utc)
    return ts, ph, ec, temp


def append_reading(
    df: pd.DataFrame,
    timestamp: Optional[_dt.datetime],
    ph: Optional[float],
    ec: Optional[float],
    temp: Optional[float],
) -> Tuple[pd.DataFrame, bool]:
    """Append a new row if the timestamp is new. Returns (df, was_appended)."""
    if timestamp is None:
        return df, False
    if not df.empty and df.iloc[-1]["time"] == timestamp:
        return df, False
    new_row = pd.DataFrame(
        {"time": [timestamp], "pH": [ph], "EC": [ec], "temperature": [temp]}
    )
    return pd.concat([df, new_row], ignore_index=True), True


@st.cache_resource(show_spinner=False)
def open_sheet() -> Optional["gspread.Worksheet"]:
    """Open the configured Google Sheet. Returns None on any failure (display still works)."""
    try:
        creds_dict = dict(st.secrets["google_service_account"])
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)
        client = gspread.authorize(credentials)
        return client.open(SHEET_NAME).sheet1
    except Exception:
        logging.exception("Could not open Google Sheet — Sheets logging disabled")
        return None


def main() -> None:
    st.set_page_config(page_title="Edenic Telemetry Dashboard", layout="wide")
    st.title("Edenic Telemetry Dashboard")

    api_key = st.secrets["general"]["api_key"]
    device_id = st.secrets["general"]["device_id"]

    if "history" not in st.session_state:
        st.session_state["history"] = pd.DataFrame(
            columns=["time", "pH", "EC", "temperature"], dtype=float
        )

    st_autorefresh(interval=POLL_INTERVAL_SEC * 1000, limit=None, key="auto_refresh")
    sheet = open_sheet()

    try:
        ts, ph_val, ec_val, temp_val = get_latest_telemetry(
            device_id=device_id, api_key=api_key
        )
        st.session_state["history"], appended = append_reading(
            st.session_state["history"], ts, ph_val, ec_val, temp_val
        )
        if appended and sheet is not None:
            try:
                eastern = _dt.timezone(_dt.timedelta(hours=-4))
                local = ts.astimezone(eastern).strftime("%Y-%m-%d %H:%M:%S")
                sheet.append_row([local, ph_val, ec_val, temp_val])
            except Exception as sheet_err:
                logging.exception("Sheet append failed")
                st.warning(f"Display ok, but Sheets logging failed: {sheet_err}")
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
        latest = history.iloc[-1]
        c1, c2, c3 = st.columns(3)
        c1.metric("pH", f"{latest['pH']:.2f}" if latest["pH"] is not None else "—")
        c2.metric("EC", f"{latest['EC']:.2f}" if latest["EC"] is not None else "—")
        c3.metric(
            "Temperature (°F)",
            f"{latest['temperature']:.2f}" if latest["temperature"] is not None else "—",
        )
        if isinstance(latest["time"], _dt.datetime):
            eastern = _dt.timezone(_dt.timedelta(hours=-4))
            local_time = latest["time"].astimezone(eastern)
            st.caption(
                f"Last updated: {local_time.strftime('%Y-%m-%d %I:%M:%S %p EDT')}"
                + ("  ·  logged to Sheet" if sheet is not None else "  ·  Sheets disabled")
            )
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
            "Polls the Edenic API every 60 seconds for pH / EC / temperature. "
            "Each new reading is displayed and appended to the "
            f"**{SHEET_NAME}** Google Sheet."
        )


if __name__ == "__main__":
    main()
