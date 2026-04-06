# app/admin/routes.py - Admin dashboard and management views
from flask import render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from app.admin import admin
from app.models import Student, Attendance, Alert, Report, Config
from app.extensions import db
from datetime import datetime
from functools import wraps, lru_cache
import threading
from io import BytesIO
from fpdf import FPDF


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("You do not have permission to access that page.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


@lru_cache(maxsize=128)
def get_cached_student(student_id):
    student_doc = db.collection("students").document(str(student_id)).get()
    return Student.from_dict(student_doc.to_dict()) if student_doc.exists else None


@admin.route("/dashboard")
@login_required
@admin_required
def dashboard():
    students_ref = db.collection("students").get()
    total_students = len(students_ref)

    low_risk = sum(1 for s in students_ref if s.to_dict().get("risk_score") == "Low")
    medium_risk = sum(
        1 for s in students_ref if s.to_dict().get("risk_score") == "Medium"
    )
    high_risk = sum(1 for s in students_ref if s.to_dict().get("risk_score") == "High")
    critical_risk = sum(
        1 for s in students_ref if s.to_dict().get("risk_score") == "Critical"
    )

    alerts_ref = (
        db.collection("alerts")
        .order_by("created_at", direction="DESCENDING")
        .limit(5)
        .get()
    )
    recent_alerts = []
    for doc in alerts_ref:
        alert = Alert.from_dict(doc.to_dict())
        alert.student = get_cached_student(alert.student_id)
        recent_alerts.append(alert)

    return render_template(
        "admin/dashboard.html",
        total_students=total_students,
        low_risk=low_risk,
        medium_risk=medium_risk,
        high_risk=high_risk,
        critical_risk=critical_risk,
        recent_alerts=recent_alerts,
    )


@admin.route("/students")
@login_required
@admin_required
def students():
    students_ref = db.collection("students").get()
    all_students = [Student.from_dict(s.to_dict()) for s in students_ref]
    return render_template("admin/students.html", students=all_students)


@admin.route("/students/<id>")
@login_required
@admin_required
def student_detail(id):
    student_doc = db.collection("students").document(str(id)).get()
    if not student_doc.exists:
        flash("Student not found.", "danger")
        return redirect(url_for("admin.students"))

    student = Student.from_dict(student_doc.to_dict())

    attendances_ref = (
        db.collection("attendances").where("student_id", "==", str(id)).get()
    )
    attendances = [Attendance.from_dict(doc.to_dict()) for doc in attendances_ref]
    attendances.sort(key=lambda x: str(x.date), reverse=True)

    alerts_ref = db.collection("alerts").where("student_id", "==", str(id)).get()
    alerts = [Alert.from_dict(doc.to_dict()) for doc in alerts_ref]
    alerts.sort(key=lambda x: str(x.created_at), reverse=True)

    return render_template(
        "admin/student_detail.html",
        student=student,
        attendances=attendances,
        alerts=alerts,
    )


@admin.route("/students/<id>/pdf")
@login_required
@admin_required
def student_pdf(id):
    student_doc = db.collection("students").document(str(id)).get()
    if not student_doc.exists:
        flash("Student not found.", "danger")
        return redirect(url_for("admin.students"))

    student = Student.from_dict(student_doc.to_dict())

    attendances_ref = (
        db.collection("attendances").where("student_id", "==", str(id)).get()
    )
    attendances = [Attendance.from_dict(doc.to_dict()) for doc in attendances_ref]
    attendances.sort(key=lambda x: str(x.date), reverse=True)

    alerts_ref = db.collection("alerts").where("student_id", "==", str(id)).get()
    all_alerts = [Alert.from_dict(doc.to_dict()) for doc in alerts_ref]
    recs = [a for a in all_alerts if a.alert_type == "recommendation"]

    pdf = FPDF()
    pdf.add_page()

    # Custom Brand Colors
    BRAND_R, BRAND_G, BRAND_B = 37, 99, 235  # Primary blue
    TEXT_R, TEXT_G, TEXT_B = 30, 41, 59  # Main text
    MUTED_R, MUTED_G, MUTED_B = 100, 116, 139  # Muted text

    # Header
    pdf.set_font("helvetica", "B", 24)
    pdf.set_text_color(BRAND_R, BRAND_G, BRAND_B)
    pdf.cell(0, 15, "AI Attendance Report", new_x="LMARGIN", new_y="NEXT", align="C")

    pdf.set_font("helvetica", "I", 10)
    pdf.set_text_color(MUTED_R, MUTED_G, MUTED_B)
    pdf.cell(
        0,
        5,
        f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        new_x="LMARGIN",
        new_y="NEXT",
        align="C",
    )

    pdf.ln(10)

    # Divider Log
    pdf.set_draw_color(226, 232, 240)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # Student Info Box
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(TEXT_R, TEXT_G, TEXT_B)
    pdf.cell(0, 10, "Student Profile", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("helvetica", "", 12)
    pdf.cell(50, 8, "Name:")
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, str(student.name), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("helvetica", "", 12)
    pdf.cell(50, 8, "Roll Number:")
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, str(student.roll_number), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("helvetica", "", 12)
    pdf.cell(50, 8, "Predicted Attendance:")
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(
        0, 8, f"{student.predicted_attendance:.1f}%", new_x="LMARGIN", new_y="NEXT"
    )

    pdf.set_font("helvetica", "", 12)
    pdf.cell(50, 8, "Risk Level:")
    pdf.set_font("helvetica", "B", 12)
    if student.risk_score.lower() in ["high", "critical"]:
        pdf.set_text_color(220, 38, 38)
    elif student.risk_score.lower() == "medium":
        pdf.set_text_color(217, 119, 6)
    else:
        pdf.set_text_color(22, 163, 74)
    pdf.cell(0, 8, str(student.risk_score), new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(TEXT_R, TEXT_G, TEXT_B)

    # Divider
    pdf.ln(5)
    pdf.set_draw_color(226, 232, 240)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # Recommendations
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "AI Recommendations", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    if recs:
        for r in recs:
            safe_msg = (
                str(r.message)
                .replace("\xa0", " ")
                .replace("•", "-")
                .replace("‘", "'")
                .replace("’", "'")
                .replace("“", '"')
                .replace("”", '"')
                .replace("—", "-")
            )
            safe_msg = safe_msg.encode("latin-1", "replace").decode("latin-1")
            pdf.set_x(10)
            pdf.multi_cell(0, 8, f"- {safe_msg}")
            pdf.ln(2)
    else:
        pdf.set_font("helvetica", "I", 11)
        pdf.set_text_color(MUTED_R, MUTED_G, MUTED_B)
        pdf.cell(
            0, 10, "No active recommendations available.", new_x="LMARGIN", new_y="NEXT"
        )

    # Divider
    pdf.set_text_color(TEXT_R, TEXT_G, TEXT_B)
    pdf.ln(5)
    pdf.set_draw_color(226, 232, 240)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # Recent Attendance Table
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Recent Attendance Log", new_x="LMARGIN", new_y="NEXT")

    # Table Header
    pdf.set_fill_color(241, 245, 249)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(50, 10, "Date", border=1, fill=True)
    pdf.cell(90, 10, "Subject", border=1, fill=True)
    pdf.cell(0, 10, "Status", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("helvetica", "", 11)
    for a in attendances[:10]:
        date_str = (
            a.date.strftime("%Y-%m-%d") if hasattr(a.date, "strftime") else str(a.date)
        )
        pdf.cell(50, 10, date_str, border=1)
        pdf.cell(90, 10, str(a.subject), border=1)

        status_text = str(a.status)
        if status_text.lower() == "present":
            pdf.set_text_color(22, 163, 74)
        else:
            pdf.set_text_color(220, 38, 38)

        pdf.cell(0, 10, status_text, border=1, new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(TEXT_R, TEXT_G, TEXT_B)

    pdf_bytes = bytes(pdf.output())
    buffer = BytesIO(pdf_bytes)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{student.roll_number}_report.pdf",
        mimetype="application/pdf",
    )


@admin.route("/alerts")
@login_required
@admin_required
def alerts():
    alerts_ref = (
        db.collection("alerts").order_by("created_at", direction="DESCENDING").get()
    )
    all_alerts = []
    for doc in alerts_ref:
        alert = Alert.from_dict(doc.to_dict())
        alert.student = get_cached_student(alert.student_id)
        all_alerts.append(alert)
    return render_template("admin/alerts.html", alerts=all_alerts)


@admin.route("/reports")
@login_required
@admin_required
def reports():
    reports_ref = (
        db.collection("reports").order_by("generated_at", direction="DESCENDING").get()
    )
    all_reports = [Report.from_dict(doc.to_dict()) for doc in reports_ref]
    return render_template("admin/reports.html", reports=all_reports)


@admin.route("/run-analysis", methods=["GET"])
@login_required
@admin_required
def run_analysis_view():
    return render_template("admin/run_analysis.html")


@admin.route("/run-analysis", methods=["POST"])
@login_required
@admin_required
def run_analysis_trigger():
    try:
        from crew.attendance_crew import run_attendance_analysis

        thread = threading.Thread(target=run_attendance_analysis)
        thread.start()
        flash(
            "Analysis strongly started in the background! It may take a few minutes. Check reports later.",
            "success",
        )
    except Exception as e:
        flash(f"Error running analysis: {e}", "danger")
    return redirect(url_for("admin.reports"))


@admin.route("/settings", methods=["GET", "POST"])
@login_required
@admin_required
def settings():
    import os

    # Use environment variable directly instead of DB config
    current_key = os.environ.get("GEMINI_API_KEY", "")

    if request.method == "POST":
        flash(
            "API Keys are now strictly managed via the .env file. Please edit your .env file to update keys.",
            "warning",
        )

    return render_template("admin/settings.html", current_key=current_key)
