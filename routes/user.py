from flask import Blueprint, render_template as render, request, redirect, url_for as get_url, flash, session
from models import db, User, Trek, Booking

user_controller = Blueprint("user", __name__)


@user_controller.route("/dashboard")
def user_dashboard():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(get_url("auth.index"))
    if session.get("role") != "user":
        flash("Access denied.", "danger")
        return redirect(get_url("auth.index"))

    uid = session["user_id"]
    open_treks = db.session.query(Trek).filter(Trek.status.in_(["Open", "Approved"])).order_by(Trek.start_date).limit(6).all()
    my_bookings = (
        db.session.query(Booking, Trek)
        .join(Trek, Booking.trek_id == Trek.id)
        .filter(Booking.user_id == uid, Booking.status == "Booked")
        .order_by(Booking.booking_date.desc()).all()
    )
    stats = {
        "total_bookings": db.session.query(Booking).filter_by(user_id=uid).count(),
        "active": db.session.query(Booking).filter_by(user_id=uid, status="Booked").count(),
        "completed": db.session.query(Booking).filter_by(user_id=uid, status="Completed").count(),
    }
    return render("user/dashboard.html", open_treks=open_treks,
                           my_bookings=my_bookings, stats=stats)


@user_controller.route("/treks")
def user_treks():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(get_url("auth.index"))
    if session.get("role") != "user":
        flash("Access denied.", "danger")
        return redirect(get_url("auth.index"))

    query = db.session.query(Trek).filter(Trek.status.in_(["Open", "Approved"]))
    diff = request.args.get("difficulty", "")
    loc = request.args.get("location", "").strip()
    search = request.args.get("search", "").strip()
    if diff:
        query = query.filter_by(difficulty=diff)
    if loc:
        query = query.filter(Trek.location.ilike(f"%{loc}%"))
    if search:
        query = query.filter(db.or_(Trek.name.ilike(f"%{search}%"), Trek.location.ilike(f"%{search}%")))
    treks = query.order_by(Trek.start_date).all()
    locations = db.session.query(Trek.location).filter(Trek.status.in_(["Open", "Approved"])).distinct().order_by(Trek.location).all()
    return render("user/treks.html", treks=treks, locations=[l[0] for l in locations],
                           filters={"difficulty": diff, "location": loc, "search": search})


@user_controller.route("/treks/<int:tid>")
def user_trek_detail(tid):
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(get_url("auth.index"))
    if session.get("role") != "user":
        flash("Access denied.", "danger")
        return redirect(get_url("auth.index"))

    trek = db.session.query(Trek).get_or_404(tid)
    uid = session["user_id"]
    already_booked = db.session.query(Booking).filter_by(user_id=uid, trek_id=tid, status="Booked").first()
    
    return render("user/trek_detail.html", trek=trek, already_booked=bool(already_booked))

@user_controller.route("/treks/<int:tid>/book", methods=["POST"])
def user_book_trek(tid):
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(get_url("auth.index"))
    if session.get("role") != "user":
        flash("Access denied.", "danger")
        return redirect(get_url("auth.index"))

    trek = db.session.query(Trek).get_or_404(tid)
    if trek.status not in ("Open", "Approved"):
        flash("This trek is not available for booking.", "warning")
        return redirect(get_url("user.user_trek_detail", tid=tid))
    if trek.available_slots <= 0:
        flash("No slots available.", "danger")
        return redirect(get_url("user.user_trek_detail", tid=tid))
    if db.session.query(Booking).filter_by(user_id=session["user_id"], trek_id=tid, status="Booked").first():
        flash("You already booked this trek.", "warning")
        return redirect(get_url("user.user_trek_detail", tid=tid))
    booking = Booking(user_id=session["user_id"], trek_id=tid, status="Booked")
    db.session.add(booking)
    trek.available_slots -= 1
    db.session.commit()
    flash("Trek booked successfully!", "success")
    return redirect(get_url("user.user_bookings"))


@user_controller.route("/bookings")
def user_bookings():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(get_url("auth.index"))
    if session.get("role") != "user":
        flash("Access denied.", "danger")
        return redirect(get_url("auth.index"))

    bookings = (
        db.session.query(Booking, Trek)
        .join(Trek, Booking.trek_id == Trek.id)
        .filter(Booking.user_id == session["user_id"])
        .order_by(Booking.booking_date.desc()).all()
    )
    return render("user/bookings.html", bookings=bookings)


@user_controller.route("/bookings/<int:bid>/cancel", methods=["POST"])
def user_cancel_booking(bid):
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(get_url("auth.index"))
    if session.get("role") != "user":
        flash("Access denied.", "danger")
        return redirect(get_url("auth.index"))

    booking = db.session.query(Booking).filter_by(id=bid, user_id=session["user_id"]).first()
    if booking and booking.status == "Booked":
        booking.status = "Cancelled"
        trek = db.session.query(Trek).get(booking.trek_id)
        trek.available_slots += 1
        db.session.commit()
        flash("Booking cancelled.", "info")
    return redirect(get_url("user.user_bookings"))


@user_controller.route("/history")
def user_history():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(get_url("auth.index"))
    if session.get("role") != "user":
        flash("Access denied.", "danger")
        return redirect(get_url("auth.index"))

    history = (
        db.session.query(Booking, Trek)
        .join(Trek, Booking.trek_id == Trek.id)
        .filter(Booking.user_id == session["user_id"],
                Booking.status.in_(["Completed", "Cancelled"]))
        .order_by(Booking.booking_date.desc()).all()
    )
    return render("user/history.html", history=history)


@user_controller.route("/profile", methods=["GET", "POST"])
def user_profile():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(get_url("auth.index"))
    if session.get("role") != "user":
        flash("Access denied.", "danger")
        return redirect(get_url("auth.index"))

    user = db.session.query(User).get(session["user_id"])
    if request.method == "POST":
        fname = request.form["full_name"].strip()
        email = request.form["email"].strip()
        
        if not fname or not email:
            flash("Full name and email are required.", "danger")
            return redirect(get_url("user.user_profile"))
        if "@" not in email or "." not in email:
            flash("Invalid email format.", "danger")
            return redirect(get_url("user.user_profile"))
            
        existing_email = db.session.query(User).filter(User.email == email, User.id != user.id).first()
        if existing_email:
            flash("Email is already in use by another account.", "danger")
            return redirect(get_url("user.user_profile"))
            
        user.full_name = fname
        user.phone = request.form.get("phone", "").strip()
        user.bio = request.form.get("bio", "").strip()
        user.email = email
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(get_url("user.user_profile"))
    return render("user/profile.html", user=user)
