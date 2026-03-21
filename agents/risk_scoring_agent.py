# agents/risk_scoring_agent.py - Assigns risk scores
from crewai import Agent
from crewai.tools import tool
from app.models import Student
from app.extensions import db

@tool("Assign Risk Scores")
def assign_risk_scores_tool(input: str = "") -> str:
    """
    Assigns risk scores using actual database metrics.
    Do NOT pass JSON into the input argument. Keep it empty.
    """
    try:
        from app.ai_cache import get_cached_ai_response
        from app.models import Config
        import os
        import json
        config_key = Config.query.filter_by(key='gemini_api_key_2').first()
        api_key = config_key.value if config_key else os.environ.get('GEMINI_API_KEY_2')
        if not api_key:
            # fallback to key 1
            api_key = os.environ.get('GEMINI_API_KEY')
        
        students = Student.query.all()
        results = []
        
        if students and api_key:
            student_data = [{"id": s.id, "rate": round(s.predicted_attendance, 1)} for s in students]
            prompt = f"Assign risk scores for these students based on typical academic attendance standards. Below 65 is Critical, 65-74 is High, 75-84 is Medium, 85+ is Low. Data: {json.dumps(student_data)}. Respond ONLY with valid JSON mapping student id to 'Low', 'Medium', 'High', or 'Critical': {{\"results\": [{{\"id\": 1, \"score\": \"Low\"}}]}}"
            
            try:
                res_text = get_cached_ai_response(prompt, api_key=api_key)
                # simple parsing attempt
                import re
                json_str = res_text[res_text.find('{'):res_text.rfind('}')+1]
                scores_map = {item['id']: item['score'] for item in json.loads(json_str).get('results', [])}
            except Exception as e:
                scores_map = {}
                
            for s in students:
                s.risk_score = scores_map.get(s.id, 'Medium')
                results.append(f"Student {s.id}: Risk {s.risk_score}")
            
        db.session.commit()
        return "\n".join(results)
    except Exception as e:
        db.session.rollback()
        return f"Error updating risks: {str(e)}"

def create_agent(llm):
    return Agent(
        role="Student Risk Evaluator",
        goal="Assign each student a risk level: Low (above 85%), Medium (75–85%), High (65–75%), Critical (below 65%) and write this back to the Student table",
        backstory="Evaluates student performance to identify at-risk individuals.",
        verbose=True,
        allow_delegation=False,
        tools=[assign_risk_scores_tool],
        llm=llm
    )
