import os

from flask import Flask, render_template, request, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from extensions import mail

from datetime import datetime, timedelta

# ==========================================================
# EMAIL IMPORTS
# FILE: app.py
# ==========================================================

from flask_mail import Message
from extensions import mail

# ==========================================================
# PROJECT IMPORTS
# FILE: app.py
# ==========================================================

from student import student_bp
from admin import admin_bp

from models import (
    db,
    Student,
    Admin,
    LoginAttempt,
    Notes,
    LiveClass,
    Test,
    ActiveSession  # <-- Yeh yahan add karein
)

app = Flask(__name__)

# ==========================================================
# EMAIL CONFIGURATION (SECURED WITH ENV VARIABLES)
# FILE: app.py
# ==========================================================

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = "bikizzzclasses@gmail.com"
# ✅ Ab aapka password Render Environment se safe uthayega, GitHub par leak nahi hoga
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = "bikizzzclasses@gmail.com"
mail.init_app(app)


import secrets

# ✅ Stable Secret Key
app.secret_key = os.environ.get("SECRET_KEY", "biki_fallback_secret_key_2026")
# ==========================================================
# SECURITY CONFIGURATIONS (SESSION PROTECTION)
# ==========================================================


app.config["SESSION_COOKIE_SECURE"] = True  


app.config["SESSION_COOKIE_HTTPONLY"] = True  


app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  

app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=1)
app.config["MAX_LOGIN_ATTEMPTS"] = 5
app.config["LOCK_TIME"] = 10   # minutes

UPLOAD_FOLDER = "static/uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# ==========================================================
# FILE VALIDATION CONFIGURATION 
# ==========================================================
# Sirf in photo formats ko allow karenge
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ================= PROFILE PHOTO UPLOAD =================

@app.route("/upload-profile", methods=["POST"])
def upload_profile():

    if "student_id" not in session:
        return redirect("/login")

    # Check 1: Kya request mein file aayi hai?
    if "photo" not in request.files:
        flash("No file part found!")
        return redirect("/profile")

    file = request.files["photo"]

    if file and file.filename != "":
        
        # ✅ Check 2: Security Check - Kya file ek genuine photo hai?
        if not allowed_file(file.filename):
            flash("Khatra! Only images (png, jpg, jpeg, gif) are allowed!")
            return redirect("/profile")

        # Filename ko secure banayein (path traversal attack se bachne ke liye)
        filename = secure_filename(file.filename)

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        file.save(filepath)

        student = db.session.get(Student, session["student_id"])

        student.profile_image = filename

        db.session.commit()

        flash("Profile Photo Uploaded Successfully!")

    else:
        flash("Please select a file to upload.")

    return redirect("/profile")


# ================= DATABASE CONFIGURATION (UPDATED FOR POSTGRESQL) =================

# Render ke Postgres se connect karega, agar nahi mila toh local SQLite chalayega
db_uri = os.environ.get("DATABASE_URL")

if db_uri and db_uri.startswith("postgres://"):
    db_uri = db_uri.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_uri or "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Database initialize karein
db.init_app(app)

# --- GLOBAL SCOPE MEIN TABLES AUR DEFAULT ADMIN BANANE KA LOGIC ---
with app.app_context():
    db.create_all() 
    print("✅ Database tables checked/created in the current database")
    
    # Gunicorn startup par cloud database mein admin check aur create karega
    admin = Admin.query.filter_by(email="bikizzzclasses@gmail.com").first()
    if not admin:
        admin = Admin(
            name="BIKIzz Admin",
            email="bikizzzclasses@gmail.com",
            password=generate_password_hash("BIKI2488@")
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Default Admin Created Successfully on Cloud Database")
# -----------------------------------------------------------------

app.register_blueprint(student_bp)
app.register_blueprint(admin_bp)

# ================= HOME =================

@app.route("/about")
def about():
    return render_template("about.html")

# ================= PROFILE =================

@app.route("/profile")
def profile():

    if "student_id" not in session:
        return redirect("/login")

    student = db.session.get(Student, session["student_id"])

    return render_template("profile.html", student=student)


# ================= LOGOUT (UPDATED FOR 2-DEVICE LIMIT) =================

@app.route("/logout")
def logout():

    # Agar session mein token hai, toh database se delete karein
    if "session_token" in session:
        ActiveSession.query.filter_by(session_token=session["session_token"]).delete()
        db.session.commit()

    # Flask session clear karein
    session.clear()

    flash("Logged Out Successfully")

    return redirect("/login")


# ================= PAYMENT =================

@app.route("/payment", methods=["GET", "POST"])
def payment():

    if "student_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        # Check 1: Kya request mein file field maujood hai?
        if "payment" not in request.files:
            flash("No file part found!")
            return redirect("/payment")

        file = request.files["payment"]

        if file and file.filename != "":

            # ✅ Security Check: Kya file sirf ek image (png, jpg, jpeg) hai?
            if not allowed_file(file.filename):
                flash("Security Alert! Only images (png, jpg, jpeg, gif) are allowed as payment screenshots!")
                return redirect("/payment")

            # Filename ko secure banayein
            filename = secure_filename(file.filename)

            filepath = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            file.save(filepath)

            # SQLAlchemy ke naye standards ke mutabik db.session.get use karna zyada sahi hai
            student = db.session.get(Student, session["student_id"])

            student.payment_image = filename

            db.session.commit()

            flash("Payment Screenshot Uploaded Successfully!")

            return redirect("/dashboard")
        
        else:
            flash("Please select a file before clicking upload.")
            return redirect("/payment")

    return render_template("payment.html")
# ================= RUN =================

if __name__ == "__main__":
    # Local laptop par run karne ke liye ekdum clean run block
    app.run(host="0.0.0.0", port=5105, debug=True)