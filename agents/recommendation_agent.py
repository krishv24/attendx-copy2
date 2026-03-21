# agents/recommendation_agent.py - Generates recommendations with LLM
from crewai import Agent
from crewai.tools import tool
from app.models import Student, Alert
from app.extensions import db
import os

@tool("Provide Recommendations")
def provide_recommendations_tool(input: str = "") -> str:
    """
    Generates personalized text recommendations for students with Medium/High/Critical risk.
    Do NOT pass data in input. Keep it empty.
    """
    try:
        from app.ai_cache import get_cached_ai_response
        from app.models import Config
        import os
        import json
        config_key = Config.query.filter_by(key='gemini_api_key_2').first()
        api_key = config_key.value if config_key else os.environ.get('GEMINI_API_KEY_2')
        if not api_key:
            api_key = os.environ.get('GEMINI_API_KEY')
        
        count = 0
        students = Student.query.filter(Student.risk_score.in_(['Medium', 'High', 'Critical'])).all()
        
        if students and api_key:
            student_data = [{"id": s.id, "name": s.name, "risk": s.risk_score, "rate": round(s.predicted_attendance,1)} for s in students]
            prompt = f"Write a brief 1-sentence personalized encouraging recommendation for each of these at-risk students. Suggest mentoring, counselor referral, or extra classes based on risk. Data: {json.dumps(student_data)}. Return ONLY valid JSON: {{\"recommendations\": [{{\"id\": 1, \"text\": \"...\"}}]}}"
            
            try:
                res_text = get_cached_ai_response(prompt, api_key=api_key)
                json_str = res_text[res_text.find('{'):res_text.rfind('}')+1]
                rec_map = {item['id']: item['text'] for item in json.loads(json_str).get('recommendations', [])}
                
                for s in students:
                    if s.id in rec_map:
                        alert = Alert(student_id=s.id, message=rec_map[s.id], alert_type='recommendation')
                        db.session.add(alert)
                        count += 1
            except Exception as e:
                pass
                
        db.session.commit()
        return f"Generated {count} personalized recommendations."
    except Exception as e:
        db.session.rollback()
        return f"DB Error recommendations: {str(e)}"

def create_agent(llm):
    return Agent(
        role="Student Support Advisor",
        goal="For each at-risk student, generate a personalized recommendation and save as 'recommendation' Alert",
        backstory="A compassionate advisor using contextual data to help students succeed.",
        verbose=True,
        allow_delegation=False,
        tools=[provide_recommendations_tool],
        llm=llm
    )
