#!/usr/bin/env python3
"""seeddb_massive.py - Generates robust synthetic demo data."""
import uuid
import random
from datetime import date, timedelta, datetime
from werkzeug.security import generate_password_hash
from google.cloud.firestore_v1.base_collection import _auto_id

from app import create_app
from app.extensions import db


def seed_database():
    app = create_app()
    with app.app_context():
        print("Starting massive database seed for Demo...")

        # 1. Create Admin
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

        # 2. Create Teacher mapped to specific class
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
                    "assigned_department": "Computer Science",
                    "assigned_semester": 5,
                }
            )
            print(f"Created Teacher mapped to CS Sem 5: {teacher_email}")

        print("Generating Students...")
        demo_students = []
        cs_first_names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
        for i, name in enumerate(cs_first_names, start=1):
            beh = random.choice(["good", "average", "poor"])
            if beh == "good":
                risk, pred = "Low", random.uniform(85, 100)
            elif beh == "average":
                risk, pred = "Medium", random.uniform(75, 84)
            else:
                risk, pred = random.choice(["High", "Critical"]), random.uniform(50, 74)

            demo_students.append(
                {
                    "name": f"{name} Smith",
                    "roll": f"CS0{i:02d}",
                    "email": f"{name.lower()}@school.com",
                    "risk": risk,
                    "pred": pred,
                    "behavior": beh,
                    "dept": "Computer Science",
                    "sem": 5,
                }
            )

        it_names = ["Zack", "Wendy", "Victor"]
        for i, name in enumerate(it_names, start=1):
            demo_students.append(
                {
                    "name": f"{name} Johnson",
                    "roll": f"IT0{i:02d}",
                    "email": f"{name.lower()}@school.com",
                    "risk": "Low",
                    "pred": 90.0,
                    "behavior": "good",
                    "dept": "Information Technology",
                    "sem": 3,
                }
            )

        student_docs = []
        for s in demo_students:
            existing = db.collection("users").where("email", "==", s["email"]).get()
            if existing:
                student_id = existing[0].to_dict().get("student_id")
                if student_id:
                    student_docs.append(
                        (student_id, s["behavior"], s["dept"], s["sem"])
                    )
                continue

            student_id = str(uuid.uuid4())
            user_id = str(uuid.uuid4())

            db.collection("students").document(student_id).set(
                {
                    "id": student_id,
                    "name": s["name"],
                    "roll_number": s["roll"],
                    "department": s["dept"],
                    "semester": s["sem"],
                    "email": s["email"],
                    "risk_score": s["risk"],
                    "predicted_attendance": s["pred"],
                }
            )
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
            student_docs.append((student_id, s["behavior"], s["dept"], s["sem"]))

        print(f"Created {len(student_docs)} students.")

        subjects = ["Mathematics", "Physics", "Computer Science"]
        start_date = date.today() - timedelta(days=60)

        print("Generating robust 60-day attendance history...")
        batch = db.batch()
        batch_count = 0
        total_created = 0

        for i in range(60):
            d = start_date + timedelta(days=i)
            if d.weekday() >= 5:
                continue

            for student_id, behavior, dept, sem in student_docs:
                for subject in subjects:
                    is_anomaly_day = i == 45
                    chance = random.random()
                    if is_anomaly_day and chance > 0.15:
                        status = "Absent"
                    else:
                        if behavior == "good":
                            status = "Present" if chance > 0.05 else "Absent"
                        elif behavior == "poor":
                            status = "Present" if chance > 0.60 else "Absent"
                        else:
                            status = "Present" if chance > 0.20 else "Absent"

                    att_id = str(uuid.uuid4())
                    batch.set(
                        db.collection("attendances").document(att_id),
                        {
                            "id": att_id,
                            "student_id": student_id,
                            "subject": subject,
                            "date": datetime.combine(
                                d, datetime.min.time()
                            ).isoformat(),
                            "status": status,
                            "recorded_by": "system",
                        },
                    )

                    batch_count += 1
                    total_created += 1
                    if batch_count >= 400:
                        batch.commit()
                        batch = db.batch()
                        batch_count = 0
        if batch_count > 0:
            batch.commit()
        print(
            f"Successfully generated {total_created} synthetic attendance records spanning 60 days."
        )


if __name__ == "__main__":
    seed_database()
