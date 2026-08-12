from flask import Blueprint, render_template as render, request, redirect, url_for as get_url, flash, session
from werkzeug.security import generate_password_hash
from models import db, User, Trek, Booking

admin_controller = Blueprint("admin", __name__, url_prefix="/admin")


@admin_controller.route("/")
def admin_dashboard():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(get_url("auth.index"))
    if session.get("role") != "admin":
        flash("Access denied.", "danger")
        return redirect(get_url("auth.index"))

    stats = {
        "treks": db.session.query(Trek).count(),
        "users": db.session.query(User).filter_by(role="user").count(),
        "staff": db.session.query(User).filter_by(role="staff").count(),
        "bookings": db.session.query(Booking).count(),
        "open": db.session.query(Trek).filter_by(status="Open").count(),
        "completed": db.session.query(Trek).filter_by(status="Completed").count(),
    }
    recent_bookings = (
        db.session.query(Booking, User, Trek)
        .join(User, Booking.user_id == User.id)
        .join(Trek, Booking.trek_id == Trek.id)
        .order_by(Booking.booking_date.desc()).limit(5).all()
    )
    recent_treks = db.session.query(Trek).order_by(Trek.created_at.desc()).limit(5).all()
    
    # Chart Data Preparation
    import json
    popular_treks = []
    for t in db.session.query(Trek).all():
        b_count = db.session.query(Booking).filter_by(trek_id=t.id).count()
        popular_treks.append({"name": t.name, "count": b_count})
    popular_treks.sort(key=lambda x: x["count"], reverse=True)
    top_5 = popular_treks[:5]
    
    trek_chart_labels = [x["name"] for x in top_5]
    trek_chart_data = [x["count"] for x in top_5]
    
    booking_status_data = [
        db.session.query(Booking).filter_by(status="Booked").count(),
        db.session.query(Booking).filter_by(status="Completed").count(),
        db.session.query(Booking).filter_by(status="Cancelled").count()
    ]

    return render("admin/dashboard.html", stats=stats,
                           recent_bookings=recent_bookings, recent_treks=recent_treks,
                           trek_chart_labels=json.dumps(trek_chart_labels),
                           trek_chart_data=json.dumps(trek_chart_data),
                           booking_status_data=json.dumps(booking_status_data))


# ── Treks ────────────────────────────────────────────────────────────
@admin_controller.route("/treks")
def admin_treks():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(get_url("auth.index"))
    if session.get("role") != "admin":
        flash("Access denied.", "danger")
        return redirect(get_url("auth.index"))

    q = request.args.get("q", "").strip()
    query = db.session.query(Trek)
    if q:
        filters = [Trek.name.ilike(f"%{q}%"), Trek.location.ilike(f"%{q}%")]
        if q.isdigit():
            filters.append(Trek.id == int(q))
        query = query.filter(db.or_(*filters))
    treks = query.order_by(Trek.created_at.desc()).all()
    return render("admin/treks.html", treks=treks, q=q)


@admin_controller.route("/treks/add", methods=["GET", "POST"])
def admin_add_trek():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(get_url("auth.index"))
    if session.get("role") != "admin":
        flash("Access denied.", "danger")
        return redirect(get_url("auth.index"))

    staff_list = db.session.query(User).filter_by(role="staff", status="active").all()
    if request.method == "POST":
        name = request.form["name"].strip()
        location = request.form["location"].strip()
        if not name or not location:
            flash("Trek name and location are required.", "danger")
            return redirect(get_url("admin.admin_add_trek"))
        try:
            slots = int(request.form["total_slots"])
            duration_days = int(request.form["duration_days"])
            price = float(request.form.get("price", 0))
            if slots <= 0 or duration_days <= 0 or price < 0:
                raise ValueError
        except ValueError:
            flash("Slots and duration must be positive integers, and price cannot be negative.", "danger")
            return redirect(get_url("admin.admin_add_trek"))
        
        trek = Trek(
            name=name,
            location=location,
            difficulty=request.form["difficulty"],
            duration_days=duration_days,
            total_slots=slots,
            available_slots=slots,
            assigned_staff_id=request.form.get("assigned_staff_id") or None,
            status=request.form.get("status", "Pending"),
            start_date=request.form.get("start_date") or None,
            end_date=request.form.get("end_date") or None,
            description=request.form.get("description", "").strip(),
            price=float(request.form.get("price", 0)),
            altitude=request.form.get("altitude", "").strip(),
        )
        db.session.add(trek)
        db.session.commit()
        flash("Trek created!", "success")
        return redirect(get_url("admin.admin_treks"))
    return render("admin/add_trek.html", staff_list=staff_list)


