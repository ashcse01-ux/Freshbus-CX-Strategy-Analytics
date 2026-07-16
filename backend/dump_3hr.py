import pandas as pd
from database import get_tenant_db_engine
import models
from sqlalchemy.orm import sessionmaker
import warnings
warnings.filterwarnings('ignore')

def parse_time_to_seconds(time_str):
    if not time_str or pd.isna(time_str) or str(time_str).strip() == '':
        return 0
    try:
        parts = str(time_str).strip().split(':')
        if len(parts) == 3: # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2: # MM:SS
            return int(parts[0]) * 60 + int(parts[1])
        return 0
    except:
        return 0

engine = get_tenant_db_engine("Inbound")
TenantSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = TenantSessionLocal()

query = db.query(models.CallRecord)
df = pd.read_sql(query.statement, engine)
db.close()

if not df.empty:
    text_cols = ['Agent', 'Status', 'Campaign', 'Disposition', 'Hangup_By', 'DID', 'Skill', 'Call_Type', 'Dial_Status', 'Transfer_Details', 'Ratings']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip().str.lower()
            df.loc[df[col].isin(['nan', 'none', 'null', '<na>']), col] = ''

    df['Call_Date_DT'] = pd.to_datetime(df['Call_Date'], format='%d-%m-%Y', errors='coerce')
    df = df.dropna(subset=['Call_Date_DT'])
    
    df['Timestamp'] = pd.to_datetime(df['Call_Date'] + ' ' + df['Start_Time'], format='%d-%m-%Y %H:%M:%S', errors='coerce')
    nat_mask = df['Timestamp'].isna() & df['Call_Date'].notna() & df['Start_Time'].notna()
    if nat_mask.any():
        df.loc[nat_mask, 'Timestamp'] = pd.to_datetime(df.loc[nat_mask, 'Call_Date'] + ' ' + df.loc[nat_mask, 'Start_Time'], errors='coerce')

    if 'Call_ID' in df.columns:
        df['temp_TTA_Sec'] = df['Time_to_Answer'].apply(parse_time_to_seconds)
        df['temp_Dur_Sec'] = df['Duration'].apply(parse_time_to_seconds)
        
        min_ts = df.groupby('Call_ID')['Timestamp'].min()
        df['Min_Timestamp'] = df['Call_ID'].map(min_ts)
        
        df['Actual_Answer_Time'] = df['Timestamp'] + pd.to_timedelta(df['temp_TTA_Sec'], unit='s')
        df['Actual_End_Time'] = df['Timestamp'] + pd.to_timedelta(df['temp_Dur_Sec'], unit='s')
        
        df['Cum_TTA_Sec'] = (df['Actual_Answer_Time'] - df['Min_Timestamp']).dt.total_seconds().fillna(0).astype(int)
        
        max_end_ts = df.groupby('Call_ID')['Actual_End_Time'].max()
        df['Max_End_Timestamp'] = df['Call_ID'].map(max_end_ts)
        df['Cum_Dur_Sec'] = (df['Max_End_Timestamp'] - df['Min_Timestamp']).dt.total_seconds().fillna(0).astype(int)
        
        df['_status_score'] = df['Status'].apply(lambda x: 0 if str(x).lower().strip() == 'answered' else 1)
        df['_agent_score'] = df['Agent'].apply(lambda x: 0 if str(x).strip() != '' else 1)
        df['_disp_score'] = df['Disposition'].apply(lambda x: 0 if str(x).strip() != '' else 1)
        
        df = df.sort_values(by=['_status_score', '_agent_score', '_disp_score', 'Timestamp'])
        df = df.drop_duplicates(subset=['Call_ID'], keep='first')
        
        df['TTA_Sec_Override'] = df['Cum_TTA_Sec']
        df['Duration_Sec_Override'] = df['Cum_Dur_Sec']
        
        df = df.drop(columns=['_status_score', '_agent_score', '_disp_score', 'Min_Timestamp', 'Actual_Answer_Time', 'Actual_End_Time', 'Max_End_Timestamp', 'Cum_TTA_Sec', 'Cum_Dur_Sec', 'temp_TTA_Sec', 'temp_Dur_Sec'])

    base_time = pd.Timestamp.now(tz='Asia/Kolkata').tz_localize(None)
    if pd.notna(base_time):
        df_3hr = df[df['Timestamp'] >= (base_time - pd.Timedelta(hours=3))]
        
        out_path = r"c:\Users\Ayush Jain\Downloads\Freshbus CX Analytics\3hr_data_dump.csv"
        df_3hr.to_csv(out_path, index=False)
        print("Successfully generated 3hr_data_dump.csv with size:", len(df_3hr))
    else:
        print("No valid timestamps found.")
else:
    print("Database is empty.")
