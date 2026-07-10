import os
from flask import Flask, render_template, request, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_mail import Message
from extensions import mail
from tutor import tutor_bp

# ==========================================================
# PROJECT IMPORTS
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
    Notice,
    Test,
    ActiveSession  
)

app = Flask(__name__)

# ==========================================================
# EMAIL CONFIGURATION (SECURED WITH ENV VARIABLES)
# ==========================================================
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = "bikizzzclasses@gmail.com"
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = "bikizzzclasses@gmail.com"
mail.init_app(app)

# ==========================================================
# SECURITY CONFIGURATIONS (SESSION PROTECTION)
# ==========================================================
app.secret_key = os.environ.get("SECRET_KEY", "biki_fallback_secret_key_2026")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=1)

# Agar Render par hai toh True, local par hai toh False automatically ho jayega
app.config['SESSION_COOKIE_SECURE'] = False if os.getenv('DEBUG', 'False') == 'True' or not os.getenv('RENDER') else True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' 
app.config["MAX_LOGIN_ATTEMPTS"] = 5
app.config["LOCK_TIME"] = 10   # minutes

# Notes PDF file upload ke liye folder configuration safe rakha hai
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ==========================================================
# DATABASE CONFIGURATION (UPDATED FOR POSTGRESQL)
# ==========================================================
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
    
    admin = Admin.query.filter_by(email="bikizzzclasses@gmail.com").first()
    if not admin:
        from werkzeug.security import generate_password_hash
        admin = Admin(
            name="BIKIzz Admin",
            email="bikizzzclasses@gmail.com",
            password=generate_password_hash("BIKI2488@")
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Default Admin Created Successfully on Cloud Database")
# -----------------------------------------------------------------

# Blueprints Registration
app.register_blueprint(student_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(tutor_bp)

# ================= ABOUT =================
@app.route("/about")
def about():
    return render_template("about.html")

# ================= LOGOUT (UPDATED FOR 2-DEVICE LIMIT) =================
@app.route("/logout")
def logout():
    if "session_token" in session:
        ActiveSession.query.filter_by(session_token=session["session_token"]).delete()
        db.session.commit()

    session.clear()
    flash("Logged Out Successfully")
    return redirect("/login")

# ==========================================================
# TEMPORARY DATABASE FIX ROUTE (Tarika 1)
# ==========================================================
from sqlalchemy import text
@app.route("/biki-db-fix")
def biki_db_fix():
    try:
        db.session.execute(text("ALTER TABLE student ALTER COLUMN profile_image TYPE TEXT;"))
        db.session.execute(text("ALTER TABLE student ALTER COLUMN payment_image TYPE TEXT;"))
        db.session.commit()
        return "<h1>🔥 Badhai Ho! Database Columns Successfully TEXT mein badal gaye hain.</h1><p>Ab aap photo upload test kar sakte hain.</p>"
    except Exception as e:
        db.session.rollback()
        return f"<h1>Kuch gadbad hui:</h1><p>{str(e)}</p>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5105, debug=True)