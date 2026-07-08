# ==========================================================
# FILE: admin.py
# AUTHOR: BIKIzz' Classes Setup
# ==========================================================
import os
from datetime import datetime, timedelta
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    flash,
    current_app
)
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash

# DATABASE MODELS IMPORT
from models import (
    db,
    Student,
    Admin,
    LoginAttempt,
    Notes,
    LiveClass,
    Notice,
    Test
)

admin_bp = Blueprint("admin", __name__)


# ==========================================================
# ADMIN LOGIN & SECURITY
# ==========================================================
@admin_bp.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        attempt = LoginAttempt.query.filter_by(email=email).first()

        if attempt and attempt.locked_until:
            if attempt.locked_until > datetime.now():
                flash("❌ Account is temporarily locked. Try again later.")
                return redirect("/admin-login")

        admin = Admin.query.filter_by(email=email).first()

        if admin and check_password_hash(admin.password, password):
            if attempt:
                attempt.attempts = 0
                attempt.locked_until = None
                db.session.commit()

            session["admin"] = True
            session["admin_name"] = admin.name
            flash("Admin Login Successful")
            return redirect("/admin")

        if not attempt:
            attempt = LoginAttempt(email=email, attempts=1)
            db.session.add(attempt)
        else:
            attempt.attempts += 1
            if attempt.attempts >= 5:
                attempt.locked_until = datetime.now() + timedelta(minutes=10)

        db.session.commit()
        flash("Invalid Admin Email or Password")

    return render_template("admin_login.html")


@admin_bp.route("/admin-logout")
def admin_logout():
    session.pop("admin", None)
    session.pop("admin_name", None)
    flash("Admin Logged Out Successfully")
    return redirect("/admin-login")


# ==========================================================
# ADMIN CORE DASHBOARD
# ==========================================================
@admin_bp.route("/admin")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin-login")

    students = Student.query.all()
    total_students = Student.query.count()
    approved_students = Student.query.filter_by(payment_status="Approved").count()
    pending_students = Student.query.filter_by(payment_status="Pending").count()
    rejected_students = Student.query.filter_by(payment_status="Rejected").count()
    total_notes = Notes.query.count()
    total_tests = Test.query.count()
    total_notices = Notice.query.count()

    return render_template(
        "admin.html",
        students=students,
        total_students=total_students,
        approved_students=approved_students,
        pending_students=pending_students,
        rejected_students=rejected_students,
        total_notes=total_notes,
        total_tests=total_tests,
        total_notices=total_notices
    )


# ==========================================================
# STUDENT MANAGEMENT
# ==========================================================
@admin_bp.route("/students")
def students():
    if "admin" not in session:
        return redirect("/admin-login")

    students = Student.query.all()
    return render_template("students.html", students=students)


@admin_bp.route("/delete/<int:id>")
def delete(id):
    if "admin" not in session:
        return redirect("/admin-login")

    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash("Student Deleted Successfully!")
    return redirect("/students")


# ==========================================================
# PAYMENT MANAGEMENT
# ==========================================================
@admin_bp.route("/payments")
def payments():
    if "admin" not in session:
        return redirect("/admin-login")

    students = Student.query.all()
    return render_template("payments.html", students=students)


@admin_bp.route("/approve/<int:id>")
def approve(id):
    if "admin" not in session:
        return redirect("/admin-login")

    student = Student.query.get_or_404(id)
    student.payment_status = "Approved"
    db.session.commit()
    flash("Payment Approved Successfully!")
    return redirect("/payments")


@admin_bp.route("/reject/<int:id>")
def reject(id):
    if "admin" not in session:
        return redirect("/admin-login")

    student = Student.query.get_or_404(id)
    student.payment_status = "Rejected"
    db.session.commit()
    flash("Payment Rejected!")
    return redirect("/payments")


