import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime

# ---------------------------------------------------------
# 1. Page Configuration & Custom CSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="월간 일정표 관리 시스템",
    page_icon="📅",
    layout="wide"
)

st.markdown("""
<style>
    .kpi-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #0066cc;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .kpi-title {
        font-size: 14px;
        color: #6c757d;
        margin-bottom: 5px;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: bold;
        color: #212529;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Google Sheets API 연동 및 캐싱 처리 (Rate Limit 예방)
# ---------------------------------------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def init_gspread():
    """구글 시트 API 인증 연결 함수"""
    try:
        # Streamlit Secrets에서 인증 정보를 가져옵니다.
        creds_dict = st.secrets["gcp_service_account"]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"구글 인증 실패: Secrets 설정을 확인해 주세요. ({e})")
        st.stop()

@st.cache_data(ttl=60)
def load_data_from_sheets():
    """구글 시트 데이터 가져오기 (1분 캐싱)"""
    client = init_gspread()
    try:
        # DB 시트 이름 지정
        sheet = client.open("월간일정표_DB").sheet1
        records = sheet.get_all_records()
        df = pd.DataFrame(records)
        
        # 필수 컬럼 정의 및 결측값 보정
        required_columns = ["ID", "날짜", "카테고리", "일정명", "상세내용", "담당자", "상태", "비고"]
        for col in required_columns:
            if col not in df.columns:
                df[col] = ""
                
        # 데이터 타입 정제 (Zero / Null 처리)
        if not df.empty:
            df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce').dt.strftime('%Y-%m-%d')
            df['날짜'] = df['날짜'].fillna(datetime.date.today().strftime('%Y-%m-%d'))
        
        return df
    except Exception as e:
        st.warning(f"데이터를 불러오는 중 오류가 발생했거나 시트가 비어있습니다: {e}")
        return pd.DataFrame(columns=["ID", "날짜", "카테고리", "일정명", "상세내용", "담당자", "상태", "비고"])

def clear_cache_and_rerun():
    """데이터 변경 시 캐시를 초기화하고 화면을 갱신하는 함수"""
    st.cache_data.clear()
    st.rerun()

# ---------------------------------------------------------
# 3. Main UI Header
# ---------------------------------------------------------
st.title("📅 스마트 월간 일정 관리 시스템")
st.caption("Google Drive 시트 연동 기반 실시간 스케줄 관리자")

df_tasks = load_data_from_sheets()

# ---------------------------------------------------------
# 4. KPI Summary Dashboards (ZeroDivisionError 검증 완료)
# ---------------------------------------------------------
total_tasks = len(df_tasks)
completed_tasks = len(df_tasks[df_tasks["상태"] == "완료"]) if not df_tasks.empty else 0
in_progress_tasks = len(df_tasks[df_tasks["상태"] == "진행중"]) if not df_tasks.empty else 0

# 분모 0 에러 예방 조건문 적용
completion_rate = round((completed_tasks / total_tasks) * 100, 1) if total_tasks > 0 else 0.0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">전체 일정</div>
        <div class="kpi-value">{total_tasks} 건</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color: #28a745;">
        <div class="kpi-title">완료된 일정</div>
        <div class="kpi-value">{completed_tasks} 건</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color: #ffc107;">
        <div class="kpi-title">진행중인 일정</div>
        <div class="kpi-value">{in_progress_tasks} 건</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color: #17a2b8;">
        <div class="kpi-title">달성률</div>
        <div class="kpi-value">{completion_rate} %</div>
    </div>
    """, unsafe_allow_html=True)

st.write("---")

# ---------------------------------------------------------
# 5. 일정 등록 / 수정 / 삭제 탭 구성
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📋 일정 조회 및 관리", "➕ 새 일정 추가", "✏️ 일정 수정/삭제"])

# Tab 1: 일정 목록 조회
with tab1:
    st.subheader("등록된 일정 목록")
    if df_tasks.empty:
        st.info("현재 등록된 일정이 없습니다. [새 일정 추가] 탭에서 등록해 주세요.")
    else:
        # 필터링 옵션
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            category_filter = st.multiselect("카테고리 필터", options=df_tasks["카테고리"].unique())
        with col_f2:
            status_filter = st.multiselect("상태 필터", options=["대기", "진행중", "완료"])

        filtered_df = df_tasks.copy()
        if category_filter:
            filtered_df = filtered_df[filtered_df["카테고리"].isin(category_filter)]
        if status_filter:
            filtered_df = filtered_df[filtered_df["상태"].isin(status_filter)]

        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

