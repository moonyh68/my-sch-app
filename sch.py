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
# 구글 캘린더 연동 설정
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
    """구글 캘린더 신규 일정 등록 (생성된 event_id 반환)"""
    try:
        service = get_calendar_service()
        start_datetime = f"{date_str}T{start_time_str}:00"
        end_datetime = f"{date_str}T{end_time_str}:00"

        event = {
            'summary': title,
            'description': memo if memo else '',
            'start': {'dateTime': start_datetime, 'timeZone': 'Asia/Seoul'},
            'end': {'dateTime': end_datetime, 'timeZone': 'Asia/Seoul'},
        }

        created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return True, str(created_event.get('id', '')), None
    except Exception as e:
        return False, "", str(e)

def update_google_calendar_event(event_id, date_str, start_time_str, end_time_str, title, memo):
    """구글 캘린더 일정 수정 (event_id 없거나 실패 시 새로 생성)"""
    try:
        service = get_calendar_service()
        start_datetime = f"{date_str}T{start_time_str}:00"
        end_datetime = f"{date_str}T{end_time_str}:00"

        event = {
            'summary': title,
            'description': memo if memo else '',
            'start': {'dateTime': start_datetime, 'timeZone': 'Asia/Seoul'},
            'end': {'dateTime': end_datetime, 'timeZone': 'Asia/Seoul'},
        }

        # event_id가 유효한 경우 기존 이벤트 수정 시도
        if event_id and not pd.isna(event_id) and str(event_id).strip() != "":
            try:
                service.events().update(calendarId=CALENDAR_ID, eventId=str(event_id), body=event).execute()
                return True, str(event_id), None
            except Exception:
                # 캘린더에 이벤트가 없는 경우 아래 신규 생성으로 진행
                pass

        # event_id가 없거나 기존 수정 실패 시 신규 등록
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
        service.events().delete(calendarId=CALENDAR_ID, eventId=str(event_id)).execute()
        return True, None
    except Exception as e:
        return False, str(e)

