#!/usr/bin/env python3
"""seeddb.py - Generates default user, student, and attendance data for demo purposes.
Updates the database explicitly using Firebase Firestore to align with the current DB schema.
"""

import uuid
import random
from datetime import date, timedelta, datetime
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db


def seed_database():
    app = create_app()
    with app.app_context():
        print("Starting database seed for Demo...")

        # 1. Create Admin & Teacher
        admin_email = "admin@school.com"
        admin_query = db.collection("users").where("email", "==", admin_email).get()
        if not admin_query:
            admin_id = str(uuid.uuid4())
            db.collection("users").document(admin_id).set(
                {
                    "id": admin_id,
                    "name": "Admin User",
                    "email": admin_email,
                    "password_hash": generate_password_hash("admin123!"),
                    "role": "admin",
                    "student_id": None,
                }
            )
            print(f"Created Admin: {admin_email}")

        teacher_email = "teacher@school.com"
        teacher_query = db.collection("users").where("email", "==", teacher_email).get()
        if not teacher_query:
            teacher_id = str(uuid.uuid4())
            db.collection("users").document(teacher_id).set(
                {
                    "id": teacher_id,
                    "name": "Prof. Smith",
                    "email": teacher_email,
                    "password_hash": generate_password_hash("teacher123!"),
                    "role": "teacher",
                    "student_id": None,
                }
            )
            print(f"Created Teacher: {teacher_email}")

        # 2. Create Students & Student Users
        demo_students = [
            {
                "name": "Alice Smith",
                "roll": "CS001",
                "email": "alice@school.com",
                "risk": "Low",
                "pred": 95.0,
                "behavior": "good",
            },
            {
                "name": "Bob Jones",
                "roll": "CS002",
                "email": "bob@school.com",
                "risk": "Critical",
                "pred": 45.0,
                "behavior": "poor",
            },
            {
                "name": "Charlie Davis",
                "roll": "CS003",
                "email": "charlie@school.com",
                "risk": "Medium",
                "pred": 80.0,
                "behavior": "average",
            },
        ]

        student_docs = []
        for s in demo_students:
            # check if exists
            existing = db.collection("users").where("email", "==", s["email"]).get()
            if existing:
                student_docs.append(
                    (existing[0].to_dict()["student_id"], s["behavior"])
                )
                continue

            student_id = str(uuid.uuid4())
            user_id = str(uuid.uuid4())

            # Student Record
            db.collection("students").document(student_id).set(
                {
                    "id": student_id,
                    "name": s["name"],
                    "roll_number": s["roll"],
                    "department": "Computer Science",
                    "semester": 5,
                    "email": s["email"],
                    "risk_score": s["risk"],
                    "predicted_attendance": s["pred"],
                }
            )

            # User Record
            db.collection("users").document(user_id).set(
                {
                    "id": user_id,
                    "name": s["name"],
                    "email": s["email"],
                    "password_hash": generate_password_hash("student123"),
                    "role": "student",
                    "student_id": student_id,
                }
            )

            student_docs.append((student_id, s["behavior"]))
            print(f"Created Student: {s['email']}")

        # 3. Generate Attendances (30 days back)
        subjects = ["Mathematics", "Physics", "Computer Science"]
        start_date = date.today() - timedelta(days=30)

        print("Generating attendance records...")
        batch = db.batch()
        batch_count = 0

        for i in range(30):
            d = start_date + timedelta(days=i)
            if d.weekday() >= 5:  # Skip weekends
                continue

            for student_id, behavior in student_docs:
                for subject in subjects:
                    # Determine presence based on assigned behavior
                    chance = random.random()
                    if behavior == "good":
                        status = "Present" if chance > 0.05 else "Absent"
                    elif behavior == "poor":
                        status = "Present" if chance > 0.55 else "Absent"
                    else:
                        status = "Present" if chance > 0.20 else "Absent"

                    att_id = str(uuid.uuid4())
                    doc_ref = db.collection("attendances").document(att_id)
                    batch.set(
                        doc_ref,
                        {
                            "id": att_id,
                            "student_id": student_id,
                            "subject": subject,
                            "date": datetime.combine(
                                d, datetime.min.time()
                            ).isoformat(),
                            "status": status,
                        },
                    )

                    batch_count += 1
                    if batch_count == 400:
                        batch.commit()
                        batch = db.batch()
                        batch_count = 0

        if batch_count > 0:
            batch.commit()

        print("Successfully generated mock attendance records.")


if __name__ == "__main__":
    seed_database()
