from flask import Flask, g, session
from werkzeug.security import generate_password_hash
from models import db, User
from routes import auth_controller, admin_controller, staff_controller, user_controller, api_bp
import os

app = Flask(__name__)

# Config
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "trekking-secret-key-2026")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "instance", "trekking.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ── Database ─────────────────────────────────────────────────────────
os.makedirs(os.path.join(os.path.dirname(__file__), "instance"), exist_ok=True)
db.init_app(app)

with app.app_context():
    db.create_all()
    if not db.session.query(User).filter_by(role="admin").first():
        admin = User(
            username="admin",
            email="admin@trekking.com",
            password=generate_password_hash("admin123"),
            full_name="System Administrator",
            phone="9999999999",
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()

# ── Blueprints ───────────────────────────────────────────────────────
app.register_blueprint(auth_controller)
app.register_blueprint(admin_controller)
app.register_blueprint(staff_controller)
app.register_blueprint(user_controller)
app.register_blueprint(api_bp)

# ── Global before-request ────────────────────────────────────────────
@app.before_request
def before_request():
    g.user = None
    if "user_id" in session:
        g.user = db.session.query(User).get(session["user_id"])

# ── Run ──────────────────────────────────────────────────────────────

from flask import send_from_directory
import os

@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('css', filename)

@app.route('/images/<path:filename>')
def serve_images(filename):
    return send_from_directory('images', filename)

if __name__ == "__main__":
    app.run(debug=True, port=5000)


