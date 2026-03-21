# app/student/routes.py - Student specific views
from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.student import student
from app.models import Student, Attendance, Alert, Report
from functools import wraps

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('You do not have permission to access that page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@student.route('/dashboard')
@login_required
@student_required
def dashboard():
    student_record = Student.query.get(current_user.student_id)
    if not student_record:
        flash('Student record not found.', 'danger')
        return redirect(url_for('auth.login'))
        
    recent_attendances = Attendance.query.filter_by(student_id=student_record.id).order_by(Attendance.date.desc()).limit(5).all()
    recent_alerts = Alert.query.filter_by(student_id=student_record.id).filter(Alert.alert_type != 'recommendation').order_by(Alert.created_at.desc()).limit(5).all()
    
    return render_template('student/dashboard.html', 
                           student=student_record,
                           attendances=recent_attendances,
                           alerts=recent_alerts)

@student.route('/attendance')
@login_required
@student_required
def attendance():
    student_record = Student.query.get(current_user.student_id)
    attendances = Attendance.query.filter_by(student_id=student_record.id).order_by(Attendance.date.desc()).all()
    return render_template('student/attendance.html', student=student_record, attendances=attendances)

@student.route('/alerts')
@login_required
@student_required
def alerts():
    student_record = Student.query.get(current_user.student_id)
    all_alerts = Alert.query.filter_by(student_id=student_record.id).filter(Alert.alert_type != 'recommendation').order_by(Alert.created_at.desc()).all()
    return render_template('student/alerts.html', alerts=all_alerts)

@student.route('/recommendations')
@login_required
@student_required
def recommendations():
    student_record = Student.query.get(current_user.student_id)
    all_recs = Alert.query.filter_by(student_id=student_record.id, alert_type='recommendation').order_by(Alert.created_at.desc()).all()
    return render_template('student/recommendations.html', recommendations=all_recs)
