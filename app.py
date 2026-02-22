import os
import json
import redis
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token,
    create_refresh_token, jwt_required, get_jwt_identity
)
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# ================= CONFIG =================
app = Flask(__name__)
app.config["SECRET_KEY"] = "ultra-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ultra.db"
app.config["JWT_SECRET_KEY"] = "jwt-ultra-secret"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

# ================= MODELS =================
class Tenant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(255))
    role = db.Column(db.String(50))
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenant.id"))
    locked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

db.create_all()

# Create default tenant + admin
if not Tenant.query.first():
    t = Tenant(name="default")
    db.session.add(t)
    db.session.commit()
    admin = User(
        username="admin",
        password=generate_password_hash("admin123"),
        role="admin",
        tenant_id=t.id
    )
    db.session.add(admin)
    db.session.commit()

# ================= ROLE CHECK =================
def require_role(role):
    user = User.query.get(session.get("user_id"))
    return user and user.role == role

# ================= AUTH =================
@app.route("/api/register", methods=["POST"])
def register():
    data = request.json
    tenant = Tenant.query.filter_by(name=data["tenant"]).first()
    if not tenant:
        tenant = Tenant(name=data["tenant"])
        db.session.add(tenant)
        db.session.commit()

    user = User(
        username=data["username"],
        password=generate_password_hash(data["password"]),
        role="user",
        tenant_id=tenant.id
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({"msg": "Registered"})

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(username=data["username"]).first()

    if not user or not check_password_hash(user.password, data["password"]):
        return jsonify({"msg": "Bad credentials"}), 401

    if user.locked:
        return jsonify({"msg": "Account locked"}), 403

    access = create_access_token(identity=user.id)
    refresh = create_refresh_token(identity=user.id)

    session["user_id"] = user.id

    return jsonify(access_token=access, refresh_token=refresh)

# ================= DASHBOARD =================
@app.route("/api/dashboard")
@jwt_required()
def dashboard():
    user_id = get_jwt_identity()

    cached = r.get("stats")
    if cached:
        return jsonify(json.loads(cached))

    total_users = User.query.count()
    total_tenants = Tenant.query.count()

    data = {
        "users": total_users,
        "tenants": total_tenants,
        "time": str(datetime.utcnow())
    }

    r.setex("stats", 30, json.dumps(data))
    return jsonify(data)

# ================= ADMIN =================
@app.route("/api/admin/lock/<int:user_id>", methods=["POST"])
@jwt_required()
def lock_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    user.locked = True
    db.session.commit()

    socketio.emit("user_locked", {"user": user.username})

    return jsonify({"msg": "User locked"})

# ================= REALTIME =================
@socketio.on("connect")
def on_connect():
    emit("message", {"msg": "Connected to Ultra System"})

# ================= SIMPLE UI =================
@app.route("/")
def home():
    return """
    <h2>ULTRA ENTERPRISE SYSTEM</h2>
    <p>Admin: admin / admin123</p>
    <p>Use API endpoints to interact.</p>
    """

# ================= RUN =================
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
