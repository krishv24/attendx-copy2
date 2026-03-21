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
        students = Student.query.all()
        alerts = Alert.query.all()
        
        low = sum(1 for s in students if s.risk_score == 'Low')
        med = sum(1 for s in students if s.risk_score == 'Medium')
        high = sum(1 for s in students if s.risk_score == 'High')
        crit = sum(1 for s in students if s.risk_score == 'Critical')
        
        from app.ai_cache import get_cached_ai_response
        from app.models import Config
        import os
        config_key = Config.query.filter_by(key='gemini_api_key').first()
        api_key = config_key.value if config_key else os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return "No Gemini API key available."
        os.environ['GEMINI_API_KEY'] = api_key
        
        stats_summary = (
            f"Total Students: {len(students)}\n"
            f"Risk Distribution: {low} Low | {med} Medium | {high} High | {crit} Critical\n"
            f"Alerts Triggered: {len(alerts)}\n"
            "Top At-Risk: "
        )
        
        at_risk = sorted([s for s in students if s.risk_score in ['High', 'Critical']], key=lambda x: x.predicted_attendance)
        for i, s in enumerate(at_risk[:10]):
            stats_summary += f"{s.name} ({s.predicted_attendance:.1f}% risk: {s.risk_score}), "
            
        prompt = f"Write a comprehensive, professional executive summary (about 150 words) on student attendance and at risk models based on this data: {stats_summary}. Use descriptive paragraphs, not exact code formatting, but retain key numbers. Sign off as 'AI Attendance System'."
        
        try:
            report_content = get_cached_ai_response(prompt, api_key=api_key)
        except Exception as e:
            report_content = "Failed to generate AI report: " + str(e)
            
        report = Report(title="Comprehensive AI Attendance Report", content=report_content)
        db.session.add(report)
        db.session.commit()
        
        return "Report generated and saved to database successfully."
    except Exception as e:
        db.session.rollback()
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
