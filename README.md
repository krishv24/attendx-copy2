# AI-Powered Student Attendance Management System

## 🎓 Academic Details
- **Course:** Natural Language Processing (NLP)
- **Class:** Semester VI (Third Year Engineering)
- **College:** Pillai College of Engineering, You can learn more about the college by visiting the official website of Pillai College of Engineering. https://www.pce.ac.in/

## 📌 Overview
An AI-based Student Attendance Management System built with Python, Flask, and Firebase. It incorporates state-of-the-art AI agents (powered by CrewAI and Google Gemini) to automatically analyze student attendance logs, detect hidden absence patterns, evaluate risk levels, predict future attendance, issue early warning alerts, and generate personalized recommendations.

## 🎯 Objective
To solve the problem of manual attendance tracking and reactive student intervention. By utilizing NLP and autonomous AI agents, the system moves beyond just counting absences; it proactively detects at-risk students, predicts future attendance patterns, and provides personalized, automated recommendations for struggling students before they fall behind.

## 🧠 Technologies Used
- **Backend:** Python, Flask
- **Database:** Firebase Firestore (NoSQL)
- **AI & Machine Learning:** CrewAI, LangChain, Google Gemini API, Pandas, Scikit-learn
- **Frontend:** HTML5, Vanilla CSS, Jinja2 Templates
- **Production Server:** Gunicorn

## 📊 Dataset
- The project is initially seeded with locally generated mock attendance datasets covering various student profiles (e.g., highly consistent students, consistently absent students, and conditionally absent students) to train and demonstrate the AI analysis and prediction capabilities.

## ⚙️ Installation
Steps to run the project locally:

```bash
git clone https://github.com/krishv24/NLP-rewritten.git
cd NLP-rewritten
pip install -r requirements.txt
```

> **Note:** You will need to add a `firebase-credentials.json` file in the root directory and provide your Google Gemini API key during the initial setup to talk to the AI services.

## ▶️ Usage
How to run the project.

```bash
# Wait for the environment to build, then run the app:
python run.py

# Alternatively, run the batch script (Windows)
./start.bat
```
Navigate to `http://127.0.0.1:5000` in your web browser. 

* **Admin Access:** `admin@school.com` / `admin123!`
* **Student Access:** `alice@school.com` / `student123`

## 📈 Results
- **Accuracy / outputs:** The predictive AI successfully maps non-linear absence patterns and flags anomalies. The system automatically categorizes students into Low, Medium, High, or Critical risk tiers with respective predictive attendance accuracies logged in the Admin dashboard.
- Features dynamic, downloadable PDF reporting for automated tracking.

## 🎥 Demo Video
[Insert YouTube link here]

*(Note: Detailed system architecture and infrastructure documentation has been moved to `documentation.md`)*
