# agents/reporting_agent.py - Report generator
from crewai import Agent
from crewai.tools import tool
from app.models import Student, Alert, Report
from app.extensions import db

@tool("Generate Summary Report")
def generate_report_tool(input: str = "") -> str:
    """
    Compiles findings into the Report table in MySQL.
    Queries the database directly. Do NOT pass data to input.
    """
    try:
        from app.extensions import db
        import uuid
        from datetime import datetime
        
        students_query = db.collection('students').get()
        alerts_query = db.collection('alerts').get()
        
        students = [s.to_dict() for s in students_query]
        alerts = [a.to_dict() for a in alerts_query]
        
        low = sum(1 for s in students if s.get('risk_score') == 'Low')
        med = sum(1 for s in students if s.get('risk_score') == 'Medium')
        high = sum(1 for s in students if s.get('risk_score') == 'High')
        crit = sum(1 for s in students if s.get('risk_score') == 'Critical')
        
        from app.ai_cache import get_cached_ai_response
        import os
        config_doc = db.collection('configs').document('gemini_api_key').get()
        api_key = config_doc.to_dict().get('value') if config_doc.exists else os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return "No Gemini API key available."
        os.environ['GEMINI_API_KEY'] = api_key
        
        recent_anomalies = [a for a in alerts if a.get('alert_type') == 'anomaly']
        anam_text = "; ".join([f"{a.get('message')}" for a in recent_anomalies[:3]])
        
        stats_summary = (
            f"Total Students: {len(students)}\n"
            f"Risk Distribution: {low} Low | {med} Medium | {high} High | {crit} Critical\n"
            f"Alerts Triggered: {len(alerts)}\n"
            f"Recent Anomalies: {anam_text if anam_text else 'None'}\n"
            "Top At-Risk: "
        )
        
        at_risk = sorted([s for s in students if s.get('risk_score') in ['High', 'Critical']], key=lambda x: x.get('predicted_attendance', 0))
        for i, s in enumerate(at_risk[:10]):
            stats_summary += f"{s.get('name')} ({s.get('predicted_attendance',0):.1f}% risk: {s.get('risk_score')}), "
            
        prompt = (
            f"Write a highly actionable, concise, and heavily bulleted report based on this data: {stats_summary}.\n"
            "Do NOT write a long essay. Format the report strictly with these two headers:\n"
            "**Key Insights** (3 brief bullets max highlighting the biggest issues/anomalies)\n"
            "**Immediate Actions Required** (Specific steps for the admin to take for the highly at-risk students).\n\n"
            "Sign off as 'AI Attendance System'."
        )
        
        try:
            report_content = get_cached_ai_response(prompt, api_key=api_key)
        except Exception as e:
            report_content = "Failed to generate AI report: " + str(e)
            
        report_id = str(uuid.uuid4())
        db.collection('reports').document(report_id).set({
            'id': report_id,
            'title': "Comprehensive AI Attendance Report",
            'content': report_content,
            'generated_at': datetime.utcnow().isoformat()
        })
        
        return "Report generated and saved to database successfully."
    except Exception as e:
        return f"Error creating report: {str(e)}"

def create_agent(llm):
    return Agent(
        role="Administrative Report Generator",
        goal="Compile all findings into a structured text report and save to Report table",
        backstory="An executive assistant bot that summarizes data into executive reports.",
        verbose=True,
        allow_delegation=False,
        tools=[generate_report_tool],
        llm=llm
    )
