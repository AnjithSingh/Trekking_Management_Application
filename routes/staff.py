from flask import Blueprint, render_template as render, request, redirect, url_for as get_url, flash, session
from models import db, User, Trek, Booking

staff_controller = Blueprint("staff", __name__, url_prefix="/staff")


@staff_controller.route("/")
def staff_dashboard():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(get_url("auth.index"))
    if session.get("role") != "staff":
        flash("Access denied.", "danger")
        return redirect(get_url("auth.index"))

    uid = session["user_id"]
    treks = db.session.query(Trek).filter_by(assigned_staff_id=uid).order_by(Trek.start_date).all()
    trek_participants = {}
    for t in treks:
        trek_participants[t.id] = db.session.query(Booking).filter_by(trek_id=t.id, status="Booked").count()
    return render("staff/dashboard.html", treks=treks, trek_participants=trek_participants)


@staff_controller.route("/trek/<int:tid>", methods=["GET", "POST"])
def staff_trek_detail(tid):
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(get_url("auth.index"))
    if session.get("role") != "staff":
        flash("Access denied.", "danger")
        return redirect(get_url("auth.index"))

    trek = db.session.query(Trek).filter_by(id=tid, assigned_staff_id=session["user_id"]).first()
    if not trek:
        flash("Trek not found or not assigned to you.", "danger")
        return redirect(get_url("staff.staff_dashboard"))
    if request.method == "POST":
        action = request.form.get("action")
        if action == "update_slots":
            new_avail = int(request.form["available_slots"])
            booked = db.session.query(Booking).filter_by(trek_id=tid, status="Booked").count()
            if new_avail < booked:
                flash(f"Cannot set below current bookings ({booked}).", "danger")
            else:
                trek.available_slots = new_avail
                trek.total_slots = new_avail + booked
                db.session.commit()
                flash("Slots updated.", "success")
        elif action == "update_status":
            new_status = request.form["status"]
            trek.status = new_status
            if new_status == "Completed":
                db.session.query(Booking).filter_by(trek_id=tid, status="Booked").update({"status": "Completed"})
            db.session.commit()
            flash("Status updated.", "success")
        return redirect(get_url("staff.staff_trek_detail", tid=tid))
    participants = (
        db.session.query(Booking, User)
        .join(User, Booking.user_id == User.id)
        .filter(Booking.trek_id == tid)
        .order_by(Booking.booking_date).all()
    )
    return render("staff/trek_detail.html", trek=trek, participants=participants)
