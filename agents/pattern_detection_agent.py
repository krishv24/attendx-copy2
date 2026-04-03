# agents/pattern_detection_agent.py - Detects patterns
from crewai import Agent
from crewai.tools import tool
from app.models import Attendance
import pandas as pd
import json

@tool("Detect Attendance Patterns")
def detect_patterns_tool(input: str = "") -> str:
    """
    Detects attendance patterns directly from the database.
    Do NOT pass previous data or JSON into the input. It must remain empty.
    Finds students with repeated absences and specific trends using recent data.
    """
    try:
        from app.extensions import db
        attendances = db.collection('attendances').get()
        if not attendances:
            return json.dumps({"error": "No data for pattern detection."})
            
        data = []
        for a in attendances:
            d = a.to_dict()
            data.append({'student_id': d.get('student_id'), 'subject': d.get('subject'), 'date': d.get('date'), 'status': d.get('status')})
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by='date', ascending=False)
        
        from app.ai_cache import get_cached_ai_response
        import os
        import json
        config_doc = db.collection('configs').document('gemini_api_key_2').get()
        api_key = config_doc.to_dict().get('value') if config_doc.exists else os.environ.get('GEMINI_API_KEY_2')
        if not api_key:
            api_key = os.environ.get('GEMINI_API_KEY')
            
        patterns = []
        grouped = df.groupby('student_id')
        
        histories = {}
        for student_id, group in grouped:
            recent = group.head(10)
            histories[student_id] = ", ".join(recent['status'].tolist())
            
        if api_key and histories:
            prompt = f"Analyze these recent 10-day attendance histories for students: {json.dumps(histories)}. If a student has 4+ absences or a declining/skipping pattern, record a short description of the pattern. If no clear pattern, omit them. Return ONLY valid JSON: {{\"patterns\": [{{\"student_id\": 1, \"pattern\": \"Skipping every other day\"}}]}}"
            try:
                res_text = get_cached_ai_response(prompt, api_key=api_key)
                json_str = res_text[res_text.find('{'):res_text.rfind('}')+1]
                patterns = json.loads(json_str).get('patterns', [])
            except:
                pass
                
        if not patterns:
            # fallback
            for student_id, group in grouped:
                recent = group.head(10)
                absences = (recent['status'] == 'Absent').sum()
                if absences >= 4:
                    patterns.append({'student_id': student_id, 'pattern': f'Repeated absences ({absences} in last 10 days)'})
                
        return json.dumps({"patterns": patterns})
    except Exception as e:
        return json.dumps({"error": str(e)})

def create_agent(llm):
    return Agent(
        role="Attendance Pattern Analyst",
        goal="Identify students with repeated absences on specific days, students avoiding specific subjects, and students showing a declining attendance trend over the last 4 weeks",
        backstory="Expert in identifying hidden patterns in student attendance data.",
        verbose=True,
        allow_delegation=False,
        tools=[detect_patterns_tool],
        llm=llm
    )
