from flask import Flask, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key")

DATABASE = "users.db"


# =========================
# INIT DATABASE
# =========================
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                is_active INTEGER NOT NULL DEFAULT 1
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin TEXT,
                action TEXT,
                target TEXT,
                time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tạo admin mặc định
        c.execute("SELECT * FROM users WHERE username='admin'")
        if not c.fetchone():
            admin_pass = generate_password_hash("123456")
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                      ("admin", admin_pass, "admin"))

        conn.commit()


init_db()


# =========================
# LOGIN
# =========================
@app.route("/", methods=["GET", "POST"])
def login():
    message = ""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("SELECT id, password, role, is_active FROM users WHERE username=?", (username,))
            user = c.fetchone()

        if user:
            if user[3] == 0:
                message = "<p style='color:red;'>Account is locked</p>"
            elif check_password_hash(user[1], password):
                session["user_id"] = user[0]
                session["username"] = username
                session["role"] = user[2]
                return redirect(url_for("dashboard"))
            else:
                message = "<p style='color:red;'>Wrong password</p>"
        else:
            message = "<p style='color:red;'>User not found</p>"

    return page_template("Login", message, True)


# =========================
# REGISTER
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():
    message = ""

    if request.method == "POST":
        username = request.form.get("username")
        password = generate_password_hash(request.form.get("password"))

        try:
            with sqlite3.connect(DATABASE) as conn:
                c = conn.cursor()
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                          (username, password))
                conn.commit()
            return redirect(url_for("login"))
        except:
            message = "<p style='color:red;'>Username already exists</p>"

    return page_template("Register", message, False)


# =========================
# DASHBOARD
# =========================
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))

    admin_link = ""
    if session.get("role") == "admin":
        admin_link = '<p><a href="/admin" style="color:white;">Admin Panel</a></p>'

    return f"""
    <body style="background:linear-gradient(45deg,#0f2027,#2c5364);
                 color:white;
                 font-family:Arial;
                 text-align:center;
                 padding-top:100px;">
        <h1>Welcome {session['username']} 👋</h1>
        <p>Role: {session['role']}</p>
        {admin_link}
        <p><a href="/change-password" style="color:white;">Change Password</a></p>
        <a href="/logout" style="color:white;">Logout</a>
    </body>
    """


# =========================
# ADMIN PANEL
# =========================
@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    search = request.args.get("search", "")

    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()

        if search:
            c.execute("SELECT id, username, role, is_active FROM users WHERE username LIKE ?",
                      ('%' + search + '%',))
        else:
            c.execute("SELECT id, username, role, is_active FROM users")

        users = c.fetchall()
        total_users = len(users)

    rows = ""
    for u in users:
        status = "🟢 Active" if u[3] == 1 else "🔴 Locked"

        rows += f"""
        <tr>
            <td>{u[0]}</td>
            <td>{u[1]}</td>
            <td>{u[2]}</td>
            <td>{status}</td>
            <td>
                <a class="btn" href='/toggle/{u[0]}'>Lock</a>
                <a class="btn" href='/reset/{u[0]}'>Reset</a>
                <a class="btn delete" href='/delete/{u[0]}' onclick="return confirm('Are you sure?')">Delete</a>
            </td>
        </tr>
        """

    return f"""
    <html>
    <head>
    <style>
    body {{background:linear-gradient(45deg,#0f2027,#2c5364);
          font-family:Arial;color:white;padding:40px;}}

    table {{width:100%;background:white;color:black;
            border-radius:10px;border-collapse:collapse;}}

    th, td {{padding:12px;text-align:center;border-bottom:1px solid #ddd;}}

    th {{background:#2c5364;color:white;}}

    tr:hover {{background:#f2f2f2;}}

    .btn {{padding:5px 10px;background:#2c5364;
          color:white;text-decoration:none;border-radius:5px;font-size:12px;}}

    .delete {{background:#b33939;}}

    input {{padding:8px;border-radius:5px;border:none;width:200px;}}

    button {{padding:8px 12px;border:none;border-radius:5px;background:white;cursor:pointer;}}
    </style>
    </head>

    <body>
        <h2>Admin Panel</h2>
        <p>Total Users: {total_users}</p>
        <a href="/logs" style="color:white;">View Logs</a><br><br>

        <form method="GET">
            <input type="text" name="search" placeholder="Search username..." value="{search}">
            <button type="submit">Search</button>
        </form><br>

        <table>
            <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Role</th>
                <th>Status</th>
                <th>Action</th>
            </tr>
            {rows}
        </table>

        <br><a href="/dashboard" style="color:white;">Back</a>
    </body>
    </html>
    """


