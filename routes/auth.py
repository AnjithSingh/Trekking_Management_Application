from flask import Blueprint, render_template as render, request, redirect, url_for as get_url, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

auth_controller = Blueprint("auth", __name__)


@auth_controller.route("/")
def index():
    if "user_id" in session:
        role = session.get("role")
        if role == "admin":
            return redirect(get_url("admin.admin_dashboard"))
        if role == "staff":
            return redirect(get_url("staff.staff_dashboard"))
        return redirect(get_url("user.user_dashboard"))
    return render("landing.html")


@auth_controller.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if "username" in request.form:
            uname = request.form["username"]
        else:
            uname = ""
            
        if "password" in request.form:
            pwd = request.form["password"]
        else:
            pwd = ""
        user = db.session.query(User).filter_by(username=uname).first()
        if user and check_password_hash(user.password, pwd):
            if user.status == "blacklisted":
                flash("Your account has been blacklisted. Contact admin.", "danger")
                return redirect(get_url("auth.login"))
            if user.role == "staff" and user.status == "pending":
                flash("Your staff account is pending admin approval.", "warning")
                return redirect(get_url("auth.login"))
            session["user_id"] = user.id
            session["role"] = user.role
            session["username"] = user.username
            flash(f"Welcome back, {user.full_name}!", "success")
            if user.role == "admin":
                return redirect(get_url("admin.admin_dashboard"))
            if user.role == "staff":
                return redirect(get_url("staff.staff_dashboard"))
            return redirect(get_url("user.user_dashboard"))
        flash("Invalid credentials.", "danger")
    return render("auth/login.html")


@auth_controller.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if "username" in request.form:
            uname = request.form["username"]
        else:
            uname = ""
            
        if "email" in request.form:
            email = request.form["email"]
        else:
            email = ""
            
        if "password" in request.form:
            pwd = request.form["password"]
        else:
            pwd = ""
            
        if "full_name" in request.form:
            fname = request.form["full_name"]
        else:
            fname = ""
            
        if "phone" in request.form:
            phone = request.form["phone"]
        else:
            phone = ""
        if not uname or not email or not pwd or not fname:
            flash("All required fields must be filled.", "danger")
            return redirect(get_url("auth.register"))
        if len(uname) < 3:
            flash("Username must be at least 3 characters long.", "danger")
            return redirect(get_url("auth.register"))
        if len(pwd) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return redirect(get_url("auth.register"))
        if "@" not in email or "." not in email:
            flash("Invalid email address.", "danger")
            return redirect(get_url("auth.register"))
        if db.session.query(User).filter_by(username=uname).first():
            flash("Username already taken.", "danger")
            return redirect(get_url("auth.register"))
        if db.session.query(User).filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return redirect(get_url("auth.register"))
        role_choice = request.form.get("role", "user")
        role = "staff" if role_choice == "staff" else "user"
        status = "pending" if role == "staff" else "active"
        
        new_user = User(
            username=uname, email=email,
            password=generate_password_hash(pwd),
            full_name=fname, phone=phone, role=role, status=status
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(get_url("auth.login"))
    return render("auth/register.html")


@auth_controller.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(get_url("auth.index"))
