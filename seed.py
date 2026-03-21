# seed.py - Seeds the database with initial admin and sample students
from app import create_app
from app.extensions import db
from app.models import User, Student, Attendance
from werkzeug.security import generate_password_hash
from datetime import date, timedelta
import random

app = create_app()

def seed_data():
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(email='admin@school.com').first()
        if not admin:
            admin = User(
                name='Admin User',
                email='admin@school.com',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            print("Admin user created (admin@school.com / admin123)")

        # Generate some mock student data
        if Student.query.count() == 0:
            student1 = Student(name='Alice Smith', roll_number='CS001', department='Computer Science', semester=5, email='alice@school.com', risk_score='Low', predicted_attendance=90.0)
            student2 = Student(name='Bob Jones', roll_number='CS002', department='Computer Science', semester=5, email='bob@school.com', risk_score='High', predicted_attendance=70.0)
            db.session.add_all([student1, student2])
            db.session.commit()
            
            # Create user accounts for students
            user_alice = User(name='Alice Smith', email='alice@school.com', password_hash=generate_password_hash('student123'), role='student', student_id=student1.id)
            user_bob = User(name='Bob Jones', email='bob@school.com', password_hash=generate_password_hash('student123'), role='student', student_id=student2.id)
            db.session.add_all([user_alice, user_bob])

            # Generate some mock attendances
            subjects = ['Math', 'Physics', 'Computer Science']
            start_date = date.today() - timedelta(days=30)
            for i in range(30):
                d = start_date + timedelta(days=i)
                # Skip weekends
                if d.weekday() >= 5:
                    continue
                # Alice is mostly present
                sub = subjects[i % 3]
                status_a = 'Present' if random.random() > 0.1 else 'Absent'
                a1 = Attendance(student_id=student1.id, subject=sub, date=d, status=status_a)
                db.session.add(a1)
                
                # Bob is frequently absent
                status_b = 'Present' if random.random() > 0.4 else 'Absent'
                a2 = Attendance(student_id=student2.id, subject=sub, date=d, status=status_b)
                db.session.add(a2)
            
            print("Mock student data created.")

        db.session.commit()
        print("Database seeded successfully.")

if __name__ == '__main__':
    seed_data()
