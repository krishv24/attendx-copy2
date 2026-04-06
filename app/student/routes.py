# app/student/routes.py - Student specific views
from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.student import student
from app.models import Student, Attendance, Alert, Report
from app.extensions import db
from functools import wraps


def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "student":
            flash("You do not have permission to access that page.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


@student.route("/dashboard")
@login_required
@student_required
def dashboard():
    student_doc = db.collection("students").document(str(current_user.student_id)).get()
    if not student_doc.exists:
        flash("Student record not found.", "danger")
        return redirect(url_for("auth.login"))

    student_record = Student.from_dict(student_doc.to_dict())

    # Workaround: fetch all for the student and sort in Python to avoid Firebase index error
    attendance_docs = (
        db.collection("attendances")
        .where("student_id", "==", str(student_record.id))
        .get()
    )
    all_attendances_dict = [doc.to_dict() for doc in attendance_docs]
    all_attendances_dict.sort(key=lambda x: x.get("date", ""), reverse=True)
    recent_attendances = [Attendance.from_dict(d) for d in all_attendances_dict[:5]]

    # Fetch all, sort and filter in python to avoid complex index requirements on free tier:
    alerts_all = (
        db.collection("alerts").where("student_id", "==", str(student_record.id)).get()
    )
    alerts_list = [
        Alert.from_dict(doc.to_dict())
        for doc in alerts_all
        if doc.to_dict().get("alert_type") != "recommendation"
    ]
    alerts_list.sort(key=lambda x: x.created_at, reverse=True)
    recent_alerts = alerts_list[:5]

    return render_template(
        "student/dashboard.html",
        student=student_record,
        attendances=recent_attendances,
        alerts=recent_alerts,
    )


@student.route("/attendance")
@login_required
@student_required
def attendance():
    doc = db.collection("students").document(str(current_user.student_id)).get()
    student_record = Student.from_dict(doc.to_dict())

    attendance_docs = (
        db.collection("attendances")
        .where("student_id", "==", str(student_record.id))
        .get()
    )
    all_attendances_dict = [d.to_dict() for d in attendance_docs]
    all_attendances_dict.sort(key=lambda x: x.get("date", ""), reverse=True)
    attendances = [Attendance.from_dict(d) for d in all_attendances_dict]

    return render_template(
        "student/attendance.html", student=student_record, attendances=attendances
    )


@student.route("/alerts")
@login_required
@student_required
def alerts():
    doc = db.collection("students").document(str(current_user.student_id)).get()
    student_record = Student.from_dict(doc.to_dict())

    alerts_all = (
        db.collection("alerts").where("student_id", "==", str(student_record.id)).get()
    )
    all_alerts = [
        Alert.from_dict(doc.to_dict())
        for doc in alerts_all
        if doc.to_dict().get("alert_type") != "recommendation"
    ]
    all_alerts.sort(key=lambda x: x.created_at, reverse=True)

    return render_template("student/alerts.html", alerts=all_alerts)


@student.route("/recommendations")
@login_required
@student_required
def recommendations():
    doc = db.collection("students").document(str(current_user.student_id)).get()
    student_record = Student.from_dict(doc.to_dict())

    recs_all = (
        db.collection("alerts")
        .where("student_id", "==", str(student_record.id))
        .where("alert_type", "==", "recommendation")
        .get()
    )
    all_recs = [Alert.from_dict(doc.to_dict()) for doc in recs_all]
    all_recs.sort(key=lambda x: x.created_at, reverse=True)

    return render_template("student/recommendations.html", recommendations=all_recs)
