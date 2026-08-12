import datetime
from googleapiclient.discovery import build
import pytz

def get_monthly_events(service, calendar_id, year, month):
    """
    선택한 연/월의 모든 일정을 구글 캘린더 API로부터 안전하게 가져오는 함수
    """
    tz = pytz.timezone('Asia/Seoul')
    
    # 1. 해당 월의 시작일 (1일 00:00:00)
    start_date = datetime.datetime(year, month, 1, 0, 0, 0)
    
    # 2. 해당 월의 마지막일 계산 (다음 달 1일 미만까지)
    if month == 12:
        end_date = datetime.datetime(year + 1, 1, 1, 0, 0, 0)
    else:
        end_date = datetime.datetime(year, month + 1, 1, 0, 0, 0)
        
    # ISO 8601 문자열 포맷팅 (타임존 포함)
    time_min = tz.localize(start_date).isoformat()
    time_max = tz.localize(end_date).isoformat()
    
    all_events = []
    page_token = None
    
    # 3. pageToken 처리로 한 달 치 전체 데이터 누락 없이 수집
    while True:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,          # 반복 일정 개별 이벤트로 분리
            orderBy='startTime',        # 시작 시간순 정렬
            pageToken=page_token,
            maxResults=2500             # 한 번에 불러올 최대 개수 확대
        ).execute()
        
        items = events_result.get('items', [])
        all_events.extend(items)
        
        page_token = events_result.get('nextPageToken')
        if not page_token:
            break

    return all_events


# --- Streamlit 렌더링 파트 점검 예시 ---
def render_calendar_view(events, year, month):
    """
    불러온 events 리스트를 날짜별 dictionary로 바인딩할 때 키값(YYYY-MM-DD) 매핑 점검
    """
    events_by_date = {}
    
    for event in events:
        # start 시각 정보 추출 (dateTime 우선, 없으면 종일 일정 date)
        start_raw = event['start'].get('dateTime', event['start'].get('date'))
        
        # 'YYYY-MM-DD' 형식 추출
        event_date = start_raw[:10] 
        
        if event_date not in events_by_date:
            events_by_date[event_date] = []
            
        events_by_date[event_date].append(event)
        
    return events_by_date
