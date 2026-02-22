import os
import sqlite3
from datetime import datetime
from flask import Flask, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecret"
DB = "database.db"

# ---------------- DB ----------------

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user',
        locked INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        actor TEXT,
        target TEXT,
        time TEXT
    )
    """)

    # admin mặc định
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)",
                  ("admin", generate_password_hash("Vuduythang"), "admin"))

    conn.commit()
    conn.close()

@app.before_request
def before():
    init_db()

# ---------------- LOG ----------------

def add_log(action, actor="", target=""):
    conn = get_db()
    conn.execute("INSERT INTO logs(action,actor,target,time) VALUES(?,?,?,?)",
                 (action, actor, target,
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# ---------------- STYLE ----------------

def layout(content):
    return f"""
    <html>
    <head>
    <title>FULL PRO SYSTEM</title>
    <style>
        body {{
            margin:0;
            font-family: Arial;
            background: linear-gradient(135deg,#667eea,#764ba2);
            display:flex;
            justify-content:center;
            align-items:center;
            height:100vh;
        }}
        .card {{
            background:white;
            padding:25px;
            border-radius:15px;
            width:520px;
            box-shadow:0 10px 30px rgba(0,0,0,0.3);
            text-align:center;
        }}
        input {{
            width:100%;
            padding:8px;
            margin:5px 0;
            border-radius:6px;
            border:1px solid #ccc;
        }}
        button {{
            padding:6px 10px;
            margin:2px;
            border:none;
            border-radius:6px;
            cursor:pointer;
            background:#667eea;
            color:white;
        }}
        button:hover {{
            background:#5a67d8;
        }}
        a {{
            display:block;
            margin-top:8px;
            text-decoration:none;
            color:#667eea;
        }}
        .box {{
            max-height:200px;
            overflow:auto;
            text-align:left;
            font-size:13px;
            margin-top:10px;
        }}
        .stat {{
            background:#f2f2f2;
            padding:6px;
            border-radius:6px;
            margin:4px 0;
        }}
        .row {{
            font-size:13px;
            padding:4px;
            border-bottom:1px solid #eee;
        }}
    </style>
    </head>
    <body>
        <div class="card">
        {content}
        </div>
    </body>
    </html>
    """

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")

# LOGIN
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?",
                            (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            if user["locked"] == 1:
                return layout("<h3>Account Locked</h3>")

            session["user"] = user["username"]
            session["role"] = user["role"]
            add_log("Login Success", username)
            return redirect("/dashboard")

        add_log("Login Failed", username)
        return layout("<h3>Sai tài khoản hoặc mật khẩu</h3><a href='/login'>Back</a>")

    return layout("""
    <h2>Login</h2>
    <form method="post">
    <input name="username" placeholder="Username">
    <input name="password" type="password" placeholder="Password">
    <button>Login</button>
    </form>
    <a href="/register">Register</a>
    """)

# REGISTER
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        try:
            conn = get_db()
            conn.execute("INSERT INTO users(username,password) VALUES(?,?)",
                         (username,password))
            conn.commit()
            conn.close()
            add_log("Register", username)
            return redirect("/login")
        except:
            return layout("<h3>Username đã tồn tại</h3>")

    return layout("""
    <h2>Register</h2>
    <form method="post">
    <input name="username">
    <input name="password" type="password">
    <button>Register</button>
    </form>
    """)

# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    if session["role"] == "admin":
        return redirect("/admin")

    return layout(f"""
    <h2>Welcome {session['user']}</h2>
    <a href="/change_password">Đổi mật khẩu</a>
    <a href="/logout">Logout</a>
    """)

# ADMIN PANEL
@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return layout("<h3>No Permission</h3>")

    conn = get_db()

    search = request.args.get("q","")
    if search:
        users = conn.execute("SELECT * FROM users WHERE username LIKE ?",
                             (f"%{search}%",)).fetchall()
    else:
        users = conn.execute("SELECT * FROM users").fetchall()

    total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    admins = conn.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0]
    locked = conn.execute("SELECT COUNT(*) FROM users WHERE locked=1").fetchone()[0]

    conn.close()

    rows = ""
    for u in users:
        if u["username"] == "admin":
            control = "(Protected)"
        else:
            lock_btn = "Unlock" if u["locked"] else "Lock"
            control = f"""
            <a href="/lock/{u['id']}">{lock_btn}</a>
            <a href="/reset/{u['id']}">Reset</a>
            <a href="/delete/{u['id']}">Delete</a>
            """
        rows += f"<div class='row'>{u['username']} | {u['role']} | {'Locked' if u['locked'] else 'Active'} {control}</div>"

    return layout(f"""
    <h2>ADMIN PANEL</h2>

    <div class="stat">Total: {total}</div>
    <div class="stat">Admins: {admins}</div>
    <div class="stat">Locked: {locked}</div>

    <form>
    <input name="q" placeholder="Search user">
    </form>

    <div class="box">{rows}</div>

    <a href="/logs">View Logs</a>
    <a href="/logout">Logout</a>
    """)

# LOCK / UNLOCK
@app.route("/lock/<int:id>")
def lock_user(id):
    if session.get("role") != "admin":
        return redirect("/login")

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (id,)).fetchone()

    if user and user["username"] != "admin":
        new_status = 0 if user["locked"] else 1
        conn.execute("UPDATE users SET locked=? WHERE id=?", (new_status,id))
        conn.commit()
        add_log("Lock/Unlock", session["user"], user["username"])

    conn.close()
    return redirect("/admin")

# RESET PASSWORD
@app.route("/reset/<int:id>")
def reset_password(id):
    if session.get("role") != "admin":
        return redirect("/login")

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (id,)).fetchone()

    if user and user["username"] != "admin":
        conn.execute("UPDATE users SET password=? WHERE id=?",
                     (generate_password_hash("123456"), id))
        conn.commit()
        add_log("Reset Password", session["user"], user["username"])

    conn.close()
    return redirect("/admin")

# DELETE
@app.route("/delete/<int:id>")
def delete_user(id):
    if session.get("role") != "admin":
        return redirect("/login")

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (id,)).fetchone()

    if user and user["username"] != "admin" and user["username"] != session["user"]:
        conn.execute("DELETE FROM users WHERE id=?", (id,))
        conn.commit()
        add_log("Delete User", session["user"], user["username"])

    conn.close()
    return redirect("/admin")

# CHANGE PASSWORD (USER)
@app.route("/change_password", methods=["GET","POST"])
def change_password():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        new_pass = generate_password_hash(request.form["password"])
        conn = get_db()
        conn.execute("UPDATE users SET password=? WHERE username=?",
                     (new_pass, session["user"]))
        conn.commit()
        conn.close()
        add_log("Change Password", session["user"])
        return redirect("/dashboard")

    return layout("""
    <h3>Change Password</h3>
    <form method="post">
    <input name="password" type="password" placeholder="New Password">
    <button>Save</button>
    </form>
    """)

# LOGS
@app.route("/logs")
def logs():
    if session.get("role") != "admin":
        return redirect("/login")

    conn = get_db()
    data = conn.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()

    log_rows = ""
    for l in data:
        log_rows += f"<div class='row'>{l['time']} | {l['actor']} | {l['action']} | {l['target']}</div>"

    return layout(f"""
    <h2>System Logs</h2>
    <div class="box">{log_rows}</div>
    <a href="/admin">Back</a>
    """)

@app.route("/logout")
def logout():
    if "user" in session:
        add_log("Logout", session["user"])
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
