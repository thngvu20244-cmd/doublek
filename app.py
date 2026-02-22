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

        # Tạo admin mặc định nếu chưa có
        c.execute("SELECT * FROM users WHERE username = 'admin'")
        if not c.fetchone():
            admin_pass = generate_password_hash("123456")
            c.execute("""
                INSERT INTO users (username, password, role)
                VALUES (?, ?, ?)
            """, ("admin", admin_pass, "admin"))
        conn.commit()


init_db()


# =========================
# LOGIN
# =========================
@app.route("/", methods=["GET", "POST"])
def login():
    message = ""

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

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
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

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
        admin_link = '<p><a href="/admin">Go to Admin Panel</a></p>'

    return f"""
    <h2>Welcome {session['username']}</h2>
    <p>Role: {session['role']}</p>
    {admin_link}
    <p><a href="/logout">Logout</a></p>
    """


# =========================
# ADMIN PANEL
# =========================
@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("SELECT id, username, role, is_active FROM users")
        users = c.fetchall()

    table = "<h2>Admin Panel</h2><table border=1><tr><th>ID</th><th>User</th><th>Role</th><th>Status</th><th>Action</th></tr>"

    for u in users:
        status = "Active" if u[3] == 1 else "Locked"
        toggle = f"<a href='/toggle/{u[0]}'>Lock/Unlock</a>"
        delete = f"<a href='/delete/{u[0]}'>Delete</a>"
        table += f"<tr><td>{u[0]}</td><td>{u[1]}</td><td>{u[2]}</td><td>{status}</td><td>{toggle} | {delete}</td></tr>"

    table += "</table><br><a href='/dashboard'>Back</a>"
    return table


# =========================
# DELETE USER
# =========================
@app.route("/delete/<int:user_id>")
def delete(user_id):
    if session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()

    return redirect(url_for("admin"))


# =========================
# LOCK / UNLOCK
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
        conn.commit()

    return redirect(url_for("admin"))


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =========================
# SIMPLE TEMPLATE
# =========================
def page_template(title, message, register_link):
    link = ""
    if register_link:
        link = "<p>Don't have account? <a href='/register'>Register</a></p>"
    else:
        link = "<p>Already have account? <a href='/'>Login</a></p>"

    return f"""
    <h2>{title}</h2>
    <form method="POST">
        <input name="username" placeholder="Username" required><br><br>
        <input name="password" type="password" placeholder="Password" required><br><br>
        <button type="submit">{title}</button>
    </form>
    {message}
    {link}
    """


# =========================
# RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
