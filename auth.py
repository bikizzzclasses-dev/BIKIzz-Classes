# ==========================================================
# STEP 2.1 - AUTH.PY IMPORTS
# FILE: auth.py
# ==========================================================

from flask import Blueprint, render_template, request, redirect, flash
from werkzeug.security import generate_password_hash
from models import db, Student

auth_bp = Blueprint("auth", __name__)

# ==========================================================
# STEP 2.2 - STUDENT REGISTER ROUTE
# FILE: auth.py
# ==========================================================

@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        student = Student(
            name=request.form["name"],
            mobile=request.form["mobile"],
            email=request.form["email"],
            password=generate_password_hash(request.form["password"])
        )

        db.session.add(student)
        db.session.commit()

        flash("Registration Successful!")

        return redirect("/login")

    return render_template("register.html")