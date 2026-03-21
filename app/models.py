# app/models.py - Defines database tables using SQLAlchemy ORM
from app.extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20))  # 'admin' or 'student'
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    roll_number = db.Column(db.String(20), unique=True)
    department = db.Column(db.String(50))
    semester = db.Column(db.Integer)
    email = db.Column(db.String(120))
    risk_score = db.Column(db.String(20), default='Low')
    predicted_attendance = db.Column(db.Float, default=0.0)
    attendances = db.relationship('Attendance', backref='student', lazy=True)
    alerts = db.relationship('Alert', backref='student', lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    subject = db.Column(db.String(50))
    date = db.Column(db.Date)
    status = db.Column(db.String(10))   # 'Present' or 'Absent'

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    message = db.Column(db.Text)
    alert_type = db.Column(db.String(30))  # 'risk', 'anomaly', 'recommendation'
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    content = db.Column(db.Text)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Config(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True)
    value = db.Column(db.Text)
