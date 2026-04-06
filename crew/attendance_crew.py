# crew/attendance_crew.py - Orchestrates the CrewAI process
from crewai import Crew, Process, Task, LLM
from app.extensions import db
import os
import time


def run_attendance_analysis():
    # Attempt to grab API key from environment
    api_key1 = os.environ.get("GEMINI_API_KEY")
    api_key2 = os.environ.get("GEMINI_API_KEY_2") or api_key1

    if not api_key1:
        raise ValueError(
            "No GEMINI_API_KEY environment variable found. Please set it in .env."
        )

    model_name = "gemini/gemini-2.5-flash-lite"
    os.environ["AI_MODEL_NAME"] = model_name

    llm1 = LLM(model=model_name, api_key=api_key1)
    llm2 = LLM(model=model_name, api_key=api_key2)

    from agents.data_ingestion_agent import create_agent as get_data
    from agents.pattern_detection_agent import create_agent as get_pattern
    from agents.prediction_agent import create_agent as get_pred
    from agents.risk_scoring_agent import create_agent as get_risk
    from agents.alert_agent import create_agent as get_alert
    from agents.recommendation_agent import create_agent as get_rec
    from agents.anomaly_detection_agent import create_agent as get_anom
    from agents.reporting_agent import create_agent as get_rep

    ag1 = get_data(llm1)
    ag2 = get_pattern(llm2)
    ag3 = get_pred(llm1)
    ag4 = get_risk(llm2)
    ag5 = get_alert(llm1)
    ag6 = get_rec(llm2)
    ag7 = get_anom(llm1)
    ag8 = get_rep(llm2)

    def task_callback(output):
        time.sleep(15)  # wait 15 seconds between agents
        return output

    # Creating Tasks
    t1 = Task(
        description="Fetch and compute attendance data using the provided tool.",
        expected_output="A structured summary of attendance records.",
        agent=ag1,
        callback=task_callback,
    )
    t2 = Task(
        description="Detect any patterns of repeated absences using the provided tool.",
        expected_output="A list of observed attendance patterns.",
        agent=ag2,
        callback=task_callback,
    )
    t3 = Task(
        description="Predict the next 30 days attendance and save to student database.",
        expected_output="Confirmation of updated predictions.",
        agent=ag3,
        callback=task_callback,
    )
    t4 = Task(
        description="Calculate risk scores based on predictions and update student records.",
        expected_output="Success message of risk score updates.",
        agent=ag4,
        callback=task_callback,
    )
    t5 = Task(
        description="Generate alerts for students at risk.",
        expected_output="Confirmation of alert generation.",
        agent=ag5,
        callback=task_callback,
    )
    t6 = Task(
        description="Provide personalized recommendations for at-risk students.",
        expected_output="Count of generated recommendations.",
        agent=ag6,
        callback=task_callback,
    )
    t7 = Task(
        description="Detect anomalies such as mass class absences.",
        expected_output="Anomaly report details.",
        agent=ag7,
        callback=task_callback,
    )
    t8 = Task(
        description="Compile the final executive report and store it in the Report table.",
        expected_output="Confirmation of Report creation.",
        agent=ag8,
        callback=task_callback,
    )

    crew = Crew(
        agents=[ag1, ag2, ag3, ag4, ag5, ag6, ag7, ag8],
        tasks=[t1, t2, t3, t4, t5, t6, t7, t8],
        process=Process.sequential,
        verbose=True,
    )

    return crew.kickoff()
