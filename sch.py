import streamlit as st
import datetime
import calendar
import pandas as pd
from zoneinfo import ZoneInfo
from streamlit_gsheets import GSheetsConnection
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 페이지 기본 설정
st.set_page_config(page_title="월간 일정표", layout="wide", page_icon="📅")

# ---------------------------------------------------------
# 대한민국 주요 공휴일 및 대체공휴일 자동 계산 함수
# ---------------------------------------------------------
def get_kr_holidays(year):
    holidays = {
        f"{year}-01-01": "신정",
        f"{year}-03-01": "삼일절",
        f"{year}-05-05": "어린이날",
        f"{year}-06-06": "현충일",
        f"{year}-08-15": "광복절",
        f"{year}-10-03": "개천절",
        f"{year}-10-09": "한글날",
        f"{year}-12-25": "성탄절",
    }
    
    lunar_and_sub_holidays = {
        2024: {
            "2024-02-09": "설날 연휴", "2024-02-10": "설날", "2024-02-11": "설날 연휴", "2024-02-12": "대체공휴일",
            "2024-05-06": "대체공휴일", "2024-05-15": "부처님오신날",
            "2024-09-16": "추석 연휴", "2024-09-17": "추석", "2024-09-18": "추석 연휴"
        },
        2025: {
            "2025-01-28": "설날 연휴", "2025-01-29": "설날", "2025-01-30": "설날 연휴", "2025-03-03": "대체공휴일",
            "2025-05-05": "부처님오신날/어린이날", "2025-05-06": "대체공휴일",
            "2025-10-05": "추석 연휴", "2025-10-06": "추석", "2025-10-07": "추석 연휴", "2025-10-08": "대체공휴일"
        },
        2026: {
            "2026-02-16": "설날 연휴", "2026-02-17": "설날", "2026-02-18": "설날 연휴",
            "2026-05-24": "부처님오신날", "2026-05-25": "대체공휴일",
            "2026-08-17": "대체공휴일",
            "2026-09-24": "추석 연휴", "2026-09-25": "추석", "2026-09-26": "추석 연휴", "2026-09-28": "대체공휴일",
            "2026-10-05": "대체공휴일"
        },
        2027: {
            "2027-02-06": "설날 연휴", "2027-02-07": "설날", "2027-02-08": "설날 연휴", "2027-02-09": "대체공휴일",
            "2027-05-13": "부처님오신날",
            "2027-09-14": "추석 연휴", "2027-09-15": "추석", "2027-09-16": "추석 연휴",
            "2027-10-04": "대체공휴일", "2027-10-10": "대체공휴일"
        }
    }
    
    if year in lunar_and_sub_holidays:
        holidays.update(lunar_and_sub_holidays[year])
        
    return holidays

# ---------------------------------------------------------
# 구글 캘린더 연동 설정
# ---------------------------------------------------------
CALENDAR_ID = "moonyh68@gmail.com"

def get_calendar_service():
    creds_dict = st.secrets["connections"]["gsheets"]
    credentials = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=['https://www.googleapis.com/auth/calendar']
    )
    return build('calendar', 'v3', credentials=credentials)

def add_google_calendar_event(date_str, start_time_str, end_time_str, title, memo):
    try:
        service = get_calendar_service()
        start_dt = datetime.datetime.strptime(f"{date_str} {start_time_str}", "%Y-%m-%d %H:%M")
        end_dt = datetime.datetime.strptime(f"{date_str} {end_time_str}", "%Y-%m-%d %H:%M")
        if end_dt <= start_dt:
            end_dt += datetime.timedelta(days=1)

        event = {
            'summary': title,
            'description': memo if memo else '',
            'start': {'dateTime': start_dt.strftime("%Y-%m-%dT%H:%M:00"), 'timeZone': 'Asia/Seoul'},
            'end': {'dateTime': end_dt.strftime("%Y-%m-%dT%H:%M:00"), 'timeZone': 'Asia/Seoul'},
        }

        created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return True, str(created_event.get('id', '')), None
    except Exception as e:
        return False, "", str(e)

def update_google_calendar_event(event_id, date_str, start_time_str, end_time_str, title, memo):
    try:
        service = get_calendar_service()
        start_dt = datetime.datetime.strptime(f"{date_str} {start_time_str}", "%Y-%m-%d %H:%M")
        end_dt = datetime.datetime.strptime(f"{date_str} {end_time_str}", "%Y-%m-%d %H:%M")
        if end_dt <= start_dt:
            end_dt += datetime.timedelta(days=1)

        event = {
            'summary': title,
            'description': memo if memo else '',
            'start': {'dateTime': start_dt.strftime("%Y-%m-%dT%H:%M:00"), 'timeZone': 'Asia/Seoul'},
            'end': {'dateTime': end_dt.strftime("%Y-%m-%dT%H:%M:00"), 'timeZone': 'Asia/Seoul'},
        }

        if event_id and not pd.isna(event_id) and str(event_id).strip() != "":
            try:
                service.events().update(calendarId=CALENDAR_ID, eventId=str(event_id).strip(), body=event).execute()
                return True, str(event_id).strip(), None
            except Exception:
                pass

        created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return True, str(created_event.get('id', '')), None
    except Exception as e:
        return False, "", str(e)

def delete_google_calendar_event(event_id):
    if not event_id or pd.isna(event_id) or str(event_id).strip() == "":
        return True, None
    try:
        service = get_calendar_service()
        service.events().delete(calendarId=CALENDAR_ID, eventId=str(event_id).strip()).execute()
        return True, None
    except Exception as e:
        return False, str(e)

# ---------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------
st.markdown("""
    <style>
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        max-width: 100% !important;
    }
    header[data-testid="stHeader"] { background: transparent !important; }
    hr { margin: 0.5rem 0 !important; border-color: #E2E8F0 !important; }
    div[data-testid="stColumn"] div[data-testid="stVerticalBlock"] { gap: 0px !important; }
    div[data-testid="stColumn"] div[data-testid="stElementContainer"] { margin-bottom: 0px !important; }

    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
        border-right: 1px solid #E2E8F0 !important; 
        border-bottom: 1px solid #E2E8F0 !important; 
        padding: 2px 4px !important;
        min-height: 80px !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child {
        border-left: 1px solid #E2E8F0 !important;
    }

    div
