import os
import random 
import secrets  
import requests  # <-- BREVO API

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    flash,
    current_app
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename

from random import randint
# from flask_mail import Message 

from models import (
    db,
    Student,
    Notes,
    LiveClass,
    Notice,
    Test,
    PasswordResetOTP,
    ActiveSession  # <-- Yeh naya model humne yahan import kiya
)

student_bp = Blueprint("student", __name__)

# ==========================================================
# HOME PAGE
# FILE: student.py
# ==========================================================

@student_bp.route("/")
def home():
    return render_template("index.html")

# ==========================================================
# STUDENT REGISTER (UPDATED WITH DUPLICATE CHECK)
# FILE: student.py
# ==========================================================
@student_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        email = request.form["email"].strip().lower()

        existing_student = Student.query.filter_by(email=email).first()
        if existing_student:
            flash("Account already exists with this email!")
            return redirect("/register")

        student = Student(
            name=request.form["name"],
            mobile=request.form["mobile"],
            email=email,
            password=generate_password_hash(request.form["password"])
        )

        db.session.add(student)
        db.session.commit()

        flash("Registration Successful! Please Login.")
        return redirect("/login")

    return render_template("register.html")

# ==========================================================
# STUDENT LOGIN (WITH 2-DEVICE LIMIT)
# FILE: student.py
# ==========================================================

@student_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        student = Student.query.filter_by(email=email).first()

        if student and check_password_hash(student.password, password):

            # 1. Check karein ki is student ke pehle se kitne active devices/sessions hain
            active_devices_count = ActiveSession.query.filter_by(student_id=student.id).count()

            if active_devices_count >= 2:
                flash("Login Failed! Yeh account pehle se hi 2 devices par active hai. Kisi ek se logout kijiye.")
                return redirect("/login")

            # 2. Agar 2 se kam hain, toh ek secure unique session token banayein
            token = secrets.token_hex(16)

            new_session = ActiveSession(
                student_id=student.id,
                session_token=token
            )
            db.session.add(new_session)
            db.session.commit()

            # 3. Flask session mein details aur token save karein
            session["student_id"] = student.id
            session["student_name"] = student.name
            session["session_token"] = token  # Isse device track hoga logout ke waqt

            flash("Login Successful")

            return redirect("/dashboard")

        flash("Invalid Email or Password")

    return render_template("login.html")

# ==========================================================
# FORGOT PASSWORD (SAFE VERSION - NO HARDCODED KEY)
# FILE: student.py
# ==========================================================
@student_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":
        email = request.form["email"].strip().lower()
        student = Student.query.filter_by(email=email).first()

        if not student:
            flash("Email not found!")
            return redirect("/forgot-password")

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))

        # Delete old OTP
        PasswordResetOTP.query.filter_by(email=email).delete()

        # Save new OTP
        reset = PasswordResetOTP(
            email=email,
            otp=otp
        )

        db.session.add(reset)
        db.session.commit()

        # --- BREVO EMAIL API LOGIC WITH ENVIRONMENT VARIABLE ---
        url = "https://api.brevo.com/v3/smtp/email"
        
        headers = {
            # Yeh line ab Render ke environment se automatic key utha legi
            "api-key": os.environ.get("BREVO_API_KEY"), 
            "content-type": "application/json"
        }

        payload = {
            "sender": {
                "email": "bikizzzclasses@gmail.com",  # Jo email aapne Brevo par verify ki hai
                "name": "BIKIzz Classes"
            },
            "to": [{"email": email}],
            "subject": "BIKIzz Classes Password Reset OTP",
            "textContent": f"Hello {student.name},\n\nYour Password Reset OTP is: {otp}\n\nThis OTP is valid for 10 minutes.\n\nBIKIzz Classes"
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 201:
                session["reset_email"] = email
                flash("OTP Sent Successfully!")
                return redirect("/verify-otp")
            else:
                print("Brevo API Error:", response.text)
                flash("Email service currently unavailable.")
                return redirect("/forgot-password")
                
        except Exception as e:
            print("Connection Error:", str(e))
            flash("Something went wrong while sending email.")
            return redirect("/forgot-password")

    return render_template("forgot_password.html")
# ==========================================================
# VERIFY OTP
# FILE: student.py
# ==========================================================

@student_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():

    if "reset_email" not in session:
        return redirect("/forgot-password")

    if request.method == "POST":

        user_otp = request.form["otp"]

        reset = PasswordResetOTP.query.filter_by(
            email=session["reset_email"]
        ).first()

        # DEBUG
        print("Session Email:", session.get("reset_email"))
        print("DB OTP:", reset.otp if reset else "No OTP Found")
        print("User OTP:", user_otp)

        if not reset:

            flash("OTP Expired!")

            return redirect("/forgot-password")

        if reset.otp != user_otp:

            flash("Invalid OTP!")

            return redirect("/verify-otp")

        session["otp_verified"] = True

        flash("OTP Verified Successfully!")

        return redirect("/reset-password")

    return render_template("verify_otp.html")

# ==========================================================
# RESET PASSWORD
# FILE: student.py
# ==========================================================

@student_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():

    if "reset_email" not in session:
        return redirect("/forgot-password")

    if "otp_verified" not in session:
        return redirect("/verify-otp")

    if request.method == "POST":

        password = request.form["password"]
        confirm = request.form["confirm_password"]

        if password != confirm:

            flash("Passwords do not match!")

            return redirect("/reset-password")

        student = Student.query.filter_by(
            email=session["reset_email"]
        ).first()

        student.password = generate_password_hash(password)

        PasswordResetOTP.query.filter_by(
            email=session["reset_email"]
        ).delete()

        db.session.commit()

        session.pop("reset_email", None)
        session.pop("otp_verified", None)

        flash("Password Changed Successfully!")

        return redirect("/login")

    return render_template("reset_password.html")


# ==========================================================
# STUDENT DASHBOARD
# FILE: student.py
# ==========================================================

@student_bp.route("/dashboard")
def dashboard():

    if "student_id" not in session:
        return redirect("/login")

    student = db.session.get(Student, session["student_id"])

    if student is None:
        session.clear()
        flash("Please login again.")
        return redirect("/login")

    live = LiveClass.query.first()
    
    notes = Notes.query.order_by(Notes.id.desc()).all()

    notices = Notice.query.order_by(
        Notice.created_at.desc()
    ).limit(5).all()

    return render_template(
        "dashboard.html",
        student=student,
        name=student.name,
        status=student.payment_status,
        live=live,
        notes=notes,
        notices=notices
    )

# ==========================================================
# ALL STUDY NOTES VIEW (CRASH SAFE)
# FILE: student.py
# ==========================================================
@student_bp.route("/all-notes")
def all_notes():
    if "student_id" not in session:
        return redirect("/login")

    student = db.session.get(Student, session["student_id"])

    if student is None:
        session.clear()
        flash("Please login again.")
        return redirect("/login")

    try:
        notes = Notes.query.order_by(Notes.id.desc()).all()
    except Exception as e:
        notes = []

    return render_template(
        "all_notes.html",
        notes=notes,
        status=student.payment_status,
        name=student.name
    )

# ==========================================================
# STUDENT TEST
# FILE: student.py
# ==========================================================
@student_bp.route("/student-test")
def student_test():

    if "student_id" not in session:
        return redirect("/login")

    questions = Test.query.all()

    return render_template(
        "student_test.html",
        questions=questions
    )