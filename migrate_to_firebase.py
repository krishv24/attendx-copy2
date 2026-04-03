import os
from flask import Flask
from app.extensions import db
from app.models import User, Student, Attendance, Alert, Report, Config
import firebase_admin
from firebase_admin import credentials, firestore

def migrate():
    from config import Config as AppConfig
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = AppConfig.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    print("Initializing Firebase...")
    cred = credentials.Certificate('firebase-credentials.json')
    firebase_admin.initialize_app(cred)
    fdb = firestore.client()
    
    with app.app_context():
        print("Migrating Config...")
        configs = Config.query.all()
        for c in configs:
            fdb.collection('configs').document(c.key).set({
                'key': c.key,
                'value': c.value
            })
            
        print("Migrating Students...")
        students = Student.query.all()
        for s in students:
            fdb.collection('students').document(str(s.id)).set({
                'id': s.id,
                'name': s.name,
                'roll_number': s.roll_number,
                'department': s.department,
                'semester': s.semester,
                'email': s.email,
                'risk_score': s.risk_score,
                'predicted_attendance': s.predicted_attendance
            })
            
        print("Migrating Users...")
        users = User.query.all()
        for u in users:
            fdb.collection('users').document(str(u.id)).set({
                'id': u.id,
                'name': u.name,
                'email': u.email,
                'password_hash': u.password_hash,
                'role': u.role,
                'student_id': u.student_id
            })
            
        print("Migrating Attendances...")
        attendances = Attendance.query.all()
        for a in attendances:
            fdb.collection('attendances').document(str(a.id)).set({
                'id': a.id,
                'student_id': a.student_id,
                'subject': a.subject,
                'date': a.date.isoformat() if a.date else None,
                'status': a.status
            })
            
        print("Migrating Alerts...")
        alerts = Alert.query.all()
        for a in alerts:
            fdb.collection('alerts').document(str(a.id)).set({
                'id': a.id,
                'student_id': a.student_id,
                'message': a.message,
                'alert_type': a.alert_type,
                'is_read': a.is_read,
                'created_at': a.created_at.isoformat() if a.created_at else None
            })
            
        print("Migrating Reports...")
        reports = Report.query.all()
        for r in reports:
            fdb.collection('reports').document(str(r.id)).set({
                'id': r.id,
                'title': r.title,
                'content': r.content,
                'generated_at': r.generated_at.isoformat() if r.generated_at else None
            })
            
        print("Migration complete!")

if __name__ == '__main__':
    migrate()
