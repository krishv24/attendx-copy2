# app/teacher/routes.py - Teacher specific views
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.teacher import teacher
from app.models import Student, Attendance
from app.extensions import db
from datetime import datetime
from functools import wraps
import csv
from io import StringIO
import uuid


def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if (
            hasattr(current_user, "is_authenticated")
            and not current_user.is_authenticated
        ):
            return redirect(url_for("auth.login"))
        if getattr(current_user, "role", "") != "teacher":
            flash("You do not have permission to access that page.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


@teacher.route("/dashboard")
@login_required
@teacher_required
def dashboard():
    return render_template("teacher/dashboard.html")


@teacher.route("/csv_upload", methods=["GET", "POST"])
@login_required
@teacher_required
def csv_upload():
    if request.method == "POST":
        if "csv_file" not in request.files:
            flash("No file part", "danger")
            return redirect(request.url)

        file = request.files["csv_file"]
        if file.filename == "":
            flash("No selected file", "danger")
            return redirect(request.url)

        subject = request.form.get("subject")
        date_input = request.form.get("date")

        if not subject or not date_input:
            flash("Please select date and subject", "danger")
            return redirect(request.url)

        try:
            target_date = datetime.strptime(date_input, "%Y-%m-%d")
            iso_date = datetime.combine(
                target_date.date(), datetime.min.time()
            ).isoformat()
        except ValueError:
            flash("Invalid date format", "danger")
            return redirect(request.url)

        if file and file.filename.endswith(".csv"):
            try:
                stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
                csv_reader = csv.reader(stream)
                header = next(csv_reader)

                # Check for roll_number column
                try:
                    roll_idx = next(
                        i for i, col in enumerate(header) if "roll" in col.lower()
                    )
                    status_idx = next(
                        i for i, col in enumerate(header) if "status" in col.lower()
                    )
                except StopIteration:
                    flash(
                        'CSV must contain "Roll Number" and "Status" columns.', "danger"
                    )
                    return redirect(request.url)

                # First fetch class students
                students_query = db.collection("students")
                if getattr(current_user, "assigned_department", None):
                    students_query = students_query.where(
                        "department", "==", current_user.assigned_department
                    )
                if getattr(current_user, "assigned_semester", None):
                    students_query = students_query.where(
                        "semester", "==", current_user.assigned_semester
                    )
                class_students = {
                    s.to_dict()["roll_number"]: s.to_dict()
                    for s in students_query.get()
                }

                batch = db.batch()
                batch_count = 0
                records_saved = 0

                for row in csv_reader:
                    if not row or len(row) <= max(roll_idx, status_idx):
                        continue
                    r_num = row[roll_idx].strip()
                    status = row[status_idx].strip().capitalize()

                    if status not in ["Present", "Absent", "Late"]:
                        continue

                    if r_num in class_students:
                        s_id = class_students[r_num]["id"]

                        # Validate existing
                        existing = (
                            db.collection("attendances")
                            .where("student_id", "==", s_id)
                            .where("subject", "==", subject)
                            .where("date", "==", iso_date)
                            .get()
                        )

                        if not existing:
                            att_id = str(uuid.uuid4())
                            doc_ref = db.collection("attendances").document(att_id)
                            batch.set(
                                doc_ref,
                                {
                                    "id": att_id,
                                    "student_id": s_id,
                                    "subject": subject,
                                    "date": iso_date,
                                    "status": status,
                                    "recorded_by": current_user.email,
                                },
                            )
                            records_saved += 1
                            batch_count += 1

                            if batch_count == 400:
                                batch.commit()
                                batch = db.batch()
                                batch_count = 0

                if batch_count > 0:
                    batch.commit()

                flash(
                    f"Successfully imported {records_saved} attendance records from CSV.",
                    "success",
                )
                return redirect(url_for("teacher.dashboard"))

            except Exception as e:
                flash(f"Error processing CSV: {str(e)}", "danger")
                return redirect(request.url)

    return render_template(
        "teacher/csv_upload.html", today=datetime.today().strftime("%Y-%m-%d")
    )


@teacher.route("/attendance", methods=["GET", "POST"])
@login_required
@teacher_required
def manual_attendance():
    # Fetch students mapped to teacher's department and semester
    students_query = db.collection("students")
    if getattr(current_user, "assigned_department", None):
        students_query = students_query.where(
            "department", "==", current_user.assigned_department
        )
    if getattr(current_user, "assigned_semester", None):
        students_query = students_query.where(
            "semester", "==", current_user.assigned_semester
        )

    students_ref = students_query.get()
    all_students = [Student.from_dict(s.to_dict()) for s in students_ref]
    all_students.sort(key=lambda s: s.roll_number)

    if request.method == "POST":
        date_input = request.form.get("date")
        subject = request.form.get("subject")

        if not date_input or not subject:
            flash("Please select date and subject", "danger")
            return redirect(url_for("teacher.manual_attendance"))

        try:
            target_date = datetime.strptime(date_input, "%Y-%m-%d")
        except ValueError:
            flash("Invalid date format", "danger")
            return redirect(url_for("teacher.manual_attendance"))

        batch = db.batch()
        batch_count = 0
        records_saved = 0

        for student in all_students:
            status = request.form.get(f"status_{student.id}")
            if status in ["Present", "Absent", "Late"]:
                # Check if it already exists for same student, subject, date
                iso_date = datetime.combine(
                    target_date.date(), datetime.min.time()
                ).isoformat()
                existing = (
                    db.collection("attendances")
                    .where("student_id", "==", str(student.id))
                    .where("subject", "==", subject)
                    .where("date", "==", iso_date)
                    .get()
                )

                if not existing:
                    att_id = str(uuid.uuid4())
                    doc_ref = db.collection("attendances").document(att_id)
                    batch.set(
                        doc_ref,
                        {
                            "id": att_id,
                            "student_id": str(student.id),
                            "subject": subject,
                            "date": iso_date,
                            "status": status,
                            "recorded_by": current_user.email,
                        },
                    )
                    records_saved += 1
                    batch_count += 1

                    if batch_count == 400:
                        batch.commit()
                        batch = db.batch()
                        batch_count = 0

        if batch_count > 0:
            batch.commit()

        if records_saved > 0:
            flash(
                f"Successfully recorded {records_saved} new attendance entries for {subject}.",
                "success",
            )
        else:
            flash(
                "No new records were saved (maybe attendance was already marked for this subject and date).",
                "warning",
            )

        return redirect(url_for("teacher.dashboard"))

    return render_template(
        "teacher/manual_attendance.html",
        students=all_students,
        today=datetime.today().strftime("%Y-%m-%d"),
    )
