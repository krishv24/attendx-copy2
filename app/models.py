# app/models.py - Defines data structures for Firestore
from flask_login import UserMixin
from datetime import datetime


class User(UserMixin):
    def __init__(
        self,
        id,
        name,
        email,
        password_hash,
        role,
        student_id=None,
        assigned_department=None,
        assigned_semester=None,
    ):
        self.id = str(id)
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.student_id = str(student_id) if student_id else None
        self.assigned_department = assigned_department
        self.assigned_semester = assigned_semester

    @staticmethod
    def from_dict(data):
        if not data:
            return None
        return User(
            id=data.get("id"),
            name=data.get("name"),
            email=data.get("email"),
            password_hash=data.get("password_hash"),
            role=data.get("role"),
            student_id=data.get("student_id"),
            assigned_department=data.get("assigned_department"),
            assigned_semester=data.get("assigned_semester"),
        )


class Student:
    def __init__(
        self,
        id,
        name,
        roll_number,
        department,
        semester,
        email,
        risk_score="Low",
        predicted_attendance=0.0,
        **kwargs
    ):
        self.id = str(id)
        self.name = name
        self.roll_number = roll_number
        self.department = department
        self.semester = semester
        self.email = email
        self.risk_score = risk_score
        self.predicted_attendance = predicted_attendance

    @staticmethod
    def from_dict(data):
        if not data:
            return None
        return Student(**data)


class Attendance:
    def __init__(
        self, id, student_id, subject, date, status, recorded_by=None, **kwargs
    ):
        self.id = str(id)
        self.student_id = str(student_id)
        self.subject = subject
        self.date = (
            date
            if isinstance(date, datetime)
            else datetime.fromisoformat(str(date)) if date else None
        )
        self.status = status
        self.recorded_by = recorded_by

    @staticmethod
    def from_dict(data):
        if not data:
            return None
        return Attendance(**data)


class Alert:
    def __init__(
        self,
        id,
        student_id,
        message,
        alert_type,
        is_read=False,
        created_at=None,
        **kwargs
    ):
        self.id = str(id)
        self.student_id = str(student_id)
        self.message = message
        self.alert_type = alert_type
        self.is_read = is_read
        self.created_at = (
            created_at
            if isinstance(created_at, datetime)
            else (
                datetime.fromisoformat(str(created_at))
                if created_at
                else datetime.utcnow()
            )
        )

    @staticmethod
    def from_dict(data):
        if not data:
            return None
        return Alert(**data)


class Report:
    def __init__(self, id, title, content, generated_at=None, **kwargs):
        self.id = str(id)
        self.title = title
        self.content = content
        self.generated_at = (
            generated_at
            if isinstance(generated_at, datetime)
            else (
                datetime.fromisoformat(str(generated_at))
                if generated_at
                else datetime.utcnow()
            )
        )

    @staticmethod
    def from_dict(data):
        if not data:
            return None
        return Report(**data)


class Config:
    def __init__(self, key, value, **kwargs):
        self.key = key
        self.value = value

    @staticmethod
    def from_dict(data):
        if not data:
            return None
        return Config(**data)
