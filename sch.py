import calendar
import datetime
from zoneinfo import ZoneInfo
import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ==========================================
# 1. Google Calendar API 연동
# ==========================================
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """Google Calendar API 서비스 객체 생성"""
    creds = None
    if "credentials" in st.secrets:
        creds = Credentials.from_authorized_user_info(st.secrets["credentials"], SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
    return build('calendar', 'v3', credentials=creds)

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
    # 한국 공휴일 샘플 데이터 (필요 시 API나 라이브러리로 확장 가능)
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

    # 요일 헤더
    day_names = [('일', 'sun'), ('월', ''), ('화', ''), ('수', ''), ('목', ''), ('금', ''), ('토', 'sat')]
    for name, cls in day_names:
        html.append(f"<div class='day-name {cls}'>{name}</div>")

    # 월간 날짜 매트릭스 계산
    cal = calendar.Calendar(firstweekday=6)  # 일요일 시작
    month_days = cal.monthdayscalendar(year, month)

    for week in month_days:
        for day_idx, day in enumerate(week):
            if day == 0:
                html.append("<div class='day-cell' style='background-color: #f8fafc;'></div>")
                continue

            date_str = f"{year}-{month:02d}-{day:02d}"
            
            # 요일 색상 분류
            if day_idx == 0:
                num_class = "sun"
            elif day_idx == 6:
                num_class = "sat"
            else:
                num_class = "weekday"

            # 공휴일 체크
            holiday_text = holidays.get(date_str, "")
            if holiday_text:
                num_class = "sun"

            day_events = events_by_date.get(date_str, [])

            html.append("<div class='day-cell'>")
            
            # 날짜 및 등록 개수 뱃지 표시
            if day_events:
                html.append(f"<div class='event-badge'>{day}일 [{len(day_events)}]</div>")
            else:
                html.append(f"<div class='day-number {num_class}'>{day}일</div>")

            if holiday_text:
                html.append(f"<div class='holiday-label'>{holiday_text}</div>")

            # 이벤트 목록 출력
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
    
    # 컨트롤러 영역
    today = datetime.date.today()
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        selected_year = st.selectbox("연도 선택", range(2024, 2030), index=2)
    with c2:
        selected_month = st.selectbox("월 선택", range(1, 13), index=7) # 기본 8월
    with c3:
        if st.button("🔄 일정 새로고침"):
            st.cache_data.clear()
            st.rerun()

    try:
        service = get_calendar_service()
        raw_events = fetch_monthly_events(service, 'primary', selected_year, selected_month)
        grouped_events = group_events_by_date(raw_events)
        
        # 커스텀 CSS 달력 UI 출력
        calendar_html = render_custom_css_calendar(selected_year, selected_month, grouped_events)
        st.markdown(calendar_html, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"일정을 불러오는 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