# Tab 2: 새 일정 등록
with tab2:
    st.subheader("신규 일정 등록")
    with st.form("add_task_form", clear_on_submit=True):
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            new_date = st.date_input("일자", datetime.date.today())
            new_category = st.selectbox("카테고리", ["회의", "업무", "개인", "기타"])
            new_title = st.text_input("일정명 (필수)")
        with col_a2:
            new_assignee = st.text_input("담당자")
            new_status = st.selectbox("상태", ["대기", "진행중", "완료"])
            new_note = st.text_input("비고")
        
        new_detail = st.text_area("상세내용")
        submit_btn = st.form_submit_button("일정 저장하기")

        if submit_btn:
            if not new_title.strip():
                st.error("일정명은 필수 입력 항목입니다.")
            else:
                try:
                    client = init_gspread()
                    sheet = client.open("월간일정표_DB").sheet1
                    
                    # 새로운 ID 생성
                    new_id = len(df_tasks) + 1
                    new_row = [
                        new_id,
                        str(new_date),
                        new_category,
                        new_title,
                        new_detail,
                        new_assignee,
                        new_status,
                        new_note
                    ]
                    
                    sheet.append_row(new_row)
                    st.success(f"'{new_title}' 일정이 성공적으로 등록되었습니다!")
                    clear_cache_and_rerun()
                except Exception as e:
                    st.error(f"저장 중 오류가 발생했습니다: {e}")

# Tab 3: 일정 수정 및 삭제 (1-based index 매핑 검증 완료)
with tab3:
    st.subheader("일정 수정 및 삭제")
    if df_tasks.empty:
        st.info("수정/삭제할 데이터가 존재하지 않습니다.")
    else:
        task_list = [f"{row['ID']} - [{row['날짜']}] {row['일정명']}" for _, row in df_tasks.iterrows()]
        selected_task_str = st.selectbox("수정/삭제할 일정을 선택하세요", task_list)
        
        selected_id = int(selected_task_str.split(" - ")[0])
        # 선택한 행 추출
        selected_row_idx = df_tasks[df_tasks["ID"] == selected_id].index[0]
        selected_data = df_tasks.loc[selected_row_idx]

        # 구글 시트 실제 행 인덱스 (헤더가 1행이므로 DataFrame index + 2)
        sheet_row_num = int(selected_row_idx) + 2

        col_e1, col_e2 = st.columns(2)
        with col_e1:
            edit_date = st.date_input("일자 변경", datetime.datetime.strptime(str(selected_data["날짜"]), '%Y-%m-%d').date())
            edit_category = st.selectbox("카테고리 변경", ["회의", "업무", "개인", "기타"], index=["회의", "업무", "개인", "기타"].index(selected_data["카테고리"]) if selected_data["카테고리"] in ["회의", "업무", "개인", "기타"] else 0)
            edit_title = st.text_input("일정명 변경", value=str(selected_data["일정명"]))
        with col_e2:
            edit_assignee = st.text_input("담당자 변경", value=str(selected_data["담당자"]))
            edit_status = st.selectbox("상태 변경", ["대기", "진행중", "완료"], index=["대기", "진행중", "완료"].index(selected_data["상태"]) if selected_data["상태"] in ["대기", "진행중", "완료"] else 0)
            edit_note = st.text_input("비고 변경", value=str(selected_data["비고"]))

        edit_detail = st.text_area("상세내용 변경", value=str(selected_data["상세내용"]))

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("수정 내용 저장"):
                try:
                    client = init_gspread()
                    sheet = client.open("월간일정표_DB").sheet1
                    
                    updated_row = [
                        selected_id,
                        str(edit_date),
                        edit_category,
                        edit_title,
                        edit_detail,
                        edit_assignee,
                        edit_status,
                        edit_note
                    ]
                    
                    # 시트 업데이트 (1-based index)
                    sheet.update(f"A{sheet_row_num}:H{sheet_row_num}", [updated_row])
                    st.success("일정이 수정되었습니다.")
                    clear_cache_and_rerun()
                except Exception as e:
                    st.error(f"수정 실패: {e}")

        with btn_col2:
            if st.button("선택한 일정 삭제", type="primary"):
                try:
                    client = init_gspread()
                    sheet = client.open("월간일정표_DB").sheet1
                    
                    sheet.delete_rows(sheet_row_num)
                    st.success("일정이 삭제되었습니다.")
                    clear_cache_and_rerun()
                except Exception as e:
                    st.error(f"삭제 실패: {e}")
