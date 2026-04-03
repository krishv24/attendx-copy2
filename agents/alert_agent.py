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
        from app.extensions import db
        import uuid
        from datetime import datetime
        
        students_query = db.collection('students').where('predicted_attendance', '<', 75.0).get()
        count = 0
        for s_doc in students_query:
            s = s_doc.to_dict()
            s_id = s.get('id')
            
            existing = db.collection('alerts').where('student_id', '==', str(s_id)).where('alert_type', '==', 'risk').where('is_read', '==', False).limit(1).get()
            if not existing:
                alert_id = str(uuid.uuid4())
                db.collection('alerts').document(alert_id).set({
                    'id': alert_id,
                    'student_id': str(s_id),
                    'message': f"Warning: predicted attendance is {s.get('predicted_attendance'):.1f}% ({s.get('risk_score')} risk)",
                    'alert_type': 'risk',
                    'is_read': False,
                    'created_at': datetime.utcnow().isoformat()
                })
                count += 1
                
        return f"Created {count} new risk alerts."
    except Exception as e:
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
