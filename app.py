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
# EMAIL CONFIGURATION
# FILE: app.py
# ==========================================================

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = "bikizzzclasses@gmail.com"
app.config["MAIL_PASSWORD"] = "izyvhkuoakvckqtn"
app.config["MAIL_DEFAULT_SENDER"] = "bikizzzclasses@gmail.com"
mail.init_app(app)


import secrets

app.secret_key = secrets.token_hex(32)

app.config["MAX_LOGIN_ATTEMPTS"] = 5
app.config["LOCK_TIME"] = 10   # minutes

UPLOAD_FOLDER = "static/uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# ================= PROFILE PHOTO UPLOAD =================

@app.route("/upload-profile", methods=["POST"])
def upload_profile():

    if "student_id" not in session:
        return redirect("/login")

    file = request.files["photo"]

    if file and file.filename != "":

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

# --- GLOBAL SCOPE MEIN TABLES BANANE KA LOGIC ---
with app.app_context():
    db.create_all() 
    print("✅ Database tables checked/created in the current database")
# -------------------------------------------------

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

        file = request.files["payment"]

        if file and file.filename != "":

            filename = secure_filename(file.filename)

            filepath = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            file.save(filepath)

            student = Student.query.get(session["student_id"])

            student.payment_image = filename

            db.session.commit()

            flash("Payment Screenshot Uploaded Successfully!")

            return redirect("/dashboard")

    return render_template("payment.html")

# ================= RUN =================

if __name__ == "__main__":

    with app.app_context():

        db.create_all()

        # Create Default Admin (Only First Time)
        admin = Admin.query.filter_by(
            email="bikizzzclasses@gmail.com"
        ).first()

        if not admin:

            admin = Admin(
                name="BIKIzz Admin",
                email="bikizzzclasses@gmail.com",
                password=generate_password_hash("BIKI2488@")
            )

            db.session.add(admin)
            db.session.commit()

            print("✅ Default Admin Created")

    app.run(host="0.0.0.0", port=5105, debug=True)