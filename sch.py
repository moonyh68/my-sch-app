# ---------------------------------------------------------
# 1. 구글 시트 데이터베이스 연동 함수 (데이터 손실 방지 수정)
# ---------------------------------------------------------
conn = st.connection("gsheets", type=GSheetsConnection)

def fetch_all_tasks():
    try:
        # ttl=0으로 실시간 데이터 조회
        df = conn.read(ttl=0)
        expected_cols = ['id', 'task_date', 'start_time', 'end_time', 'title', 'memo', 'is_done', 'is_meeting', 'meeting_notes', 'event_id']
        
        if df is None or df.empty:
            return pd.DataFrame(columns=expected_cols)
            
        # 컬럼 존재 여부 체크 및 빈 값 채우기
        for col in expected_cols:
            if col not in df.columns:
                df[col] = ""
                
        # id 컬럼 빈 값 제거 및 숫자형 정렬
        df = df.dropna(subset=['task_date']).copy()
        df = df[df['task_date'].astype(str).str.strip() != ""].copy()
        
        # ID 안전 변환
        df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
        df = df[df['id'] > 0].copy()
        
        # 데이터 타입 정규화
        df['is_done'] = pd.to_numeric(df['is_done'], errors='coerce').fillna(0).astype(int)
        df['is_meeting'] = pd.to_numeric(df['is_meeting'], errors='coerce').fillna(0).astype(int)
        
        str_cols = ['task_date', 'start_time', 'end_time', 'title', 'memo', 'meeting_notes', 'event_id']
        for col in str_cols:
            df[col] = df[col].fillna("").astype(str).str.strip()
            
        # 날짜 YYYY-MM-DD 포맷 규격화
        def normalize_date(d_str):
            try:
                dt = pd.to_datetime(d_str, errors='coerce')
                if pd.notna(dt):
                    return dt.strftime("%Y-%m-%d")
            except Exception:
                pass
            return str(d_str).strip()

        df['task_date'] = df['task_date'].apply(normalize_date)
            
        return df.reset_index(drop=True)
    except Exception as e:
        return pd.DataFrame(columns=['id', 'task_date', 'start_time', 'end_time', 'title', 'memo', 'is_done', 'is_meeting', 'meeting_notes', 'event_id'])

def save_all_tasks(df):
    """구글 시트 전체 업데이트시 데이터 보격화 후 저장"""
    expected_cols = ['id', 'task_date', 'start_time', 'end_time', 'title', 'memo', 'is_done', 'is_meeting', 'meeting_notes', 'event_id']
    
    clean_df = df.copy()
    for col in expected_cols:
        if col not in clean_df.columns:
            clean_df[col] = ""
            
    clean_df = clean_df[expected_cols].reset_index(drop=True)
    
    # 구글 시트에 저장 시 문자열/숫자 타입 명확히 지정하여 저장시 오류 방지
    clean_df['id'] = clean_df['id'].astype(int)
    clean_df['is_done'] = clean_df['is_done'].astype(int)
    clean_df['is_meeting'] = clean_df['is_meeting'].astype(int)
    
    conn.update(data=clean_df)

def fetch_month_tasks(year, month):
    df = fetch_all_tasks()
    if df.empty:
        return df
    
    # 해당 연/월 필터링 (ISO 포맷 비교)
    target_prefix = f"{year}-{month:02d}"
    return df[df['task_date'].str.startswith(target_prefix)].copy()
