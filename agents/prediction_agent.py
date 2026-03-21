# agents/prediction_agent.py - Predicts next 30 days attendance
from crewai import Agent
from crewai.tools import tool
from app.models import Attendance, Student
from app.extensions import db
import pandas as pd

@tool("Predict Attendance")
def predict_attendance_tool(input: str = "") -> str:
    """
    Predicts attendance directly from the database and updates Student records.
    Do NOT pass JSON or data into the input field. Keep the input empty.
    """
    try:
        attendances = Attendance.query.all()
        students = Student.query.all()
        if not attendances or not students:
            return "Not enough data for prediction."
            
        data = [{'student_id': a.student_id, 'date': a.date, 'status': a.status} for a in attendances]
        df = pd.DataFrame(data)
        
        from sklearn.linear_model import LinearRegression
        import numpy as np
        
        results = []
        for s in students:
            s_data = df[df['student_id'] == s.id].copy()
            if s_data.empty:
                continue
                
            s_data['day_index'] = (s_data['date'] - s_data['date'].min()).dt.days
            s_data['is_present'] = (s_data['status'] == 'Present').astype(int)
            
            if len(s_data) < 3:
                rate = s_data['is_present'].mean() * 100
                s.predicted_attendance = float(rate)
                results.append({"student_id": s.id, "predicted_attendance": float(rate)})
                continue
                
            X = s_data[['day_index']].values
            y = s_data['is_present'].values
            
            model = LinearRegression()
            model.fit(X, y)
            
            last_day = s_data['day_index'].max()
            future_X = np.array([[last_day + i] for i in range(1, 31)])
            predictions = model.predict(future_X)
            
            predictions = np.clip(predictions, 0, 1)
            rate = float(predictions.mean() * 100)
            
            s.predicted_attendance = rate
            results.append({"student_id": s.id, "predicted_attendance": rate})
            
        db.session.commit()
        return f"Predictions updated successfully for {len(results)} students."
    except Exception as e:
        db.session.rollback()
        return f"Database error during prediction: {str(e)}"

def create_agent(llm):
    return Agent(
        role="Attendance Prediction Specialist",
        goal="Predict each student's attendance percentage for the next 30 days using past trends",
        backstory="A predictive modeling expert leveraging machine learning to gauge future student attendance.",
        verbose=True,
        allow_delegation=False,
        tools=[predict_attendance_tool],
        llm=llm
    )
