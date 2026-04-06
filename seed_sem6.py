#!/usr/bin/env python3
"""seed_sem6.py - Clear Firestore and seed Sem 6 attendance demo data."""
from datetime import date, timedelta, datetime
import random
import uuid

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db

TOTAL_STUDENTS = 40
SUBJECTS = ["NLP", "SPCC", "AI"]
DAYS = 10


def delete_collection(collection_name, batch_size=400):
    while True:
        docs = db.collection(collection_name).limit(batch_size).get()
        if not docs:
            break
        batch = db.batch()
        for doc in docs:
            batch.delete(doc.reference)
        batch.commit()


def seed_database():
    app = create_app()
    with app.app_context():
        print("Clearing Firestore collections...")
        for name in [
            "attendances",
            "alerts",
            "reports",
            "students",
            "users",
            "configs",
        ]:
            delete_collection(name)

        print("Creating admin user...")
        admin_id = str(uuid.uuid4())
        db.collection("users").document(admin_id).set(
            {
                "id": admin_id,
                "name": "Admin User",
                "email": "admin@school.com",
                "password_hash": generate_password_hash("admin123"),
                "role": "admin",
                "student_id": None,
            }
        )

        print("Creating students...")
        students = []

        # Required students
        students.append(
            {
                "name": "Alice Student",
                "email": "alice@school.com",
                "roll_number": "CS6-001",
                "attendance_rate": 0.97,
            }
        )
        students.append(
            {
                "name": "Bob Student",
                "email": "bob@school.com",
                "roll_number": "CS6-002",
                "attendance_rate": 0.50,
            }
        )

        # Generate remaining students
        for i in range(3, TOTAL_STUDENTS + 1):
            students.append(
                {
                    "name": f"Student {i}",
                    "email": f"student{i:02d}@school.com",
                    "roll_number": f"CS6-{i:03d}",
                    "attendance_rate": None,
                }
            )

        # Assign attendance rates to remaining students to cover all risk tiers
        low_group = 10
        med_group = 10
        high_group = 10
        crit_group = TOTAL_STUDENTS - 2 - low_group - med_group - high_group

        rate_pool = []
        rate_pool += [random.uniform(0.92, 0.98) for _ in range(low_group)]
        rate_pool += [random.uniform(0.80, 0.88) for _ in range(med_group)]
        rate_pool += [random.uniform(0.65, 0.74) for _ in range(high_group)]
        rate_pool += [random.uniform(0.40, 0.55) for _ in range(crit_group)]
        random.shuffle(rate_pool)

        for s in students[2:]:
            s["attendance_rate"] = rate_pool.pop()

        # Create student + user docs
        student_records = []
        for s in students:
            student_id = str(uuid.uuid4())
            user_id = str(uuid.uuid4())

            predicted = round(s["attendance_rate"] * 100, 1)
            if predicted >= 90:
                risk = "Low"
            elif predicted >= 75:
                risk = "Medium"
            elif predicted >= 60:
                risk = "High"
            else:
                risk = "Critical"

            db.collection("students").document(student_id).set(
                {
                    "id": student_id,
                    "name": s["name"],
                    "roll_number": s["roll_number"],
                    "department": "Computer Science",
                    "semester": 6,
                    "email": s["email"],
                    "risk_score": risk,
                    "predicted_attendance": predicted,
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

            student_records.append(
                {
                    "student_id": student_id,
                    "email": s["email"],
                    "attendance_rate": s["attendance_rate"],
                }
            )

        # Create attendance sessions for 10 days, 3 subjects each
        start_date = date.today() - timedelta(days=DAYS - 1)
        sessions = []
        for day_offset in range(DAYS):
            d = start_date + timedelta(days=day_offset)
            for subject in SUBJECTS:
                sessions.append((d, subject))

        total_sessions = len(sessions)
        mass_absence_idx = 4 * len(SUBJECTS) + 1  # Day 5, subject "SPCC"

        print("Generating attendance records...")
        batch = db.batch()
        batch_count = 0
        total_records = 0

        # Choose > 40% of students for mass absence day (skip Alice for 95% goal)
        eligible_for_mass = [
            s for s in student_records if s["email"] != "alice@school.com"
        ]
        mass_absence_ids = {
            s["student_id"] for s in random.sample(eligible_for_mass, 20)
        }

        for s in student_records:
            target_absences = round((1.0 - s["attendance_rate"]) * total_sessions)
            target_absences = max(0, min(target_absences, total_sessions))

            absent_indices = set(random.sample(range(total_sessions), target_absences))

            # Enforce mass-absence session for selected students without changing counts
            if s["student_id"] in mass_absence_ids:
                if mass_absence_idx not in absent_indices:
                    # Replace a different absence to keep count stable
                    removable = [i for i in absent_indices if i != mass_absence_idx]
                    if removable:
                        absent_indices.remove(removable[0])
                    absent_indices.add(mass_absence_idx)

            for idx, (session_date, subject) in enumerate(sessions):
                status = "Absent" if idx in absent_indices else "Present"
                att_id = str(uuid.uuid4())
                batch.set(
                    db.collection("attendances").document(att_id),
                    {
                        "id": att_id,
                        "student_id": s["student_id"],
                        "subject": subject,
                        "date": datetime.combine(
                            session_date, datetime.min.time()
                        ).isoformat(),
                        "status": status,
                    },
                )

                batch_count += 1
                total_records += 1
                if batch_count >= 400:
                    batch.commit()
                    batch = db.batch()
                    batch_count = 0

        if batch_count > 0:
            batch.commit()

        print(
            f"Seeded {len(student_records)} students and {total_records} attendance records."
        )
        print("Login credentials:")
        print("- Admin: admin@school.com / admin123")
        print("- Student: alice@school.com / student123 (>=95% attendance)")
        print("- Student: bob@school.com / student123 (~50% attendance)")


if __name__ == "__main__":
    seed_database()
