from flask import Flask, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATABASE = "users.db"


# Tạo database nếu chưa có
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()


@app.route("/", methods=["GET", "POST"])
def login():
    message = ""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[0], password):
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            message = "<p style='color:red;'>Invalid username or password</p>"

    return page_template("Login", message, register_link=True)


@app.route("/register", methods=["GET", "POST"])
def register():
    message = ""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        hashed_password = generate_password_hash(password)

        try:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                      (username, hashed_password))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except:
            message = "<p style='color:red;'>Username already exists</p>"

    return page_template("Register", message, register_link=False)


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


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


def page_template(title, message, register_link):
    link = ""
    if register_link:
        link = '<p>Don\\'t have account? <a href="/register">Register</a></p>'
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
