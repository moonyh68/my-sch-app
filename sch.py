import streamlit as st
import datetime
import calendar
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 페이지 기본 설정
st.set_page_config(page_title="월간 일정표", layout="wide", page_icon="📅")

# ---------------------------------------------------------
# 구글 캘린더 연동 설정 (자정 넘는 일정 자동 날짜 보정)
# ---------------------------------------------------------
CALENDAR_ID = "moonyh68@gmail.com"

def get_calendar_service():
    """구글 캘린더 API 서비스 객체 생성"""
    creds_dict = st.secrets["connections"]["gsheets"]
    credentials = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=['https://www.googleapis.com/auth/calendar']
    )
    return build('calendar', 'v3', credentials=credentials)

def add_google_calendar_event(date_str, start_time_str, end_time_str, title, memo):
    """구글 캘린더 신규 일정 등록"""
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
    """구글 캘린더 일정 수정"""
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
    """구글 캘린더 일정 삭제"""
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
    
    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    hr {
        margin: 0.5rem 0 !important;
        border-color: #E2E8F0 !important;
    }

    div[data-testid="stColumn"] div[data-testid="stVerticalBlock"] {
        gap: 0px !important;
    }

    div[data-testid="stColumn"] div[data-testid="stElementContainer"] {
        margin-bottom: 0px !important;
    }

    /* 달력 각 일자별 열(Column) 구분 세로선 및 가로선 경계 스타일 */
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
        border-right: 1px solid #E2E8F0 !important; 
        border-bottom: 1px solid #E2E8F0 !important; 
        padding: 2px 4px !important;
        min-height: 80px !important;
    }

    /* 첫 번째 열(일요일) 왼쪽 세로 테두리 추가 */
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child {
        border-left: 1px solid #E2E8F0 !important;
    }

    /* 일자 날짜 버튼 높이 최적화 */
    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] div.stButton > button,
    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] div.stButton > button p,
    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] div.stButton > button div {
        background-color: transparent !important;
        border: none !important;
        color: #475569 !important;
        padding: 0px 2px !important;
        min-height: 18px !important;
        height: 20px !important;
        line-height: 20px !important;
        font-size: 13.5px !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        box-shadow: none !important;
        transition: all 0.15s ease-in-out !important;
        margin-bottom: 1px !important;
        letter-spacing: normal !important;
        -webkit-font-smoothing: antialiased !important;
    }

    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] div.stButton > button:hover,
    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] div.stButton > button:hover p {
        background-color: #F1F5F9 !important;
        color: #0284C7 !important;
    }

    /* '오늘' 날짜 원형 하이라이트 */
    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] div.stButton > button[kind="primary"],
    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] div.stButton > button[kind="primary"] p {
        background-color: #0284C7 !important;
        border: none !important;
        color: #FFFFFF !important;
        font-weight: 800 !important;
        border-radius: 10px !important;
    }

    /* 일정 텍스트 컨테이너 */
    .task-container {
        background-color: transparent !important;
        border: none !important;
        padding: 0px !important;
        margin-top: 1px !important;
    }

    /* PC 화면: 일정내용 폰트 12px */
    .task-item {
        font-size: 12px !important;
        font-weight: 500 !important;
        color: #0F172A !important;
        line-height: 1.3 !important;
        margin-bottom: 2px !important;
        white-space: normal !important;
        word-break: break-all !important;
        padding: 2px 4px !important;
        border-radius: 3px !important;
        background-color: #F0F9FF !important;
        border-left: 3px solid #38BDF8 !important;
    }

    .task-item-done {
        background-color: #DCFCE7 !important;
        border-left: 3px solid #22C55E !important;
        color: #166534 !important;
        text-decoration: line-through !important;
    }

    .task-item-meeting {
        background-color: #FEF3C7 !important;
        border-left: 3px solid #F59E0B !important;
        color: #92400E !important;
    }

    /* 네비게이션 버튼 (이전달/다음달) */
    div.stButton > button[key="btn_prev_month"], 
    div.stButton > button[key="btn_next_month"] {
        background-color: #F1F5F9 !important;
        border: 1px solid #CBD5E1 !important;
        color: #334155 !important;
        font-weight: 700 !important;
        font-size: 12px !important;
        min-height: 26px !important;
        height: 28px !important;
        border-radius: 14px !important;
        padding: 2px 10px !important;
    }

    div.stButton > button[key="btn_prev_month"]:hover, 
    div.stButton > button[key="btn_next_month"]:hover {
        background-color: #E2E8F0 !important;
        color: #0F172A !important;
    }

    div[data-testid="stFormSubmitButton"] > button {
        background-color: #166534 !important;
        color: white !important;
        font-weight: bold !important;
        font-size: 14px !important;
        min-height: 32px !important;
        border-radius: 6px !important;
    }

    /* 하단 KPI 대시보드 카드 스타일 */
    .kpi-card {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        padding: 6px 10px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
        text-align: center !important;
    }

    /* 📱 모바일 반응형 CSS: 시간 제외 */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 1.0rem !important;
        }

        div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 0px !important;
        }

        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
            width: 14.28% !important;
            min-width: 0px !important;
            flex: 1 1 14.28% !important;
            padding: 1px 1px !important;
            min-height: 60px !important;
        }

        div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] div.stButton > button,
        div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] div.stButton > button p {
            font-size: 10.5px !important;
            font-weight: 700 !important;
            min-height: 16px !important;
            height: 18px !important;
            line-height: 18px !important;
            padding: 0px !important;
        }

        .task-item {
            font-size: 9.5px !important;
            line-height: 1.2 !important;
            margin-bottom: 1px !important;
            padding: 1px 2px !important;
        }

        .task-time {
            display: none !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. 구글 시트 데이터베이스 연동 함수
# ---------------------------------------------------------
conn = st.connection("gsheets", type=GSheetsConnection)

def fetch_all_tasks():
    """Google Sheets 전체 데이터 안전 읽기"""
    try:
        df = conn.read(ttl=0)
        expected_cols = ['id', 'task_date', 'start_time', 'end_time', 'title', 'memo', 'is_done', 'is_meeting', 'meeting_notes', 'event_id']
        
        if df.empty:
            return pd.DataFrame(columns=expected_cols)
            
        for col in expected_cols:
            if col not in df.columns:
                df[col] = ""
                
        df = df.astype(object)
        
        df['id_clean'] = pd.to_numeric(df['id'], errors='coerce').fillna(-1).astype(int)
        df = df[df['id_clean'] != -1].copy()
        df['id'] = df['id_clean']
        df = df.drop(columns=['id_clean'])
        
        df['is_done'] = pd.to_numeric(df['is_done'], errors='coerce').fillna(0).astype(int)
        df['is_meeting'] = pd.to_numeric(df['is_meeting'], errors='coerce').fillna(0).astype(int)
        
        str_cols = ['task_date', 'start_time', 'end_time', 'title', 'memo', 'meeting_notes', 'event_id']
        for col in str_cols:
            df[col] = df[col].fillna("").astype(str)
            
        return df.reset_index(drop=True)
    except Exception as e:
        return pd.DataFrame(columns=['id', 'task_date', 'start_time', 'end_time', 'title', 'memo', 'is_done', 'is_meeting', 'meeting_notes', 'event_id'])

def save_all_tasks(df):
    """인덱스 재정렬 후 안전하게 Google Sheets 업데이트"""
    clean_df = df.reset_index(drop=True)
    conn.update(data=clean_df)

def fetch_month_tasks(year, month):
    df = fetch_all_tasks()
    if df.empty:
        return df
    prefix = f"{year}-{month:02d}"
    return df[df['task_date'].str.startswith(prefix)]

def insert_task(task_date, start_time, end_time, title, memo, is_done, is_meeting, meeting_notes):
    """단일 날짜 일정 저장"""
    df = fetch_all_tasks()
    
    if not df.empty and len(df['id']) > 0:
        new_id = int(df['id'].max()) + 1
    else:
        new_id = 1
    
    cal_success, cal_event_id, cal_err = add_google_calendar_event(task_date, start_time, end_time, title, memo)
    
    new_row = pd.DataFrame([{
        'id': int(new_id),
        'task_date': str(task_date),
        'start_time': str(start_time),
        'end_time': str(end_time),
        'title': str(title),
        'memo': str(memo),
        'is_done': int(is_done),
        'is_meeting': int(is_meeting),
        'meeting_notes': str(meeting_notes),
        'event_id': str(cal_event_id) if cal_event_id else ""
    }]).astype(object)
    
    updated_df = pd.concat([df, new_row], ignore_index=True)
    save_all_tasks(updated_df)
    return cal_success, cal_err

def insert_task_range(start_date, end_date, start_time, end_time, title, memo, is_done, is_meeting, meeting_notes):
    """★ [신규] 연속 기간(시작일~종료일) 일괄 생성 로직"""
    current_d = start_date
    last_err = None
    all_success = True

    while current_d <= end_date:
        date_str = current_d.strftime("%Y-%m-%d")
        succ, err = insert_task(date_str, start_time, end_time, title, memo, is_done, is_meeting, meeting_notes)
        if not succ:
            all_success = False
            last_err = err
        current_d += datetime.timedelta(days=1)

    return all_success, last_err

def update_task_full(target_id, task_date, start_time, end_time, title, memo, is_meeting, meeting_notes):
    """단일 일정 수정 로직 - ID 문자열 정규화 비교"""
    df = fetch_all_tasks()
    if df.empty:
        return True, None

    target_id_str = str(int(target_id))
    df['id_str'] = df['id'].astype(str).str.strip()
    
    mask = (df['id_str'] == target_id_str)
    if mask.any():
        idx = df[mask].index[0]
        old_event_id = str(df.loc[idx, 'event_id']) if 'event_id' in df.columns else ""
        
        cal_success, new_event_id, cal_err = update_google_calendar_event(old_event_id, task_date, start_time, end_time, title, memo)
        
        df.loc[idx, 'start_time'] = str(start_time)
        df.loc[idx, 'end_time'] = str(end_time)
        df.loc[idx, 'title'] = str(title)
        df.loc[idx, 'memo'] = str(memo)
        df.loc[idx, 'is_meeting'] = int(is_meeting)
        df.loc[idx, 'meeting_notes'] = str(meeting_notes)
        
        if new_event_id:
            df.loc[idx, 'event_id'] = str(new_event_id)
            
        df = df.drop(columns=['id_str'])
        save_all_tasks(df)
        return cal_success, cal_err
        
    return True, None

def update_task_done(target_id, is_done):
    """완료 상태 단일 업데이트"""
    df = fetch_all_tasks()
    if df.empty:
        return

    target_id_str = str(int(target_id))
    df['id_str'] = df['id'].astype(str).str.strip()
    mask = (df['id_str'] == target_id_str)
    
    if mask.any():
        idx = df[mask].index[0]
        df.loc[idx, 'is_done'] = int(is_done)
        df = df.drop(columns=['id_str'])
        save_all_tasks(df)

def delete_task(target_id):
    """지정한 단 1개의 ID만 안전 삭제"""
    df = fetch_all_tasks()
    if df.empty:
        return True, None

    target_id_str = str(int(target_id))
    df['id_str'] = df['id'].astype(str).str.strip()
    
    matched = df[df['id_str'] == target_id_str]
    if not matched.empty:
        idx = matched.index[0]
        event_id = str(df.loc[idx, 'event_id']) if 'event_id' in df.columns else ""
        
        updated_df = df[df['id_str'] != target_id_str].copy()
        updated_df = updated_df.drop(columns=['id_str'])
        
        save_all_tasks(updated_df)
        
        cal_success, cal_err = delete_google_calendar_event(event_id)
        return cal_success, cal_err
        
    return True, None

# ---------------------------------------------------------
# 2. 세션 상태 초기화
# ---------------------------------------------------------
today = datetime.date.today()
if "current_year" not in st.session_state:
    st.session_state.current_year = today.year
if "current_month" not in st.session_state:
    st.session_state.current_month = today.month

year = st.session_state.current_year
month = st.session_state.current_month

# ---------------------------------------------------------
# 3. 팝업 모달 다이얼로그 (연속 기간 등록 옵션 추가)
# ---------------------------------------------------------
@st.dialog("📅 일자별 상세 일정 및 회의록", width="large")
def open_day_modal(target_date):
    date_str = target_date.strftime("%Y-%m-%d")
    st.markdown(f"### `{date_str}` 일정 관리")

    all_df = fetch_all_tasks()
    tasks_df = all_df[all_df['task_date'] == date_str].sort_values(by="start_time") if not all_df.empty else pd.DataFrame()

    if not tasks_df.empty:
        st.markdown("**📋 등록된 일정 및 수정**")
        for _, row in tasks_df.iterrows():
            row_id = int(row['id'])
            status_text = "✅ 완료" if row['is_done'] else "⏳ 진행중"
            
            with st.expander(f"[{status_text}] {row['start_time']}~{row['end_time']} | {row['title']}", expanded=False):
                st.markdown("**수정 항목 입력**")
                
                try:
                    st_time_val = datetime.datetime.strptime(str(row['start_time']), "%H:%M").time()
                except:
                    st_time_val = datetime.time(9, 0)
                try:
                    et_time_val = datetime.datetime.strptime(str(row['end_time']), "%H:%M").time()
                except:
                    et_time_val = datetime.time(10, 0)

                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    edit_start = st.time_input("시작 시간", value=st_time_val, key=f"e_start_{row_id}")
                with col_e2:
                    edit_end = st.time_input("종료 시간", value=et_time_val, key=f"e_end_{row_id}")

                edit_title = st.text_input("업무명 / 안건", value=row['title'], key=f"e_title_{row_id}")
                edit_memo = st.text_input("메모", value=row['memo'] if pd.notna(row['memo']) else "", key=f"e_memo_{row_id}")
                edit_is_meeting = st.checkbox("회의 여부", value=bool(row['is_meeting']), key=f"e_chk_mt_{row_id}")

                edit_meeting_notes = ""
                if edit_is_meeting:
                    edit_meeting_notes = st.text_area("회의 내용 및 결정 사항", value=row['meeting_notes'] if pd.notna(row['meeting_notes']) else "", key=f"e_notes_{row_id}")

                col_btn1, col_btn2, col_btn3 = st.columns([1.5, 1.5, 1])
                
                with col_btn1:
                    if st.button("💾 수정 저장", key=f"save_btn_{row_id}", use_container_width=True):
                        if not edit_title:
                            st.error("업무명을 입력해 주세요.")
                        else:
                            success, err_msg = update_task_full(
                                row_id,
                                date_str,
                                edit_start.strftime("%H:%M"),
                                edit_end.strftime("%H:%M"),
                                edit_title,
                                edit_memo,
                                edit_is_meeting,
                                edit_meeting_notes
                            )
                            if not success:
                                st.session_state["cal_status"] = "error"
                                st.session_state["cal_msg"] = f"구글 캘린더 수정 실패: {err_msg}"
                            else:
                                st.session_state["cal_status"] = None
                            st.rerun()

                with col_btn2:
                    chk_label = "✅ 완료" if row['is_done'] else "🟢 완료 처리"
                    if st.button(f"{chk_label}", key=f"chk_btn_{row_id}", use_container_width=True):
                        new_done = 0 if row['is_done'] else 1
                        update_task_done(row_id, new_done)
                        st.rerun()

                with col_btn3:
                    if st.button("🗑️ 삭제", key=f"del_btn_{row_id}", use_container_width=True):
                        success, err_msg = delete_task(row_id)
                        if not success:
                            st.session_state["cal_status"] = "error"
                            st.session_state["cal_msg"] = f"구글 캘린더 삭제 실패: {err_msg}"
                        else:
                            st.session_state["cal_status"] = None
                        st.rerun()
        st.divider()

    st.markdown("**➕ 새 일정 추가**")
    
    # ★ 등록 유형 선택 (단일 날짜 vs 연속 기간)
    entry_mode = st.radio("등록 방식", ["단일 일자", "연속 기간(여러 날)"], horizontal=True, key="entry_mode_radio")
    
    with st.form("add_task_form", clear_on_submit=False):
        if entry_mode == "연속 기간(여러 날)":
            selected_range = st.date_input(
                "기간 선택 (시작일 ~ 종료일)",
                value=(target_date, target_date + datetime.timedelta(days=2)),
                key="add_date_range"
            )
        else:
            selected_range = None

        col1, col2 = st.columns(2)
        with col1:
            start_t = st.time_input("시작 시간", datetime.time(9, 0))
        with col2:
            end_t = st.time_input("종료 시간", datetime.time(10, 0))

        title = st.text_input("업무명 / 안건", placeholder="예: 주간 실적 점검")
        memo = st.text_input("메모", placeholder="비고 및 주요 메모")

        is_meeting = st.checkbox("회의 여부 (선택 시 회의록 입력란 활성화)")
        meeting_notes = ""
        if is_meeting:
            meeting_notes = st.text_area("회의 내용 및 결정 사항", placeholder="회의 안건, 참석자, 결론 등을 입력하세요.")

        submit = st.form_submit_button("💾 일정 저장", use_container_width=True)
        if submit:
            if not title:
                st.error("업무명을 입력해 주세요.")
            else:
                if entry_mode == "연속 기간(여러 날)":
                    if isinstance(selected_range, tuple) and len(selected_range) == 2:
                        s_d, e_d = selected_range
                        success, err_msg = insert_task_range(
                            s_d, e_d,
                            start_t.strftime("%H:%M"),
                            end_t.strftime("%H:%M"),
                            title, memo, False, is_meeting, meeting_notes
                        )
                    else:
                        st.error("시작일과 종료일을 모두 선택해 주세요.")
                        success = True
                else:
                    success, err_msg = insert_task(
                        date_str,
                        start_t.strftime("%H:%M"),
                        end_t.strftime("%H:%M"),
                        title, memo, False, is_meeting, meeting_notes
                    )

                if not success:
                    st.session_state["cal_status"] = "error"
                    st.session_state["cal_msg"] = f"구글 캘린더 등록 실패: {err_msg}"
                else:
                    st.session_state["cal_status"] = None
                st.rerun()

# =================================-------------------------
# [1단] 최상단 년/월 표시 및 에러 상태 메시지 영역
# =================================-------------------------
st.markdown(
    f"<h2 style='text-align: center; font-weight: 800; font-size: 24px; margin: 0 0 8px 0; padding: 0;'><span style='color: #1E3A8A;'>{year}년</span> <span style='color: #166534;'>{month}월</span></h2>",
    unsafe_allow_html=True
)

if st.session_state.get("cal_status") == "error":
    st.error(f"⚠️ **동기화 오류**: {st.session_state.get('cal_msg')}")

# =================================-------------------------
# [2단] 월간 달력 영역
# =================================-------------------------
days_of_week = [("일", "#EF4444"), ("월", "#334155"), ("화", "#334155"), ("수", "#334155"), ("목", "#334155"), ("금", "#334155"), ("토", "#2563EB")]

cols = st.columns(7)
for idx, (day_name, color_code) in enumerate(days_of_week):
    cols[idx].markdown(f"<div style='text-align: center; color: {color_code}; font-weight: 800; font-size: 14px; padding: 2px 0; border: none; margin-bottom: 2px;'>{day_name}</div>", unsafe_allow_html=True)

month_df = fetch_month_tasks(year, month)

calendar.setfirstweekday(calendar.SUNDAY)
month_calendar = calendar.monthcalendar(year, month)

for week in month_calendar:
    week_cols = st.columns(7)
    for day_idx, day in enumerate(week):
        with week_cols[day_idx]:
            if day == 0:
                st.write("")
            else:
                curr_date = datetime.date(year, month, day)
                date_str = curr_date.strftime("%Y-%m-%d")

                day_tasks = month_df[month_df['task_date'] == date_str] if not month_df.empty else pd.DataFrame()
                day_total = len(day_tasks)

                btn_label = f"{day}일"
                if day_total > 0:
                    btn_label += f" [{day_total}]"

                is_today = (curr_date == today)
                btn_type = "primary" if is_today else "secondary"

                if st.button(btn_label, key=f"btn_day_{day}", type=btn_type, use_container_width=True):
                    open_day_modal(curr_date)

                if day_total > 0:
                    task_items = []
                    for _, t in day_tasks.iterrows():
                        css_class = "task-item"
                        icon = "📌"
                        if t['is_done']:
                            css_class += " task-item-done"
                            icon = "✅"
                        elif t['is_meeting']:
                            css_class += " task-item-meeting"
                            icon = "📝"
                        
                        time_html = f"<span class='task-time'>{t['start_time']} </span>"
                        task_items.append(f"<div class='{css_class}'>{icon} {time_html}{str(t['title'])}</div>")
                    
                    tasks_html = "".join(task_items)
                    st.markdown(f"<div class='task-container'>{tasks_html}</div>", unsafe_allow_html=True)

st.divider()

# =================================-------------------------
# [3단] 이전달 / 일정 검색 / 다음달
# =================================-------------------------
col_nav1, col_nav2, col_nav3 = st.columns([1, 2.5, 1])

with col_nav1:
    if st.button("◀ 이전달", key="btn_prev_month", use_container_width=True):
        if month == 1:
            st.session_state.current_month = 12
            st.session_state.current_year -= 1
        else:
            st.session_state.current_month -= 1
        st.rerun()

with col_nav2:
    with st.expander("🔍 **일정 검색**", expanded=False):
        search_query = st.text_input("검색어 입력", placeholder="업무명/회의록 키워드", label_visibility="collapsed")
        if search_query:
            all_data = fetch_all_tasks()
            if not all_data.empty:
                search_df = all_data[
                    all_data['title'].astype(str).str.contains(search_query, case=False, na=False) |
                    all_data['memo'].astype(str).str.contains(search_query, case=False, na=False) |
                    all_data['meeting_notes'].astype(str).str.contains(search_query, case=False, na=False)
                ].sort_values(by="task_date", ascending=False)
            else:
                search_df = pd.DataFrame()

            if not search_df.empty:
                st.success(f"총 {len(search_df)}건 검색되었습니다.")
                for _, s_row in search_df.iterrows():
                    status_icon = "✅ 완료" if s_row['is_done'] else "⏳ 진행중"
                    meeting_icon = " [📝 회의]" if s_row['is_meeting'] else ""
                    st.write(f"• **{s_row['task_date']}** | **[{status_icon}]** {s_row['title']}{meeting_icon}")
                    if pd.notna(s_row['memo']) and s_row['memo']:
                        st.caption(f"  - 메모: {s_row['memo']}")
                    if s_row['is_meeting'] and pd.notna(s_row['meeting_notes']) and s_row['meeting_notes']:
                        st.caption(f"  - 회의록: {s_row['meeting_notes']}")
            else:
                st.warning("검색 결과가 없습니다.")

with col_nav3:
    if st.button("다음달 ▶", key="btn_next_month", use_container_width=True):
        if month == 12:
            st.session_state.current_month = 1
            st.session_state.current_year += 1
        else:
            st.session_state.current_month += 1
        st.rerun()

st.divider()

# =================================-------------------------
# [4단] 카드형 대시보드 요약
# =================================-------------------------
total_tasks = len(month_df) if not month_df.empty else 0
done_tasks = len(month_df[month_df['is_done'] == 1]) if total_tasks > 0 else 0
meeting_tasks = len(month_df[month_df['is_meeting'] == 1]) if total_tasks > 0 else 0
completion_rate = round((done_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown(f"""
        <div class="kpi-card">
            <p style="font-size: 12px; font-weight: 700; color: #64748B; margin-bottom: 2px;">월간 총 업무</p>
            <h3 style="font-size: 20px; font-weight: 800; color: #1E3A8A; margin: 0;">{total_tasks}건</h3>
        </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
        <div class="kpi-card">
            <p style="font-size: 12px; font-weight: 700; color: #64748B; margin-bottom: 2px;">완료된 업무</p>
            <h3 style="font-size: 20px; font-weight: 800; color: #166534; margin: 0;">{done_tasks}건</h3>
        </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
        <div class="kpi-card">
            <p style="font-size: 12px; font-weight: 700; color: #64748B; margin-bottom: 2px;">총 회의 건수</p>
            <h3 style="font-size: 20px; font-weight: 800; color: #D97706; margin: 0;">{meeting_tasks}건</h3>
        </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
        <div class="kpi-card">
            <p style="font-size: 12px; font-weight: 700; color: #64748B; margin-bottom: 2px;">이행률 (완료율)</p>
            <h3 style="font-size: 20px; font-weight: 800; color: #7C3AED; margin: 0;">{completion_rate}%</h3>
        </div>
    """, unsafe_allow_html=True)
