from flask import Flask, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key")

DATABASE = "users.db"


# ================= INIT DATABASE =================
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
            c.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                ("admin", admin_pass, "admin")
            )

        conn.commit()


init_db()


# ================= LOGIN =================
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
                message = "<p style='color:red;'>Account locked</p>"
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


# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    message = ""

    if request.method == "POST":
        username = request.form.get("username")
        raw_password = request.form.get("password")

        if not username or not raw_password:
            message = "<p style='color:red;'>Fill all fields</p>"
        else:
            password = generate_password_hash(raw_password)
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


# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))

    admin_link = ""
    if session.get("role") == "admin":
        admin_link = '<p><a href="/admin" style="color:white;">Admin Panel</a></p>'

    return f"""
    <body style="background:linear-gradient(45deg,#0f2027,#2c5364);
    color:white;text-align:center;padding-top:100px;font-family:Arial;">
        <h1>Welcome {session['username']} 👋</h1>
        <p>Role: {session['role']}</p>
        {admin_link}
        <p><a href="/change-password" style="color:white;">Change Password</a></p>
        <a href="/logout" style="color:white;">Logout</a>
    </body>
    """


# ================= ADMIN PANEL =================
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
                <a href='/toggle/{u[0]}'>Lock/Unlock</a> |
                <a href='/reset/{u[0]}'>Reset</a> |
                <a href='/delete/{u[0]}' onclick="return confirm('Are you sure?')">Delete</a>
            </td>
        </tr>
        """

    return f"""
    <body style="background:linear-gradient(45deg,#0f2027,#2c5364);
    font-family:Arial;color:white;padding:40px;">
        <h2>Admin Panel</h2>
        <p>Total Users: {total_users}</p>
        <a href="/logs" style="color:white;">View Logs</a><br><br>

        <form method="GET">
            <input type="text" name="search" placeholder="Search username..." value="{search}">
            <button type="submit">Search</button>
        </form><br>

        <table border="1" cellpadding="10" style="background:white;color:black;">
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
    """


# ================= DELETE =================
@app.route("/delete/<int:user_id>")
def delete(user_id):
    if session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    if user_id == session.get("user_id"):
        return "<h3 style='color:red;text-align:center;'>Cannot delete yourself!</h3><a href='/admin'>Back</a>"

    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()

        c.execute("SELECT role FROM users WHERE id=?", (user_id,))
        result = c.fetchone()

        if not result:
            return redirect(url_for("admin"))

        if result[0] == "admin":
            return "<h3 style='color:red;text-align:center;'>Cannot delete another admin!</h3><a href='/admin'>Back</a>"

        c.execute("DELETE FROM users WHERE id=?", (user_id,))
        c.execute("INSERT INTO logs (admin, action, target) VALUES (?, ?, ?)",
                  (session["username"], "delete user", str(user_id)))
        conn.commit()

    return redirect(url_for("admin"))


# ================= TOGGLE =================
@app.route("/toggle/<int:user_id>")
def toggle(user_id):
    if session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("SELECT is_active FROM users WHERE id=?", (user_id,))
        result = c.fetchone()

        if not result:
            return redirect(url_for("admin"))

        new_status = 0 if result[0] == 1 else 1
        c.execute("UPDATE users SET is_active=? WHERE id=?", (new_status, user_id))

        c.execute("INSERT INTO logs (admin, action, target) VALUES (?, ?, ?)",
                  (session["username"], "toggle lock", str(user_id)))

        conn.commit()

    return redirect(url_for("admin"))


# ================= RESET PASSWORD =================
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

    return "<h3 style='color:green;text-align:center;'>Password reset to 123456</h3><a href='/admin'>Back</a>"


# ================= VIEW LOGS =================
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


# ================= CHANGE PASSWORD =================
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

            if user and check_password_hash(user[0], old_password):
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