# ==========================================================
# STUDY NOTES CONTROLLER (GET, POST, EDIT, DELETE)
# ==========================================================
@admin_bp.route("/upload-notes", methods=["GET", "POST"])
def upload_notes():
    if "admin" not in session:
        return redirect("/admin-login")

    if request.method == "POST":
        subject = request.form["subject"]
        chapter = request.form["chapter"]
        upload_date = request.form["upload_date"]
        file = request.files["pdf"]

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))

            note = Notes(
                subject=subject,
                chapter=chapter,
                pdf_file=filename,
                upload_date=upload_date
            )
            db.session.add(note)
            db.session.commit()
            flash("Notes Uploaded Successfully!")
            return redirect("/upload-notes")

    notes = Notes.query.order_by(Notes.id.desc()).all()
    return render_template("upload_notes.html", notes=notes)


@admin_bp.route("/admin/notes/delete/<int:note_id>", methods=["POST"])
def delete_note(note_id):
    if "admin" not in session:
        return redirect("/admin-login")

    note = db.session.get(Notes, note_id)
    if note:
        try:
            file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], note.pdf_file)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print("File system removal error:", e)

        db.session.delete(note)
        db.session.commit()
        flash("Notes Deleted Successfully!")
    
    return redirect("/upload-notes")


@admin_bp.route("/admin/notes/edit/<int:note_id>", methods=["POST"])
def edit_note(note_id):
    if "admin" not in session:
        return redirect("/admin-login")

    note = db.session.get(Notes, note_id)
    if not note:
        flash("Note nahi mila!")
        return redirect("/upload-notes")

    note.subject = request.form["subject"]
    note.chapter = request.form["chapter"]
    note.upload_date = request.form["upload_date"]

    if "pdf" in request.files:
        file = request.files["pdf"]
        if file and file.filename != "":
            try:
                old_path = os.path.join(current_app.config["UPLOAD_FOLDER"], note.pdf_file)
                if os.path.exists(old_path):
                    os.remove(old_path)
            except Exception as e:
                print("Purani file hatane me error:", e)

            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
            note.pdf_file = filename

    db.session.commit()
    flash("Notes Updated Successfully!")
    return redirect("/upload-notes")


# ==========================================================
# LIVE CLASS CONTROL
# ==========================================================
@admin_bp.route("/live-class", methods=["GET", "POST"])
def live_class():
    if "admin" not in session:
        return redirect("/admin-login")

    live = LiveClass.query.first()

    if request.method == "POST":
        link = request.form["meet_link"]
        date = request.form["class_date"]
        time = request.form["class_time"]

        if live:
            live.meet_link = link
            live.class_date = date
            live.class_time = time
        else:
            live = LiveClass(meet_link=link, class_date=date, class_time=time)
            db.session.add(live)

        db.session.commit()
        flash("Live Class Updated Successfully!")
        return redirect("/live-class")

    return render_template("live_class.html", live=live)


# ==========================================================
# NOTICE DESK CONTROL
# ==========================================================
@admin_bp.route("/manage-notice", methods=["GET", "POST"])
@admin_bp.route("/admin/notices", methods=["GET", "POST"])
def manage_notices():
    if "admin" not in session:
        return redirect("/admin-login")

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description") or request.form.get("message")

        notice = Notice(title=title, description=description)
        db.session.add(notice)
        db.session.commit()

        flash("Notice Added Successfully!")
        
        if request.path == "/manage-notice":
            return redirect("/manage-notice")
        return redirect("/admin/notices")

    try:
        notices = Notice.query.order_by(Notice.created_at.desc()).all()
    except:
        notices = Notice.query.all()

    return render_template("admin_notices.html", notices=notices)


# ==========================================================
# TEST SYSTEM DESK
# ==========================================================
@admin_bp.route("/manage-test", methods=["GET", "POST"])
def manage_test():
    if "admin" not in session:
        return redirect("/admin-login")

    if request.method == "POST":
        question = Test(
            question=request.form["question"],
            option1=request.form["option1"],
            option2=request.form["option2"],
            option3=request.form["option3"],
            option4=request.form["option4"],
            answer=request.form["answer"]
        )
        db.session.add(question)
        db.session.commit()
        flash("Question Added Successfully!")
        return redirect("/manage-test")

    questions = Test.query.all()
    return render_template("manage_test.html", questions=questions)