@admin_controller.route("/treks/<int:tid>/edit", methods=["GET", "POST"])
def admin_edit_trek(tid):
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(get_url("auth.index"))
    if session.get("role") != "admin":
        flash("Access denied.", "danger")
        return redirect(get_url("auth.index"))

    trek = db.session.query(Trek).get_or_404(tid)
    staff_list = db.session.query(User).filter_by(role="staff", status="active").all()
    if request.method == "POST":
        name = request.form["name"].strip()
        location = request.form["location"].strip()
        if not name or not location:
            flash("Trek name and location are required.", "danger")
            return redirect(get_url("admin.admin_edit_trek", tid=tid))
        try:
            new_total = int(request.form["total_slots"])
            duration_days = int(request.form["duration_days"])
            price = float(request.form.get("price", 0))
            if new_total <= 0 or duration_days <= 0 or price < 0:
                raise ValueError
        except ValueError:
            flash("Slots and duration must be positive integers, and price cannot be negative.", "danger")
            return redirect(get_url("admin.admin_edit_trek", tid=tid))

        booked = trek.total_slots - trek.available_slots
        new_avail = max(new_total - booked, 0)
        trek.name = name
        trek.location = location
        trek.difficulty = request.form["difficulty"]
        trek.duration_days = duration_days
        trek.total_slots = new_total
        trek.available_slots = new_avail
        trek.assigned_staff_id = request.form.get("assigned_staff_id") or None
        trek.status = request.form.get("status", "Pending")
        trek.start_date = request.form.get("start_date") or None
        trek.end_date = request.form.get("end_date") or None
        trek.description = request.form.get("description", "").strip()
        trek.price = float(request.form.get("price", 0))
        trek.altitude = request.form.get("altitude", "").strip()
        db.session.commit()
        flash("Trek updated!", "success")
        return redirect(get_url("admin.admin_treks"))
    return render("admin/edit_trek.html", trek=trek, staff_list=staff_list)


@admin_controller.route("/treks/<int:tid>/delete", methods=["POST"])
def admin_delete_trek(tid):
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(get_url("auth.index"))
    if session.get("role") != "admin":
        flash("Access denied.", "danger")
        return redirect(get_url("auth.index"))

    trek = db.session.query(Trek).get_or_404(tid)
    db.session.query(Booking).filter_by(trek_id=tid).delete()
    db.session.delete(trek)
    db.session.commit()
    flash("Trek deleted.", "info")
    return redirect(get_url("admin.admin_treks"))


# ── Staff ────────────────────────────────────────────────────────────
@admin_controller.route("/staff")
def admin_staff():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(get_url("auth.index"))
    if session.get("role") != "admin":
        flash("Access denied.", "danger")
        return redirect(get_url("auth.index"))

    q = request.args.get("q", "").strip()
    query = db.session.query(User).filter_by(role="staff")
    if q:
        filters = [User.full_name.ilike(f"%{q}%"), User.username.ilike(f"%{q}%")]
        if q.isdigit():
            filters.append(User.id == int(q))
        query = query.filter(db.or_(*filters))
    staff = query.order_by(User.created_at.desc()).all()
    return render("admin/staff.html", staff=staff, q=q)


