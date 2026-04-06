# Phase 1 Implementation Plan: Advanced AI-Driven Attendance System

## Objective

Upgrade the core data operation layers to support **Teacher** functionality, multiple subjects per day, and bulk CSV uploads, creating a reliable foundation for the AI agents.

## Checklist

### 1. Planning & Setup

- [x] Backup existing Firebase database.
- [x] Create restored safe state.
- [x] Create `seeddb.py` for demo purposes.
- [x] Create this `implementation_plan_phase1.md` tracking file.

### 2. Teacher Authentication & Access

- [ ] Register `teacher` Blueprint in Flask (`app/teacher/routes.py`).
- [ ] Update `/login` routing to route users with `role == 'teacher'` to `/teacher/dashboard`.
- [ ] Create basic `teacher/dashboard.html` template.
- [ ] Update `app/__init__.py` to register the new Blueprint.
- [ ] Add `teacher_required` decorator securing the routes.

### 3. Manual Attendance Flow (Teacher)

- [ ] Add `/teacher/attendance` route for selecting Class, Date, and Subject.
- [ ] Add Attendance marking UI with a roster of students.
- [ ] Write logic to push `Attendance` records to Firestore with validation (prevent duplicates for same session).

### 4. Bulk CSV Upload (Admin / Teacher)

- [ ] Create `/admin/upload-csv` route.
- [ ] Write CSV parsing, row validation (date, roll_number, subject, status).
- [ ] Write batch commit to Firestore.
- [ ] Create a downloadable error report for invalid rows.

### 5. Day-Wise Clubbing & UI Upgrade

- [ ] Refactor `student.dashboard` and `student.attendance` to group records by Date.
- [ ] Display subject chips (Present/Absent/Late) per day.
- [ ] Refactor `admin.student_detail` similarly.

### 6. AI Pipeline Reliability Tweaks

- [ ] Move Risk Scoring to a deterministic rule-based flow (Low/Medium/High/Critical based on predicted percentage) in `risk_scoring_agent.py` to prevent LLM hallucination on simple math.
