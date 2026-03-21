# AI-Powered Student Attendance Management System

## Project Overview
This project is an AI-based Student Attendance Management System built with Python, Flask, and MySQL. It incorporates state-of-the-art AI agents (powered by CrewAI and Google Gemini) to automatically analyze student attendance logs, detect hidden absence patterns, evaluate risk levels, predict future attendance, issue early warning alerts, and generate personalized recommendations.

## Tech Stack
* **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Migrate
* **Database:** MySQL
* **AI & Machine Learning:** CrewAI, LangChain, Google Gemini API, Pandas
* **Frontend:** Plain HTML, CSS, Vanilla JavaScript (Jinja2 Templates)
* **Auth System:** Flask-Login with Role-Based Access (Admin/Student)

## File Structure & Responsibilities

### 1. The Core Infrastructure
* **`run.py` & `start.bat`**: The entry points of your application. Running these starts the Flask server.
* **`config.py`**: Handles configuration logic and loads environment variables (like the Database URL and Secrets) from your `.env` file.
* **`app/__init__.py`**: Contains the App Factory logic (`create_app()`). It bootstraps the Flask application, database configurations, login manager, and registers all the sub-routes (Blueprints). It also enforces the "Setup API Key" check on the first visit.
* **`app/models.py`**: Your MySQL Database schema definitions via SQLAlchemy. It includes models for `User`, `Student`, `Attendance`, `Alert`, `Report`, and `Config`.
* **`app/extensions.py`**: Bootstraps external extensions like `db` (SQLAlchemy), `migrate` (Flask-Migrate), and `login_manager` (Flask-Login).
* **`seed.py`**: A utility script run once at setup to populate the database with a default Admin account (`admin@school.com`) and mock student attendance data.

### 2. Routes (The Application Logic)
The application is split into three main "Blueprints" to keep code organized:
* **`app/auth/routes.py`**: Manages the `/login`, `/logout`, and `/setup-key` endpoints. It handles password verification, creating the initial Gemini API Key if missing, and redirecting users to their respective dashboards.
* **`app/admin/routes.py`**: Contains all endpoints prefixed with `/admin`. Admins can view the system-wide dashboard, browse the total student base, view generated AI reports, monitor alerts, and importantly—trigger the CrewAI analysis process via `POST /run-analysis`.
* **`app/student/routes.py`**: Contains endpoints meant exclusively for students (`/student`). Students can log in to view only their own attendance percentage, their personal alerts, and customized AI recommendations. 

### 3. Crew AI & AI Agents (`agents/` & `crew/`)
This is the core "AI Intelligence" module. 
* **`crew/attendance_crew.py`**: Acts as the master orchestrator. When the Admin clicks "Start Analysis", this file assembles the 8 Agents below, links them with Google Gemini (`gemini-1.5-flash`), assigns them their tasks in sequential order, and executes them. Because running 8 AI tasks takes a couple of minutes, the frontend displays a loading spinner dynamically during this.

**The 8 Agents:**
1. **`data_ingestion_agent.py`**: Reads MySQL and calculates the absolute attendance percentage for every student.
2. **`pattern_detection_agent.py`**: Looks at the last 10 days of attendance to spot consecutive absences and negative trends.
3. **`prediction_agent.py`**: Extrapolates current data trends to formally predict what the student's attendance will look like 30 days from now. Updates the `predicted_attendance` field in MySQL.
4. **`risk_scoring_agent.py`**: Evaluates the math models from Agent 3 to formally assign a Risk Tag: Low, Medium, High, or Critical, writing it back to the database.
5. **`alert_agent.py`**: Creates "Warning" alerts inside the `Alert` database table for anyone at High/Critical risk.
6. **`recommendation_agent.py`**: Passes the data strictly to the Google Gemini LLM to write out a personalized, warm recommendation advising the student on how to improve (like tutoring or counseling).
7. **`anomaly_detection_agent.py`**: Checks if over 40% of the class was randomly absent on a specific date, flagging dates of mass anomalies (like unofficial holidays). 
8. **`reporting_agent.py`**: Compiles all findings from the database into a human-readable master `Report` and saves it.

### 4. Frontend & Views (`templates/` & `static/`)
* **`templates/base.html`**: The unified layout featuring your navigation bar, message flashing (popup alerts), and HTML headers.
* **`templates/admin/` & `templates/student/`**: Subfolders containing individualized dashboard logic for each role.
* **`static/css/style.css`**: The central design token file controlling custom colors, buttons, grid metrics, and visual components. Completely vanilla CSS.
* **`static/js/run_analysis.js`**: Replaces the "Start Analysis" button with an animated spinner to show the Crew is "thinking" without freezing the browser page.

---

## How it All Runs Together
1. You run `start.bat`. Flask launches locally on port `5000`.
2. A visitor reaches `http://127.0.0.1:5000`. The App checks the Database for a `gemini_api_key`. If none is found, it forces the user to the `/setup-key` page. 
3. After the key is provided safely, users hit `/login`. 
4. Upon authentication, Flask checks their `role` and routes them to either `/admin/dashboard` or `/student/dashboard`.
5. When the Admin executes an analysis, Flask communicates with `CrewAI`. CrewAI initiates the Python Agents and begins sequentially pulling data out of the MySQL database using backend `tools`. Each Agent passes its output to the next, progressively mutating database records (like bumping risk scores and generating alerts).
6. When students log in, they query those updated database strings seamlessly.


ADMIN:
admin@school.com
with admin123!


STUDENT:
Student: alice@school.com

Password: student123 (Alice represents a high-performing student with very few absences.)

Student: bob@school.com

Password: student123 (Bob represents a critical-risk struggling student with massive absences and AI alerts.)
