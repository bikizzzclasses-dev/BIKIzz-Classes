# ==========================================================
# FILE: admin.py (FIXED FOR STUDENT DELETION & SESSIONS)
# AUTHOR: BIKIzz' Classes Setup
# ==========================================================
import os
import secrets
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
    EnrollmentBanner,
    Test,
    ActiveSession  
)
from email_utils import send_resend_email

admin_bp = Blueprint("admin", __name__)

ALLOWED_PDF_MIMES = {"application/pdf"}
MAIN_ADMIN_EMAIL = "bikizzzclasses@gmail.com"


def secure_pdf_upload(file):
    filename = secure_filename(file.filename)
    if not filename.lower().endswith(".pdf") or file.mimetype not in ALLOWED_PDF_MIMES:
        return None
    unique_name = f"{secrets.token_hex(8)}_{filename}"
    return unique_name


def is_main_admin():
    return session.get("admin_email") == MAIN_ADMIN_EMAIL


def send_payment_approval_email(student):
    send_resend_email(
        student.email,
        "Payment Approved - BIKIzz Classes",
        (
            f"Hello {student.name},\n\n"
            "Your payment has been approved successfully.\n\n"
            "You can now access your premium study materials, live class details, tests, and dashboard features.\n\n"
            "BIKIzz Classes"
        ),
        (
            f"<p>Hello {student.name},</p>"
            "<p>Your payment has been <strong>approved successfully</strong>.</p>"
            "<p>You can now access your premium study materials, live class details, tests, and dashboard features.</p>"
            "<p>BIKIzz Classes</p>"
        ),
    )


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
            session["admin_email"] = admin.email
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
    session.pop("admin_email", None)
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
        total_notices=total_notices,
        is_main_admin=is_main_admin()
    )


@admin_bp.route("/admin/enrollment-banner", methods=["GET", "POST"])
def enrollment_banner_settings():
    if "admin" not in session:
        return redirect("/admin-login")

    if not is_main_admin():
        flash("Only main admin can control enrollment banner.")
        return redirect("/admin")

    banner = EnrollmentBanner.query.get(1)
    if not banner:
        banner = EnrollmentBanner(id=1)
        db.session.add(banner)
        db.session.commit()

    if request.method == "POST":
        action = request.form.get("action", "save")

        if action == "delete":
            banner.is_active = False
            flash("Enrollment banner hidden successfully.")
        else:
            banner.message = request.form.get("message", "").strip()
            banner.button_text = request.form.get("button_text", "").strip()
            banner.button_link = request.form.get("button_link", "").strip()
            banner.is_active = request.form.get("is_active") == "on"

            if not banner.message:
                banner.message = "Admission Open for HSLC 2027 Mathematics Crash Course"
            if not banner.button_text:
                banner.button_text = "Enroll Now"
            if not banner.button_link:
                banner.button_link = "/register"

            flash("Enrollment banner updated successfully.")

        db.session.commit()
        return redirect("/admin/enrollment-banner")

    return render_template("admin_enrollment_banner.html", banner=banner)


# ==========================================================
# STUDENT MANAGEMENT (FIXED CASCASED DELETE COMMAND)
# ==========================================================
@admin_bp.route("/students")
def students():
    if "admin" not in session:
        return redirect("/admin-login")

    students = Student.query.all()
    return render_template("students.html", students=students)


@admin_bp.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    if "admin" not in session:
        return redirect("/admin-login")

    try:
        # 1. 🔥 Sabse pehle ActiveSession table se student ka record delete karo varna constraint block karega
        ActiveSession.query.filter_by(student_id=id).delete()
        db.session.commit()

        # 2. Ab main Student row ko safely delete karo
        student = Student.query.get_or_404(id)
        db.session.delete(student)
        db.session.commit()
        flash("Student aur uske active sessions successfully delete ho gaye hain! 🎉")
        
    except Exception as e:
        db.session.rollback()
        print(f"🚨 DATABASE ERROR DURING DELETE: {str(e)}")
        flash(f"Delete karne mein dikkat aayi: {str(e)}")

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


@admin_bp.route("/approve/<int:id>", methods=["POST"])
def approve(id):
    if "admin" not in session:
        return redirect("/admin-login")

    student = Student.query.get_or_404(id)
    student.payment_status = "Approved"
    db.session.commit()

    send_payment_approval_email(student)

    flash("Payment Approved Successfully!")
    return redirect("/payments")


@admin_bp.route("/reject/<int:id>", methods=["POST"])
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
            filename = secure_pdf_upload(file)
            if not filename:
                flash("Only PDF files are allowed.")
                return redirect("/upload-notes")
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

            filename = secure_pdf_upload(file)
            if not filename:
                flash("Only PDF files are allowed.")
                return redirect("/upload-notes")
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

    notices = Notice.query.order_by(Notice.id.desc()).all()

    return render_template("admin_notices.html", notices=notices)


@admin_bp.route("/admin/notices/delete/<int:notice_id>", methods=["POST"])
def delete_notice(notice_id):
    if "admin" not in session:
        return redirect("/admin-login")

    notice = db.session.get(Notice, notice_id)
    if notice:
        db.session.delete(notice)
        db.session.commit()
        flash("Notice Deleted Successfully!")
    else:
        flash("Notice not found!")

    return redirect("/admin/notices")


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
