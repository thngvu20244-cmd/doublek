            from flask import Flask, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# Cấu hình
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", os.urandom(24))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# =========================
# MODEL (TẠO BẢNG)
# =========================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


# Tạo database
with app.app_context():
    db.create_all()


# =========================
# LOGIN
# =========================
@app.route("/", methods=["GET", "POST"])
def login():
    message = ""

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            message = "<p style='color:red;'>Please fill all fields</p>"
        else:
            user = User.query.filter_by(username=username).first()

            if user and check_password_hash(user.password, password):
                session["user"] = user.username
                return redirect(url_for("dashboard"))
            else:
                message = "<p style='color:red;'>Invalid username or password</p>"

    return page_template("Login", message, register_link=True)


# =========================
# REGISTER
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():
    message = ""

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            message = "<p style='color:red;'>Please fill all fields</p>"
        else:
            if User.query.filter_by(username=username).first():
                message = "<p style='color:red;'>Username already exists</p>"
            else:
                hashed_password = generate_password_hash(password)
                new_user = User(username=username, password=hashed_password)
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for("login"))

    return page_template("Register", message, register_link=False)


# =========================
# DASHBOARD
# =========================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    return f"""
    <body style="background:linear-gradient(45deg,#0f2027,#2c5364);
                 color:white;
                 font-family:Arial;
                 text-align:center;
                 padding-top:100px;">
        <h1>Welcome {session['user']} 👋</h1>
        <p>You are logged in successfully.</p>
        <a href="/logout" style="color:white;">Logout</a>
    </body>
    """


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =========================
# TEMPLATE
# =========================
def page_template(title, message, register_link):
    link = ""
    if register_link:
        link = '<p>Don\'t have account? <a href="/register">Register</a></p>'
    else:
        link = '<p>Already have account? <a href="/">Login</a></p>'

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
body{{
display:flex;
justify-content:center;
align-items:center;
height:100vh;
background:linear-gradient(45deg,#0f2027,#2c5364);
font-family:Arial;
}}

.box{{
background:#fff;
padding:40px;
border-radius:15px;
width:320px;
text-align:center;
box-shadow:0 10px 30px rgba(0,0,0,0.3);
}}

input{{
width:100%;
padding:10px;
margin:10px 0;
border-radius:8px;
border:1px solid #ccc;
}}

button{{
width:100%;
padding:10px;
border:none;
border-radius:8px;
background:#2c5364;
color:#fff;
cursor:pointer;
margin-top:10px;
}}

a{{ text-decoration:none; color:#2c5364; }}
</style>
</head>

<body>
<div class="box">
<h2>{title}</h2>
<form method="POST">
<input type="text" name="username" placeholder="Username" required>
<input type="password" name="password" placeholder="Password" required>
<button type="submit">{title}</button>
</form>
{message}
{link}
</div>
</body>
</html>
"""


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
