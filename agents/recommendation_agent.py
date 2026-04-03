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
        from app.extensions import db
        from app.ai_cache import get_cached_ai_response
        import os
        import json
        import uuid
        from datetime import datetime
        
        config_doc = db.collection('configs').document('gemini_api_key_2').get()
        api_key = config_doc.to_dict().get('value') if config_doc.exists else os.environ.get('GEMINI_API_KEY_2')
        if not api_key:
            api_key = os.environ.get('GEMINI_API_KEY')
        
        count = 0
        students_query = db.collection('students').where('risk_score', 'in', ['Medium', 'High', 'Critical']).get()
        
        if students_query and api_key:
            student_data = [{"id": s.to_dict().get('id'), "name": s.to_dict().get('name'), "risk": s.to_dict().get('risk_score'), "rate": round(s.to_dict().get('predicted_attendance',0),1)} for s in students_query]
            prompt = f"Write a brief 1-sentence personalized encouraging recommendation for each of these at-risk students. Suggest mentoring, counselor referral, or extra classes based on risk. Data: {json.dumps(student_data)}. Return ONLY valid JSON: {{\"recommendations\": [{{\"id\": \"1\", \"text\": \"...\"}}]}}"
            
            try:
                res_text = get_cached_ai_response(prompt, api_key=api_key)
                json_str = res_text[res_text.find('{'):res_text.rfind('}')+1]
                rec_map = {str(item['id']): item['text'] for item in json.loads(json_str).get('recommendations', [])}
                
                for s_doc in students_query:
                    s_id = str(s_doc.to_dict().get('id'))
                    if s_id in rec_map:
                        alert_id = str(uuid.uuid4())
                        db.collection('alerts').document(alert_id).set({
                            'id': alert_id,
                            'student_id': s_id,
                            'message': rec_map[s_id],
                            'alert_type': 'recommendation',
                            'is_read': False,
                            'created_at': datetime.utcnow().isoformat()
                        })
                        count += 1
            except Exception as e:
                pass
                
        return f"Generated {count} personalized recommendations."
    except Exception as e:
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
