# agents/alert_agent.py - Alert & Notification Agent
from crewai import Agent
from crewai.tools import tool
from app.models import Student, Alert
from app.extensions import db

@tool("Generate Risk Alerts")
def generate_alerts_tool(input: str = "") -> str:
    """
    Creates an Alert record for students whose predicted attendance is below 75%.
    Do NOT pass data into the input field. Queries the DB directly.
    """
    try:
        students = Student.query.filter(Student.predicted_attendance < 75.0).all()
        count = 0
        for s in students:
            existing = Alert.query.filter_by(student_id=s.id, alert_type='risk', is_read=False).first()
            if not existing:
                alert = Alert(
                    student_id=s.id,
                    message=f"Warning: predicted attendance is {s.predicted_attendance:.1f}% ({s.risk_score} risk)",
                    alert_type='risk'
                )
                db.session.add(alert)
                count += 1
                
        db.session.commit()
        return f"Created {count} new risk alerts."
    except Exception as e:
        db.session.rollback()
        return f"Error creating alerts: {str(e)}"

def create_agent(llm):
    return Agent(
        role="Early Warning System",
        goal="For every student whose predicted attendance will fall below 75%, create an Alert record",
        backstory="A specialized agent designed to flag at-risk students for early intervention.",
        verbose=True,
        allow_delegation=False,
        tools=[generate_alerts_tool],
        llm=llm
    )
