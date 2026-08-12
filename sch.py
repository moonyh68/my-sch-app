# ---------------------------------------------------------
# 구글 시트 데이터베이스 처리 함수 (데이터 손실 방지 강화)
# ---------------------------------------------------------
def fetch_all_tasks():
    try:
        # ttl=0으로 실시간 데이터 읽기
        df = conn.read(ttl=0)
        expected_cols = ['id', 'task_date', 'start_time', 'end_time', 'title', 'memo', 'is_done', 'is_meeting', 'meeting_notes', 'event_id']
        
        if df is None or df.empty:
            return pd.DataFrame(columns=expected_cols)
            
        # 누락된 컬럼 자동 생성
        for col in expected_cols:
            if col not in df.columns:
                df[col] = ""
                
        # 완전히 비어있는 행만 제거
        df = df.dropna(how='all').copy()
        
        # task_date가 비어있는 행 제거
        df['task_date_str'] = df['task_date'].astype(str).str.strip()
        df = df[df['task_date_str'] != ""].copy()
        df = df[df['task_date_str'] != "nan"].copy()
        df = df.drop(columns=['task_date_str'])
        
        # ID 값 안전 보정 (0이거나 유효하지 않은 ID 재부여)
        df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
        if (df['id'] == 0).any():
            df['id'] = range(1, len(df) + 1)
        
        df['is_done'] = pd.to_numeric(df['is_done'], errors='coerce').fillna(0).astype(int)
        df['is_meeting'] = pd.to_numeric(df['is_meeting'], errors='coerce').fillna(0).astype(int)
        
        str_cols = ['task_date', 'start_time', 'end_time', 'title', 'memo', 'meeting_notes', 'event_id']
        for col in str_cols:
            df[col] = df[col].fillna("").astype(str).str.strip()
            
        # 날짜 YYYY-MM-DD 포맷 정규화
        def normalize_date(d_str):
            try:
                dt = pd.to_datetime(d_str, errors='coerce')
                if pd.notna(dt):
                    return dt.strftime("%Y-%m-%d")
            except Exception:
                pass
            return str(d_str).strip()

        df['task_date'] = df['task_date'].apply(normalize_date)
            
        return df[expected_cols].reset_index(drop=True)
    except Exception as e:
        st.error(f"구글 시트 읽기 실패: {e}")
        return pd.DataFrame(columns=['id', 'task_date', 'start_time', 'end_time', 'title', 'memo', 'is_done', 'is_meeting', 'meeting_notes', 'event_id'])

def save_all_tasks(df):
    """구글 시트 안전 저장 함수"""
    expected_cols = ['id', 'task_date', 'start_time', 'end_time', 'title', 'memo', 'is_done', 'is_meeting', 'meeting_notes', 'event_id']
    clean_df = df.copy()
    
    for col in expected_cols:
        if col not in clean_df.columns:
            clean_df[col] = ""
            
    clean_df = clean_df[expected_cols].reset_index(drop=True)
    clean_df['id'] = clean_df['id'].astype(int)
    clean_df['is_done'] = clean_df['is_done'].astype(int)
    clean_df['is_meeting'] = clean_df['is_meeting'].astype(int)
    
    # 저장 실행
    conn.update(data=clean_df)

def insert_task(task_date, start_time, end_time, title, memo, is_done=0, is_meeting=0, meeting_notes=""):
    # 1. 저장 전 기존 데이터 읽기
    df = fetch_all_tasks()
    
    # 2. 신규 ID 계산
    if not df.empty and len(df['id']) > 0:
        new_id = int(df['id'].max()) + 1
    else:
        new_id = 1
    
    # 3. 구글 캘린더 이벤트 등록
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
    
    # 4. 기존 데이터 + 신규 데이터 결합 후 저장
    if df.empty:
        updated_df = new_row
    else:
        updated_df = pd.concat([df, new_row], ignore_index=True)
        
    save_all_tasks(updated_df)
    return cal_success, cal_err
