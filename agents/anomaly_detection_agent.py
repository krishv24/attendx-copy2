# agents/anomaly_detection_agent.py - Anomaly Detection
from crewai import Agent
from crewai.tools import tool
from app.models import Attendance, Student, Alert
from app.extensions import db
import pandas as pd

@tool("Detect Anomalies")
def detect_anomalies_tool(input: str = "") -> str:
    """
    Detects class-wide unusual events and flags as anomaly alerts.
    Do NOT pass data into the input. Queries the DB directly.
    """
    try:
        from app.extensions import db
        import uuid
        from datetime import datetime
        attendances = db.collection('attendances').get()
        if not attendances:
            return "No data for anomalies."
            
        data = []
        for a in attendances:
            d = a.to_dict()
            data.append({'student_id': d.get('student_id'), 'date': d.get('date'), 'status': d.get('status')})
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        
        from app.ai_cache import get_cached_ai_response
        import os
        import json
        config_doc = db.collection('configs').document('gemini_api_key').get()
        api_key = config_doc.to_dict().get('value') if config_doc.exists else os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return "No Gemini API key available."
        os.environ['GEMINI_API_KEY'] = api_key
        
        results = []
        daily_stats = df.groupby('date').apply(lambda x: (x['status'] == 'Absent').mean() * 100).reset_index(name='absence_rate')
        
        days_data = [{"date": row['date'].strftime('%Y-%m-%d'), "rate": round(row['absence_rate'], 1)} for _, row in daily_stats.iterrows()]
        high_absent_days = []
        
        if days_data and api_key:
            prompt = f"Evaluate these daily class absence rates: {json.dumps(days_data)}. Normal absence is under 20%. Return ONLY valid JSON listing dates considered an statistically alarming 'Anomaly': {{\"anomalies\": [\"2023-10-01\", \"2023-10-05\"]}}"
            try:
                res_text = get_cached_ai_response(prompt, api_key=api_key)
                json_str = res_text[res_text.find('{'):res_text.rfind('}')+1]
                anomalous_dates = json.loads(json_str).get('anomalies', [])
                
                for _, row in daily_stats.iterrows():
                    d_str = row['date'].strftime('%Y-%m-%d')
                    if d_str in anomalous_dates:
                        high_absent_days.append(row)
                        msg = f"Class-wide Anomaly detected by AI: On {d_str}, {row['absence_rate']:.1f}% absences."
                        results.append(msg)
            except:
                pass
                
        high_absent_days = pd.DataFrame(high_absent_days)
        if high_absent_days.empty:
            return "No anomalies detected."
            
        for _, row in high_absent_days.iterrows():
            date_str = row['date'].strftime('%Y-%m-%d')
            
            absent_that_day = df[(df['date'] == row['date']) & (df['status'] == 'Absent')]
            for sid in absent_that_day['student_id'].unique():
                alert_id = str(uuid.uuid4())
                db.collection('alerts').document(alert_id).set({
                    'id': alert_id,
                    'student_id': str(sid),
                    'message': f"Anomaly: High class absence on {date_str}.",
                    'alert_type': 'anomaly',
                    'is_read': False,
                    'created_at': datetime.utcnow().isoformat()
                })
                
        return f"Detected {len(high_absent_days)} anomaly days. " + " | ".join(results)
    except Exception as e:
        return f"Error storing anomalies: {str(e)}"

def create_agent(llm):
    return Agent(
        role="Anomaly Detection Specialist",
        goal="Detect class-wide unusual events and flag them as anomalies",
        backstory="A statistical outlier detection bot.",
        verbose=True,
        allow_delegation=False,
        tools=[detect_anomalies_tool],
        llm=llm
    )
