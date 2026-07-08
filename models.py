from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


db = SQLAlchemy()

# ==========================================================
# STUDENT MODEL
# ==========================================================

class Student(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    mobile = db.Column(db.String(15), unique=True, nullable=False)

    email = db.Column(db.String(100), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)

    payment_image = db.Column(db.String(200))

    payment_status = db.Column(db.String(20), default="Pending")

    profile_image = db.Column(
        db.String(200),
        default="default.png"
    )

    # ==========================================================
# PASSWORD RESET OTP MODEL
# FILE: models.py
# ==========================================================

class PasswordResetOTP(db.Model):

    __tablename__ = "password_reset_otp"

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(120), nullable=False)

    otp = db.Column(db.String(6), nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # ==========================================================
# ADMIN MODEL
# FILE: models.py
# ==========================================================

class Admin(db.Model):

    __tablename__ = "admin"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(100), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)

    # ==========================================================
# LIVE CLASS MODEL
# FILE: models.py
# ==========================================================

class LiveClass(db.Model):

    __tablename__ = "live_class"

    id = db.Column(db.Integer, primary_key=True)

    meet_link = db.Column(db.String(500), nullable=False)

    class_date = db.Column(db.String(50))

    class_time = db.Column(db.String(50))

     # ================= NOTES =================

class Notes(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    subject = db.Column(db.String(100), nullable=False)

    chapter = db.Column(db.String(200), nullable=False)

    pdf_file = db.Column(db.String(300), nullable=False)

    upload_date = db.Column(db.String(50))

    # ==========================================================
# NOTICE MODEL
# FILE: models.py
# ==========================================================

class Notice(db.Model):

    __tablename__ = "notice"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)

    description = db.Column(db.Text, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )

    # ==========================================================
# LOGIN ATTEMPT MODEL
# FILE: models.py
# ==========================================================

class LoginAttempt(db.Model):

    __tablename__ = "login_attempt"

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(100))

    attempts = db.Column(db.Integer, default=0)

    locked_until = db.Column(db.DateTime)
    # ==========================================================
# TEST MODEL
# FILE: models.py
# ==========================================================

class Test(db.Model):

    __tablename__ = "test"

    id = db.Column(db.Integer, primary_key=True)

    question = db.Column(db.String(500), nullable=False)

    option1 = db.Column(db.String(200), nullable=False)
    option2 = db.Column(db.String(200), nullable=False)
    option3 = db.Column(db.String(200), nullable=False)
    option4 = db.Column(db.String(200), nullable=False)

    answer = db.Column(db.String(200), nullable=False)

    # ==========================================================
# ACTIVE SESSION MODEL (2-DEVICE LIMIT)
# FILE: models.py
# ==========================================================

class ActiveSession(db.Model):
    __tablename__ = "active_session"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    session_token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)