# ---------------------------------------------------------
# Custom CSS (음수 마진 및 레이아웃 최적화)
# ---------------------------------------------------------
st.markdown("""
    <style>
    .block-container {
        padding-top: 2.8rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        max-width: 100% !important;
    }
    
    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    hr {
        margin: 0.8rem 0 !important;
    }

    div[data-testid="stColumn"] div[data-testid="stVerticalBlock"] {
        gap: 0px !important;
    }

    div[data-testid="stColumn"] div[data-testid="stElementContainer"] {
        margin-bottom: 0px !important;
    }

    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] div.stButton > button {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        color: #1E293B !important;
        padding: 4px 2px !important;
        min-height: 38px !important;
        font-size: 14px !important;
        font-weight: 700 !important;
        border-radius: 6px !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
        transition: all 0.15s ease-in-out !important;
        margin-bottom: 0px !important;
    }

    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] div.stButton > button:hover {
        background-color: #F1F5F9 !important;
        border-color: #64748B !important;
        color: #0F172A !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    }

    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] div.stButton > button[kind="primary"] {
        background-color: #F0F9FF !important;
        border: 2px solid #0284C7 !important;
        color: #0369A1 !important;
        font-weight: 800 !important;
    }

    .task-container {
        background-color: transparent !important;
        border: none !important;
        padding: 0px !important;
        margin-top: -0.1px !important;
    }

    .task-item {
        font-size: 12.5px !important;
        font-weight: 600 !important;
        color: #1E293B !important;
        line-height: 1.25 !important;
        margin-bottom: 2px !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }

    div.stButton > button[key="btn_prev_month"], 
    div.stButton > button[key="btn_next_month"] {
        background-color: #1E3A8A !important;
        color: white !important;
        font-weight: bold !important;
        font-size: 13px !important;
        border-radius: 6px !important;
        padding: 6px 8px !important;
    }

    div[data-testid="stFormSubmitButton"] > button {
        background-color: #2E7D32 !important;
        color: white !important;
        font-weight: bold !important;
        font-size: 15px !important;
        border-radius: 6px !important;
    }

    div[data-testid="stExpander"] summary p {
        font-size: 13px !important;
        white-space: nowrap !important;
        word-break: keep-all !important;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-top: 2.2rem !important;
        }

        div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 1px !important;
        }

        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
            width: 14.28% !important;
            min-width: 0px !important;
            flex: 1 1 14.28% !important;
            padding: 0px !important;
        }

        div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] div.stButton > button {
            font-size: 11.5px !important;
            font-weight: 700 !important;
            min-height: 35px !important;
            padding: 1px 0px !important;
            letter-spacing: -0.5px !important;
        }

        .task-container {
            margin-top: -0.1px !important;
        }

        .task-item {
            font-size: 11px !important;
            line-height: 1.2 !important;
            letter-spacing: -0.5px !important;
            margin-bottom: 1px !important;
        }

        div[data-testid="stExpander"] summary p {
            font-size: 11.5px !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. 구글 시트 데이터베이스 연동 함수
# ---------------------------------------------------------
conn = st.connection("gsheets", type=GSheetsConnection)

def fetch_all_tasks():
    try:
        df = conn.read(ttl=0)
        expected_cols = ['id', 'task_date', 'start_time', 'end_time', 'title', 'memo', 'is_done', 'is_meeting', 'meeting_notes', 'event_id']
        
        if df.empty or 'id' not in df.columns:
            df = pd.DataFrame(columns=expected_cols)
        else:
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = ""
            df = df.astype(object)
            df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
            df['is_done'] = pd.to_numeric(df['is_done'], errors='coerce').fillna(0).astype(int)
            df['is_meeting'] = pd.to_numeric(df['is_meeting'], errors='coerce').fillna(0).astype(int)
            
            str_cols = ['task_date', 'start_time', 'end_time', 'title', 'memo', 'meeting_notes', 'event_id']
            for col in str_cols:
                df[col] = df[col].fillna("").astype(str)
        return df
    except Exception as e:
        return pd.DataFrame(columns=['id', 'task_date', 'start_time', 'end_time', 'title', 'memo', 'is_done', 'is_meeting', 'meeting_notes', 'event_id'])

def save_all_tasks(df):
    conn.update(data=df)

def fetch_month_tasks(year, month):
    df = fetch_all_tasks()
    if df.empty:
        return df
    prefix = f"{year}-{month:02d}"
    return df[df['task_date'].str.startswith(prefix)]

def insert_task(task_date, start_time, end_time, title, memo, is_done, is_meeting, meeting_notes):
    df = fetch_all_tasks()
    new_id = int(df['id'].max()) + 1 if not df.empty and df['id'].max() > 0 else 1
    
    cal_success, cal_event_id, cal_err = add_google_calendar_event(task_date, start_time, end_time, title, memo)
    
    new_row = pd.DataFrame([{
        'id': new_id,
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

def update_task_full(task_id, task_date, start_time, end_time, title, memo, is_meeting, meeting_notes):
    df = fetch_all_tasks()
    idx = df[df['id'] == int(task_id)].index
    if not idx.empty:
        old_event_id = str(df.loc[idx[0], 'event_id']) if 'event_id' in df.columns else ""
        
        # 구글 캘린더 연동 수행
        cal_success, new_event_id, cal_err = update_google_calendar_event(old_event_id, task_date, start_time, end_time, title, memo)
        
        df.loc[idx, 'start_time'] = str(start_time)
        df.loc[idx, 'end_time'] = str(end_time)
        df.loc[idx, 'title'] = str(title)
        df.loc[idx, 'memo'] = str(memo)
        df.loc[idx, 'is_meeting'] = int(is_meeting)
        df.loc[idx, 'meeting_notes'] = str(meeting_notes)
        
        if new_event_id:
            df.loc[idx, 'event_id'] = str(new_event_id)
            
        save_all_tasks(df)
        return cal_success, cal_err
    return True, None

def update_task_done(task_id, is_done):
    df = fetch_all_tasks()
    idx = df[df['id'] == int(task_id)].index
    if not idx.empty:
        df.loc[idx, 'is_done'] = int(is_done)
        save_all_tasks(df)

def delete_task(task_id):
    df = fetch_all_tasks()
    idx = df[df['id'] == int(task_id)].index
    if not idx.empty:
        event_id = str(df.loc[idx[0], 'event_id']) if 'event_id' in df.columns else ""
        updated_df = df[df['id'] != int(task_id)]
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
# 3. 팝업 모달 다이얼로그
# ---------------------------------------------------------
@st.dialog("📅 일자별 상세 일정 및 회의록", width="large")
def open_day_modal(target_date):
    date_str = target_date.strftime("%Y-%m-%d")
    st.markdown(f"### `{date_str}` 일정 관리")

    all_df = fetch_all_tasks()
    tasks_df = all_df[all_df['task_date'] == date_str].sort_values(by="start_time") if not all_df.empty else pd.DataFrame()

    if not tasks_df.empty:
        st.markdown("**📋 등록된 일정 및 수정**")
        for idx, row in tasks_df.iterrows():
            status_text = "✅ 완료" if row['is_done'] else "⏳ 진행중"
            with st.expander(f"[{status_text}] {row['start_time']}~{row['end_time']} | {row['title']}", expanded=False):
                with st.form(key=f"edit_form_{row['id']}"):
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
                        edit_start = st.time_input("시작 시간", value=st_time_val, key=f"e_start_{row['id']}")
                    with col_e2:
                        edit_end = st.time_input("종료 시간", value=et_time_val, key=f"e_end_{row['id']}")

                    edit_title = st.text_input("업무명 / 안건", value=row['title'], key=f"e_title_{row['id']}")
                    edit_memo = st.text_input("메모", value=row['memo'] if pd.notna(row['memo']) else "", key=f"e_memo_{row['id']}")
                    edit_is_meeting = st.checkbox("회의 여부", value=bool(row['is_meeting']), key=f"e_chk_mt_{row['id']}")

                    edit_meeting_notes = ""
                    if edit_is_meeting:
                        edit_meeting_notes = st.text_area("회의 내용 및 결정 사항", value=row['meeting_notes'] if pd.notna(row['meeting_notes']) else "", key=f"e_notes_{row['id']}")

                    save_changes = st.form_submit_button("💾 수정사항 저장", use_container_width=True)

                    if save_changes:
                        success, err_msg = update_task_full(
                            row['id'],
                            date_str,
                            edit_start.strftime("%H:%M"),
                            edit_end.strftime("%H:%M"),
                            edit_title,
                            edit_memo,
                            edit_is_meeting,
                            edit_meeting_notes
                        )
                        if success:
                            st.session_state["cal_status"] = "success"
                            st.session_state["cal_msg"] = "일정 수정 내용이 구글 캘린더에 동기화되었습니다."
                        else:
                            st.session_state["cal_status"] = "error"
                            st.session_state["cal_msg"] = f"구글 캘린더 수정 실패: {err_msg}"
                        st.rerun()

                col_chk, col_del = st.columns([2, 1])
                with col_chk:
                    chk_label = "✅ 완료 상태" if row['is_done'] else "🟢 완료 처리하기"
                    done_chk = st.checkbox(f"**{chk_label}**", value=bool(row['is_done']), key=f"chk_done_{row['id']}")
                    if done_chk != bool(row['is_done']):
                        update_task_done(row['id'], done_chk)
                        st.rerun()
                with col_del:
                    if st.button("🗑️ 삭제", key=f"del_btn_{row['id']}", use_container_width=True):
                        success, err_msg = delete_task(row['id'])
                        if success:
                            st.session_state["cal_status"] = "success"
                            st.session_state["cal_msg"] = "일정이 삭제되었으며 구글 캘린더에서도 제거되었습니다."
                        else:
                            st.session_state["cal_status"] = "error"
                            st.session_state["cal_msg"] = f"구글 캘린더 삭제 실패: {err_msg}"
                        st.rerun()
        st.divider()

    st.markdown("**➕ 새 일정 추가**")
    with st.form("add_task_form", clear_on_submit=False):
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
                success, err_msg = insert_task(
                    date_str,
                    start_t.strftime("%H:%M"),
                    end_t.strftime("%H:%M"),
                    title,
                    memo,
                    False,
                    is_meeting,
                    meeting_notes
                )
                if success:
                    st.session_state["cal_status"] = "success"
                    st.session_state["cal_msg"] = "새 일정이 저장되었으며 구글 캘린더에도 수록되었습니다."
                else:
                    st.session_state["cal_status"] = "error"
                    st.session_state["cal_msg"] = f"구글 캘린더 등록 실패: {err_msg}"
                st.rerun()

# =================================-------------------------
# [1단] 최상단 년/월 표시 및 상태 메시지 고정 영역
# =================================-------------------------
st.markdown(
    f"<h2 style='text-align: center; font-weight: 800; font-size: 26px; margin: 0 0 12px 0; padding: 0; line-height: 1.3;'><span style='color: #1E3A8A;'>{year}년</span> <span style='color: #2E7D32;'>{month}월</span></h2>",
    unsafe_allow_html=True
)

if st.session_state.get("cal_status") == "error":
    st.error(f"⚠️ **동기화 오류**: {st.session_state.get('cal_msg')}")
elif st.session_state.get("cal_status") == "success":
    st.success(f"✅ {st.session_state.get('cal_msg')}")

# =================================-------------------------
# [2단] 월간 달력 영역
# =================================-------------------------
days_of_week = [("일", "#E53935"), ("월", "#333333"), ("화", "#333333"), ("수", "#333333"), ("목", "#333333"), ("금", "#333333"), ("토", "#1E88E5")]

cols = st.columns(7)
for idx, (day_name, color_code) in enumerate(days_of_week):
    cols[idx].markdown(f"<div style='text-align: center; color: {color_code}; font-weight: bold; font-size: 15px; padding: 2px 0; border-bottom: 2px solid #CBD5E1; margin-bottom: 6px;'>{day_name}</div>", unsafe_allow_html=True)

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
                day_done = len(day_tasks[day_tasks['is_done'] == 1]) if day_total > 0 else 0

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
                        icon = "✅" if t['is_done'] else "📌"
                        task_items.append(f"<div class='task-item'>{icon} {t['start_time']} {str(t['title'])[:6]}</div>")
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
# [4단] 대시보드 요약 표시
# =================================-------------------------
total_tasks = len(month_df) if not month_df.empty else 0
done_tasks = len(month_df[month_df['is_done'] == 1]) if total_tasks > 0 else 0
meeting_tasks = len(month_df[month_df['is_meeting'] == 1]) if total_tasks > 0 else 0
completion_rate = round((done_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.markdown("<p style='font-weight: bold; font-size: 13px; margin-bottom: 0;'>월간 총 업무</p>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='color: #1E3A8A; font-weight: bold; margin-top: 0;'>{total_tasks}건</h3>", unsafe_allow_html=True)

with kpi2:
    st.markdown("<p style='font-weight: bold; font-size: 13px; margin-bottom: 0;'>완료된 업무</p>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='color: #2E7D32; font-weight: bold; margin-top: 0;'>{done_tasks}건</h3>", unsafe_allow_html=True)

with kpi3:
    st.markdown("<p style='font-weight: bold; font-size: 13px; margin-bottom: 0;'>총 회의 건수</p>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='color: #D97706; font-weight: bold; margin-top: 0;'>{meeting_tasks}건</h3>", unsafe_allow_html=True)

with kpi4:
    st.markdown("<p style='font-weight: bold; font-size: 13px; margin-bottom: 0;'>이행률 (완료율)</p>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='color: #7C3AED; font-weight: bold; margin-top: 0;'>{completion_rate}%</h3>", unsafe_allow_html=True)
