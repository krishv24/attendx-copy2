# app/admin/routes.py - Admin dashboard and management views
from flask import render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from app.admin import admin
from app.models import Student, Attendance, Alert, Report, Config
from app.extensions import db
from datetime import datetime
from functools import wraps
from io import BytesIO
from fpdf import FPDF

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
    students_ref = db.collection('students').get()
    total_students = len(students_ref)
    
    low_risk = sum(1 for s in students_ref if s.to_dict().get('risk_score') == 'Low')
    medium_risk = sum(1 for s in students_ref if s.to_dict().get('risk_score') == 'Medium')
    high_risk = sum(1 for s in students_ref if s.to_dict().get('risk_score') == 'High')
    critical_risk = sum(1 for s in students_ref if s.to_dict().get('risk_score') == 'Critical')
    
    alerts_ref = db.collection('alerts').order_by('created_at', direction='DESCENDING').limit(5).get()
    recent_alerts = []
    for doc in alerts_ref:
        alert = Alert.from_dict(doc.to_dict())
        student_doc = db.collection('students').document(str(alert.student_id)).get()
        alert.student = Student.from_dict(student_doc.to_dict()) if student_doc.exists else None
        recent_alerts.append(alert)
    
    return render_template('admin/dashboard.html', 
                           total_students=total_students,
                           low_risk=low_risk, medium_risk=medium_risk,
                           high_risk=high_risk, critical_risk=critical_risk,
                           recent_alerts=recent_alerts)

@admin.route('/students')
@login_required
@admin_required
def students():
    students_ref = db.collection('students').get()
    all_students = [Student.from_dict(s.to_dict()) for s in students_ref]
    return render_template('admin/students.html', students=all_students)

@admin.route('/students/<id>')
@login_required
@admin_required
def student_detail(id):
    student_doc = db.collection('students').document(str(id)).get()
    if not student_doc.exists:
        flash('Student not found.', 'danger')
        return redirect(url_for('admin.students'))
        
    student = Student.from_dict(student_doc.to_dict())
    
    attendances_ref = db.collection('attendances').where('student_id', '==', str(id)).get()
    attendances = [Attendance.from_dict(doc.to_dict()) for doc in attendances_ref]
    attendances.sort(key=lambda x: str(x.date), reverse=True)
    
    alerts_ref = db.collection('alerts').where('student_id', '==', str(id)).get()
    alerts = [Alert.from_dict(doc.to_dict()) for doc in alerts_ref]
    alerts.sort(key=lambda x: str(x.created_at), reverse=True)
    
    return render_template('admin/student_detail.html', student=student, attendances=attendances, alerts=alerts)

@admin.route('/students/<id>/pdf')
@login_required
@admin_required
def student_pdf(id):
    student_doc = db.collection('students').document(str(id)).get()
    if not student_doc.exists:
        flash('Student not found.', 'danger')
        return redirect(url_for('admin.students'))
        
    student = Student.from_dict(student_doc.to_dict())
    
    attendances_ref = db.collection('attendances').where('student_id', '==', str(id)).get()
    attendances = [Attendance.from_dict(doc.to_dict()) for doc in attendances_ref]
    attendances.sort(key=lambda x: str(x.date), reverse=True)
    
    alerts_ref = db.collection('alerts').where('student_id', '==', str(id)).get()
    all_alerts = [Alert.from_dict(doc.to_dict()) for doc in alerts_ref]
    recs = [a for a in all_alerts if a.alert_type == 'recommendation']
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Student Attendance & Report", new_x="LMARGIN", new_y="NEXT", align="C")
    
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 10, f"Name: {student.name}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, f"Roll Number: {student.roll_number}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, f"Risk Score: {student.risk_score}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, f"Predicted Attendance: {student.predicted_attendance:.1f}%", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Recommendations", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    if recs:
        for r in recs:
            pdf.multi_cell(0, 8, f"- {r.message}")
    else:
        pdf.cell(0, 10, "No active recommendations.", new_x="LMARGIN", new_y="NEXT")
        
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Recent Attendance", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    for a in attendances[:10]:
        date_str = a.date.strftime("%Y-%m-%d") if hasattr(a.date, 'strftime') else str(a.date)
        pdf.cell(0, 8, f"{date_str} - {a.subject}: {a.status}", new_x="LMARGIN", new_y="NEXT")
    
    pdf_bytes = bytes(pdf.output())
    buffer = BytesIO(pdf_bytes)
    return send_file(buffer, as_attachment=True, download_name=f"{student.roll_number}_report.pdf", mimetype='application/pdf')

@admin.route('/alerts')
@login_required
@admin_required
def alerts():
    alerts_ref = db.collection('alerts').order_by('created_at', direction='DESCENDING').get()
    all_alerts = []
    for doc in alerts_ref:
        alert = Alert.from_dict(doc.to_dict())
        student_doc = db.collection('students').document(str(alert.student_id)).get()
        alert.student = Student.from_dict(student_doc.to_dict()) if student_doc.exists else None
        all_alerts.append(alert)
    return render_template('admin/alerts.html', alerts=all_alerts)

@admin.route('/reports')
@login_required
@admin_required
def reports():
    reports_ref = db.collection('reports').order_by('generated_at', direction='DESCENDING').get()
    all_reports = [Report.from_dict(doc.to_dict()) for doc in reports_ref]
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
    # Use config collection
    api_key_doc = db.collection('configs').document('gemini_api_key').get()
    current_key = api_key_doc.to_dict().get('value') if api_key_doc.exists else ''
    
    if request.method == 'POST':
        new_key = request.form.get('api_key')
        if new_key:
            try:
                db.collection('configs').document('gemini_api_key').set({
                    'key': 'gemini_api_key',
                    'value': new_key
                })
                flash('API Key updated successfully.', 'success')
                current_key = new_key
            except Exception as e:
                flash(f'Error updating API Key: {e}', 'danger')
        else:
            flash('Please enter a valid API Key.', 'danger')
            
    return render_template('admin/settings.html', current_key=current_key)
