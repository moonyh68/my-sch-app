import calendar
import datetime
from zoneinfo import ZoneInfo
import streamlit as st
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ==========================================
# 1. Google Calendar API 연동 (Secrets 자동 감지)
# ==========================================
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """Streamlit Secrets의 인증 정보를 감지하여 Google Calendar API 서비스 객체 생성"""
    
    # 1. Secrets에 [connections.gsheets] 서비스 계정이 설정되어 있는 경우
    if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        sa_info = dict(st.secrets["connections"]["gsheets"])
        creds = service_account.Credentials.from_service_account_info(
            sa_info, scopes=SCOPES
        )
        return build('calendar', 'v3', credentials=creds)

    # 2. [gcp_service_account] 섹션이 설정되어 있는 경우
    elif "gcp_service_account" in st.secrets:
        sa_info = dict(st.secrets["gcp_service_account"])
        creds = service_account.Credentials.from_service_account_info(
            sa_info, scopes=SCOPES
        )
        return build('calendar', 'v3', credentials=creds)

    # 3. [credentials] OAuth 토큰 섹션이 설정되어 있는 경우
    elif "credentials" in st.secrets:
        creds_info = dict(st.secrets["credentials"])
        creds = Credentials.from_authorized_user_info(creds_info, SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return build('calendar', 'v3', credentials=creds)

    else:
        raise KeyError(
            "Streamlit Secrets에 인증 정보가 설정되지 않았습니다. "
            "App settings > Secrets에 [connections.gsheets] 또는 [credentials] 항목을 확인해 주세요."
        )

# ==========================================
# 2. zoneinfo 기반 월간 일정 데이터 Fetch
# ==========================================
def fetch_monthly_events(service, calendar_id, year, month):
    """
    zoneinfo(Asia/Seoul)를 적용하여 한 달 전체 일정을 누락 없이 수집
    """
    tz = ZoneInfo("Asia/Seoul")
    
    # 해당 월 시작일 및 종료일 범위 설정
    start_date = datetime.datetime(year, month, 1, 0, 0, 0, tzinfo=tz)
    if month == 12:
        end_date = datetime.datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=tz)
    else:
        end_date = datetime.datetime(year, month + 1, 1, 0, 0, 0, tzinfo=tz)
        
    time_min = start_date.isoformat()
    time_max = end_date.isoformat()
    
    all_events = []
    page_token = None
    
    while True:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,      # 반복 일정 개별 분리
            orderBy='startTime',    # 시간순 정렬
            pageToken=page_token,
            maxResults=2500
        ).execute()
        
        items = events_result.get('items', [])
        all_events.extend(items)
        
        page_token = events_result.get('nextPageToken')
        if not page_token:
            break

    return all_events

def group_events_by_date(events):
    """일정 목록을 YYYY-MM-DD 날짜 키로 매핑"""
    events_by_date = {}
    for event in events:
        start_raw = event['start'].get('dateTime', event['start'].get('date'))
        if start_raw:
            date_key = start_raw[:10]
            if date_key not in events_by_date:
                events_by_date[date_key] = []
            events_by_date[date_key].append(event)
    return events_by_date

