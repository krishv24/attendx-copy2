# app/admin/routes.py - Admin dashboard and management views
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.admin import admin
from app.models import Student, Attendance, Alert, Report, Config
from app.extensions import db
from datetime import datetime
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You do not have permission to access that page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_students = Student.query.count()
    low_risk = Student.query.filter_by(risk_score='Low').count()
    medium_risk = Student.query.filter_by(risk_score='Medium').count()
    high_risk = Student.query.filter_by(risk_score='High').count()
    critical_risk = Student.query.filter_by(risk_score='Critical').count()
    
    recent_alerts = Alert.query.order_by(Alert.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                           total_students=total_students,
                           low_risk=low_risk, medium_risk=medium_risk,
                           high_risk=high_risk, critical_risk=critical_risk,
                           recent_alerts=recent_alerts)

@admin.route('/students')
@login_required
@admin_required
def students():
    all_students = Student.query.all()
    return render_template('admin/students.html', students=all_students)

@admin.route('/students/<int:id>')
@login_required
@admin_required
def student_detail(id):
    student = Student.query.get_or_404(id)
    attendances = Attendance.query.filter_by(student_id=id).all()
    alerts = Alert.query.filter_by(student_id=id).all()
    return render_template('admin/student_detail.html', student=student, attendances=attendances, alerts=alerts)

@admin.route('/alerts')
@login_required
@admin_required
def alerts():
    all_alerts = Alert.query.order_by(Alert.created_at.desc()).all()
    return render_template('admin/alerts.html', alerts=all_alerts)

@admin.route('/reports')
@login_required
@admin_required
def reports():
    all_reports = Report.query.order_by(Report.generated_at.desc()).all()
    return render_template('admin/reports.html', reports=all_reports)

@admin.route('/run-analysis', methods=['GET'])
@login_required
@admin_required
def run_analysis_view():
    return render_template('admin/run_analysis.html')

@admin.route('/run-analysis', methods=['POST'])
@login_required
@admin_required
def run_analysis_trigger():
    try:
        from crew.attendance_crew import run_attendance_analysis
        run_attendance_analysis()
        flash('Analysis finished successfully!', 'success')
    except Exception as e:
        flash(f'Error running analysis: {e}', 'danger')
    return redirect(url_for('admin.reports'))

@admin.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    api_key_config = Config.query.filter_by(key='gemini_api_key').first()
    if request.method == 'POST':
        new_key = request.form.get('api_key')
        if new_key:
            if api_key_config:
                api_key_config.value = new_key
            else:
                api_key_config = Config(key='gemini_api_key', value=new_key)
                db.session.add(api_key_config)
            
            try:
                db.session.commit()
                flash('API Key updated successfully.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating API Key: {e}', 'danger')
        else:
            flash('Please enter a valid API Key.', 'danger')
            
    return render_template('admin/settings.html', current_key=api_key_config.value if api_key_config else '')