# =========================
# DELETE
# =========================
@app.route("/delete/<int:user_id>")
def delete(user_id):
    if session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    if user_id == session.get("user_id"):
        return "<h3 style='color:red;text-align:center;'>You cannot delete yourself!</h3><a href='/admin'>Back</a>"

    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()

        c.execute("SELECT role FROM users WHERE id=?", (user_id,))
        result = c.fetchone()

        if result and result[0] == "admin":
            return "<h3 style='color:red;text-align:center;'>Cannot delete another admin!</h3><a href='/admin'>Back</a>"

        c.execute("DELETE FROM users WHERE id=?", (user_id,))
        c.execute("INSERT INTO logs (admin, action, target) VALUES (?, ?, ?)",
                  (session["username"], "delete user", str(user_id)))
        conn.commit()

    return redirect(url_for("admin"))


# =========================
# TOGGLE LOCK
# =========================
@app.route("/toggle/<int:user_id>")
def toggle(user_id):
    if session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("SELECT is_active FROM users WHERE id=?", (user_id,))
        status = c.fetchone()[0]
        new_status = 0 if status == 1 else 1
        c.execute("UPDATE users SET is_active=? WHERE id=?", (new_status, user_id))

        c.execute("INSERT INTO logs (admin, action, target) VALUES (?, ?, ?)",
                  (session["username"], "toggle lock", str(user_id)))

        conn.commit()

    return redirect(url_for("admin"))


# =========================
# RESET PASSWORD
# =========================
@app.route("/reset/<int:user_id>")
def reset_password(user_id):
    if session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    new_password = generate_password_hash("123456")

    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET password=? WHERE id=?", (new_password, user_id))
        c.execute("INSERT INTO logs (admin, action, target) VALUES (?, ?, ?)",
                  (session["username"], "reset password", str(user_id)))
        conn.commit()

    return "<h3 style='color:green;text-align:center;'>Password reset to: 123456</h3><a href='/admin'>Back</a>"


# =========================
# VIEW LOGS
# =========================
@app.route("/logs")
def view_logs():
    if session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("SELECT admin, action, target, time FROM logs ORDER BY time DESC")
        logs = c.fetchall()

    rows = ""
    for log in logs:
        rows += f"<tr><td>{log[0]}</td><td>{log[1]}</td><td>{log[2]}</td><td>{log[3]}</td></tr>"

    return f"""
    <body style="background:linear-gradient(45deg,#0f2027,#2c5364);
                 font-family:Arial;color:white;padding:40px;">
        <h2>System Logs</h2>
        <table border="1" cellpadding="10" style="background:white;color:black;">
            <tr><th>Admin</th><th>Action</th><th>User ID</th><th>Time</th></tr>
            {rows}
        </table>
        <br><a href="/admin" style="color:white;">Back</a>
    </body>
    """


# =========================
# CHANGE PASSWORD
# =========================
@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    if "username" not in session:
        return redirect(url_for("login"))

    message = ""

    if request.method == "POST":
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")

        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("SELECT password FROM users WHERE id=?", (session["user_id"],))
            user = c.fetchone()

            if check_password_hash(user[0], old_password):
                new_hash = generate_password_hash(new_password)
                c.execute("UPDATE users SET password=? WHERE id=?", (new_hash, session["user_id"]))
                conn.commit()
                message = "<p style='color:green;'>Password changed successfully!</p>"
            else:
                message = "<p style='color:red;'>Wrong old password</p>"

    return f"""
    <body style="background:linear-gradient(45deg,#0f2027,#2c5364);
                 font-family:Arial;color:white;text-align:center;padding-top:100px;">
        <h2>Change Password</h2>
        <form method="POST">
            <input type="password" name="old_password" placeholder="Old Password" required><br><br>
            <input type="password" name="new_password" placeholder="New Password" required><br><br>
            <button type="submit">Change</button>
        </form>
        {message}
        <br><a href="/dashboard" style="color:white;">Back</a>
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
# TEMPLATE LOGIN/REGISTER
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
body{{display:flex;justify-content:center;align-items:center;height:100vh;
background:linear-gradient(45deg,#0f2027,#2c5364);font-family:Arial;}}

.box{{background:#fff;padding:40px;border-radius:15px;width:320px;
text-align:center;box-shadow:0 10px 30px rgba(0,0,0,0.3);}}

input{{width:100%;padding:10px;margin:10px 0;border-radius:8px;border:1px solid #ccc;}}

button{{width:100%;padding:10px;border:none;border-radius:8px;
background:#2c5364;color:#fff;cursor:pointer;margin-top:10px;}}

a{{text-decoration:none;color:#2c5364;}}
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
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)              
