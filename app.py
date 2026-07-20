import os
import secrets
from flask import Flask, render_template, request, redirect, flash, session, abort, send_from_directory
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
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=1)

# Agar Render par hai toh True, local par hai toh False automatically ho jayega
app.config['SESSION_COOKIE_SECURE'] = False if os.getenv('DEBUG', 'False') == 'True' or not os.getenv('RENDER') else True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' 
app.config["MAX_LOGIN_ATTEMPTS"] = 5
app.config["LOCK_TIME"] = 10   # minutes
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

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


def csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def protect_post_requests():
    if request.method == "POST" and not request.is_json:
        sent_token = request.form.get("_csrf_token")
        if not sent_token or sent_token != session.get("_csrf_token"):
            abort(400)


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.is_secure:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.route("/sw.js")
def service_worker():
    response = send_from_directory(app.static_folder, "sw.js", mimetype="application/javascript")
    response.headers["Service-Worker-Allowed"] = "/"
    return response

# --- GLOBAL SCOPE MEIN TABLES AUR DEFAULT ADMIN BANANE KA LOGIC ---
with app.app_context():
    db.create_all() 
    print("✅ Database tables checked/created in the current database")
    
    admin = Admin.query.filter_by(email="bikizzzclasses@gmail.com").first()
    if not admin:
        from werkzeug.security import generate_password_hash
        default_admin_password = os.environ.get("DEFAULT_ADMIN_PASSWORD")
        if default_admin_password:
            admin = Admin(
                name="BIKIzz Admin",
                email="bikizzzclasses@gmail.com",
                password=generate_password_hash(default_admin_password)
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Default Admin Created Successfully")
        else:
            print("⚠️ Default admin not created. Set DEFAULT_ADMIN_PASSWORD first.")
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5105, debug=True)