# ==========================================
# 3. 커스텀 CSS Grid 월간 달력 HTML 생성
# ==========================================
def render_custom_css_calendar(year, month, events_by_date):
    """
    앱 화면과 동일한 스타일의 CSS Grid 기반 달력 HTML 렌더링
    """
    holidays = {
        f"{year}-08-15": "광복절",
        f"{year}-08-17": "대체공휴일"
    }

    css = """
    <style>
        .calendar-container {
            width: 100%;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin-top: 15px;
        }
        .calendar-header {
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            color: #1a365d;
            margin-bottom: 20px;
        }
        .calendar-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 1px;
            background-color: #e2e8f0;
            border: 1px solid #cbd5e1;
            border-radius: 4px;
            overflow: hidden;
        }
        .day-name {
            background-color: #ffffff;
            padding: 10px;
            text-align: center;
            font-weight: bold;
            font-size: 14px;
            border-bottom: 2px solid #cbd5e1;
        }
        .day-name.sun { color: #e53e3e; }
        .day-name.sat { color: #2b6cb0; }
        
        .day-cell {
            background-color: #ffffff;
            min-height: 110px;
            padding: 6px;
            box-sizing: border-box;
            vertical-align: top;
        }
        .day-number {
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .day-number.sun { color: #e53e3e; }
        .day-number.sat { color: #2b6cb0; }
        .day-number.weekday { color: #2d3748; }
        
        .holiday-label {
            color: #e53e3e;
            font-size: 11px;
            font-weight: bold;
            margin-top: 2px;
        }
        .event-badge {
            background-color: #0088cc;
            color: white;
            font-size: 11px;
            font-weight: bold;
            padding: 2px 6px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 4px;
        }
        .event-item {
            background-color: #edf2f7;
            border-left: 3px solid #3182ce;
            padding: 3px 5px;
            margin-top: 3px;
            border-radius: 2px;
            font-size: 11px;
            color: #1a202c;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
    </style>
    """

    html = [f"{css}<div class='calendar-container'>"]
    html.append(f"<div class='calendar-header'>{year}년 {month}월</div>")
    html.append("<div class='calendar-grid'>")

    day_names = [('일', 'sun'), ('월', ''), ('화', ''), ('수', ''), ('목', ''), ('금', ''), ('토', 'sat')]
    for name, cls in day_names:
        html.append(f"<div class='day-name {cls}'>{name}</div>")

    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)

    for week in month_days:
        for day_idx, day in enumerate(week):
            if day == 0:
                html.append("<div class='day-cell' style='background-color: #f8fafc;'></div>")
                continue

            date_str = f"{year}-{month:02d}-{day:02d}"
            
            if day_idx == 0:
                num_class = "sun"
            elif day_idx == 6:
                num_class = "sat"
            else:
                num_class = "weekday"

            holiday_text = holidays.get(date_str, "")
            if holiday_text:
                num_class = "sun"

            day_events = events_by_date.get(date_str, [])

            html.append("<div class='day-cell'>")
            
            if day_events:
                html.append(f"<div class='event-badge'>{day}일 [{len(day_events)}]</div>")
            else:
                html.append(f"<div class='day-number {num_class}'>{day}일</div>")

            if holiday_text:
                html.append(f"<div class='holiday-label'>{holiday_text}</div>")

            for ev in day_events:
                summary = ev.get('summary', '제목 없음')
                start_raw = ev['start'].get('dateTime')
                time_str = ""
                if start_raw and 'T' in start_raw:
                    time_str = start_raw.split('T')[1][:5] + " "
                
                html.append(f"<div class='event-item' title='{summary}'>📌 {time_str}{summary}</div>")

            html.append("</div>")

    html.append("</div></div>")
    return "".join(html)

# ==========================================
# 4. Streamlit 실행 부분
# ==========================================
def main():
    st.set_page_config(page_title="월간 일정표 앱", layout="wide")
    
    today = datetime.date.today()
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        selected_year = st.selectbox("연도 선택", range(2024, 2030), index=2)
    with c2:
        selected_month = st.selectbox("월 선택", range(1, 13), index=7)
    with c3:
        if st.button("🔄 일정 새로고침"):
            st.cache_data.clear()
            st.rerun()

    try:
        service = get_calendar_service()
        
        # 서비스 계정을 사용할 경우 본인의 구글 이메일 주소를 입력하거나, Secrets에서 불러옵니다.
        calendar_id = st.secrets.get("calendar_id", "primary")
        
        raw_events = fetch_monthly_events(service, calendar_id, selected_year, selected_month)
        grouped_events = group_events_by_date(raw_events)
        
        calendar_html = render_custom_css_calendar(selected_year, selected_month, grouped_events)
        st.markdown(calendar_html, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"일정을 불러오는 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
