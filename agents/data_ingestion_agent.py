# agents/data_ingestion_agent.py - Fetches data
from crewai import Agent
from crewai.tools import tool
from app.models import Attendance
import pandas as pd
import json

@tool("Fetch Attendance Data")
def fetch_attendance_data_tool(input: str = "") -> str:
    """
    Fetches all attendance records directly from the database. 
    Do NOT pass data or JSON into the input argument. It must be left empty.
    Returns computed attendance percentages per student.
    """
    try:
        from app.extensions import db
        attendances = db.collection('attendances').get()
        if not attendances:
            return json.dumps({"error": "No attendance records found."})
        
        data = []
        for a in attendances:
            d = a.to_dict()
            data.append({'student_id': d.get('student_id'), 'subject': d.get('subject'), 'date': d.get('date'), 'status': d.get('status')})
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        
        percentage_df = df.groupby('student_id').apply(lambda x: (x['status'] == 'Present').mean() * 100).reset_index()
        percentage_df.columns = ['student_id', 'attendance_percentage']
        
        return json.dumps({
            "summary": percentage_df.to_dict(orient='records'),
            "total_records": len(df)
        })
    except Exception as e:
        return json.dumps({"error": str(e)})

def create_agent(llm):
    return Agent(
        role="Data Ingestion Specialist",
        goal="Fetch all attendance records from MySQL, compute per-student attendance percentages, and return clean structured data",
        backstory="Data engineering expert handling DB extraction and pandas aggregation.",
        verbose=True,
        allow_delegation=False,
        tools=[fetch_attendance_data_tool],
        llm=llm
    )