@admin_controller.route("/staff/add", methods=["GET", "POST"])
def admin_add_staff():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(get_url("auth.index"))
    if session.get("role") != "admin":
        flash("Access denied.", "danger")
        return redirect(get_url("auth.index"))

    if request.method == "POST":
        uname = request.form["username"].strip()
        email = request.form["email"].strip()
        pwd = request.form["password"]
        fname = request.form["full_name"].strip()
        
        if not uname or not email or not pwd or not fname:
            flash("All required fields must be filled.", "danger")
            return redirect(get_url("admin.admin_add_staff"))
        if len(pwd) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return redirect(get_url("admin.admin_add_staff"))
        if "@" not in email or "." not in email:
            flash("Invalid email format.", "danger")
            return redirect(get_url("admin.admin_add_staff"))

        if db.session.query(User).filter_by(username=uname).first():
            flash("Username taken.", "danger")
            return redirect(get_url("admin.admin_add_staff"))
        if db.session.query(User).filter_by(email=email).first():
            flash("Email taken.", "danger")
            return redirect(get_url("admin.admin_add_staff"))
        staff = User(
            username=uname, email=email,
            password=generate_password_hash(request.form["password"]),
            full_name=request.form["full_name"].strip(),
            phone=request.form.get("phone", "").strip(),
            role="staff",
            bio=request.form.get("bio", "").strip(),
        )
        db.session.add(staff)
        db.session.commit()
        flash("Staff member added!", "success")
        return redirect(get_url("admin.admin_staff"))
    return render("admin/add_staff.html")


@admin_controller.route("/staff/<int:sid>/remove", methods=["POST"])
def admin_remove_staff(sid):
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(get_url("auth.index"))
    if session.get("role") != "admin":
        flash("Access denied.", "danger")
        return redirect(get_url("auth.index"))

    staff = db.session.query(User).filter_by(id=sid, role="staff").first_or_404()
    db.session.query(Trek).filter_by(assigned_staff_id=sid).update({"assigned_staff_id": None})
    db.session.delete(staff)
    db.session.commit()
    flash("Staff removed.", "info")
    return redirect(get_url("admin.admin_staff"))


@admin_controller.route("/staff/<int:sid>/toggle", methods=["POST"])
def admin_toggle_staff(sid):
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(get_url("auth.index"))
    if session.get("role") != "admin":
        flash("Access denied.", "danger")
        return redirect(get_url("auth.index"))

    staff = db.session.query(User).get_or_404(sid)
    if staff.status == "pending":
        staff.status = "active"
        flash("Staff approved and activated.", "success")
    elif staff.status == "active":
        staff.status = "blacklisted"
        flash("Staff blacklisted.", "warning")
    else:
        staff.status = "active"
        flash("Staff activated.", "success")
    db.session.commit()
    return redirect(get_url("admin.admin_staff"))


# ── Users ────────────────────────────────────────────────────────────
@admin_controller.route("/users")
def admin_users():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(get_url("auth.index"))
    if session.get("role") != "admin":
        flash("Access denied.", "danger")
        return redirect(get_url("auth.index"))

    q = request.args.get("q", "").strip()
    query = db.session.query(User).filter_by(role="user")
    if q:
        filters = [User.full_name.ilike(f"%{q}%"), User.username.ilike(f"%{q}%")]
        if q.isdigit():
            filters.append(User.id == int(q))
        query = query.filter(db.or_(*filters))
    users = query.order_by(User.created_at.desc()).all()
    return render("admin/users.html", users=users, q=q)


@admin_controller.route("/users/<int:uid>/toggle", methods=["POST"])
def admin_toggle_user(uid):
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(get_url("auth.index"))
    if session.get("role") != "admin":
        flash("Access denied.", "danger")
        return redirect(get_url("auth.index"))

    user = db.session.query(User).get_or_404(uid)
    user.status = "blacklisted" if user.status == "active" else "active"
    db.session.commit()
    flash(f"User {'blacklisted' if user.status == 'blacklisted' else 'activated'}.", "info")
    return redirect(get_url("admin.admin_users"))


# ── Bookings ─────────────────────────────────────────────────────────
@admin_controller.route("/bookings")
def admin_bookings():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(get_url("auth.index"))
    if session.get("role") != "admin":
        flash("Access denied.", "danger")
        return redirect(get_url("auth.index"))

    q = request.args.get("q", "").strip()
    query = db.session.query(Booking, User, Trek).join(User, Booking.user_id == User.id).join(Trek, Booking.trek_id == Trek.id)
    if q:
        filters = [User.full_name.ilike(f"%{q}%"), User.username.ilike(f"%{q}%"), Trek.name.ilike(f"%{q}%")]
        if q.isdigit():
            filters.append(Booking.id == int(q))
        query = query.filter(db.or_(*filters))
    bookings = query.order_by(Booking.booking_date.desc()).all()
    return render("admin/bookings.html", bookings=bookings, q=q)
