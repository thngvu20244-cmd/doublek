from flask import Flask, render_template_string, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

DB = "database.db"

# ================= DATABASE =================

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user',
        locked INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        time TEXT
    )''')

    # tạo admin mặc định
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                  ("admin", generate_password_hash("admin123"), "admin"))

    conn.commit()
    conn.close()

def log_action(text):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO logs (action,time) VALUES (?,?)",
              (text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

init_db()

# ================= TEMPLATE =================

base_style = """
<style>
body{
background: linear-gradient(135deg,#667eea,#764ba2);
font-family: Arial;
color:white;
text-align:center;
}
.box{
background:white;
color:black;
padding:20px;
margin:30px auto;
width:400px;
border-radius:10px;
}
button{
padding:8px 15px;
background:#667eea;
color:white;
border:none;
border-radius:5px;
cursor:pointer;
}
a{color:#667eea;text-decoration:none;}
input{padding:6px;margin:5px;}
table{width:100%;color:black;}
</style>
"""

# ================= ROUTES =================

@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    return redirect("/dashboard")

# LOGIN
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=request.form["username"]
        p=request.form["password"]

        conn=sqlite3.connect(DB)
        c=conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?",(u,))
        user=c.fetchone()
        conn.close()

        if user and check_password_hash(user[2],p):
            if user[4]==1:
                return "Tài khoản bị khóa!"
            session["user"]=u
            session["role"]=user[3]
            log_action(f"{u} đăng nhập")
            return redirect("/dashboard")
        return "Sai tài khoản hoặc mật khẩu"

    return render_template_string(base_style+"""
    <div class="box">
    <h2>Login</h2>
    <form method="post">
    <input name="username" placeholder="Username"><br>
    <input name="password" type="password" placeholder="Password"><br>
    <button>Login</button>
    </form>
    <a href="/register">Register</a>
    </div>
    """)

# REGISTER
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        u=request.form["username"]
        p=generate_password_hash(request.form["password"])
        try:
            conn=sqlite3.connect(DB)
            c=conn.cursor()
            c.execute("INSERT INTO users(username,password) VALUES (?,?)",(u,p))
            conn.commit()
            conn.close()
            log_action(f"{u} đăng ký")
            return redirect("/login")
        except:
            return "Username đã tồn tại"

    return render_template_string(base_style+"""
    <div class="box">
    <h2>Register</h2>
    <form method="post">
    <input name="username"><br>
    <input name="password" type="password"><br>
    <button>Register</button>
    </form>
    </div>
    """)

# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    if session["role"]=="admin":
        return redirect("/admin")

    return render_template_string(base_style+"""
    <div class="box">
    <h2>Welcome {{user}}</h2>
    <p>Role: {{role}}</p>
    <a href="/change_password">Đổi mật khẩu</a><br><br>
    <a href="/logout">Logout</a>
    </div>
    """,user=session["user"],role=session["role"])

# ADMIN PANEL
@app.route("/admin")
def admin():
    if "user" not in session or session["role"]!="admin":
        return "Không có quyền"

    search=request.args.get("search","")
    conn=sqlite3.connect(DB)
    c=conn.cursor()

    if search:
        c.execute("SELECT * FROM users WHERE username LIKE ?",('%'+search+'%',))
    else:
        c.execute("SELECT * FROM users")

    users=c.fetchall()
    total=len(users)
    conn.close()

    return render_template_string(base_style+"""
    <div class="box">
    <h2>ADMIN PANEL</h2>
    Tổng user: {{total}}<br><br>

    <form>
    <input name="search" placeholder="Tìm user">
    <button>Tìm</button>
    </form>

    <table border="1">
    <tr><th>User</th><th>Role</th><th>Lock</th><th>Action</th></tr>
    {% for u in users %}
    <tr>
    <td>{{u[1]}}</td>
    <td>{{u[3]}}</td>
    <td>{{u[4]}}</td>
    <td>
    {% if u[1] != session["user"] %}
    <a href="/lock/{{u[1]}}">Lock</a>
    <a href="/unlock/{{u[1]}}">Unlock</a>
    <a href="/reset/{{u[1]}}">Reset</a>
    {% endif %}
    </td>
    </tr>
    {% endfor %}
    </table>

    <br>
    <a href="/logs">Xem Logs</a><br><br>
    <a href="/logout">Logout</a>
    </div>
    """,users=users,total=total,session=session)

# LOCK
@app.route("/lock/<username>")
def lock(username):
    if session.get("role")!="admin":
        return "Không có quyền"
    conn=sqlite3.connect(DB)
    c=conn.cursor()
    c.execute("UPDATE users SET locked=1 WHERE username=?",(username,))
    conn.commit()
    conn.close()
    log_action(f"Lock {username}")
    return redirect("/admin")

# UNLOCK
@app.route("/unlock/<username>")
def unlock(username):
    if session.get("role")!="admin":
        return "Không có quyền"
    conn=sqlite3.connect(DB)
    c=conn.cursor()
    c.execute("UPDATE users SET locked=0 WHERE username=?",(username,))
    conn.commit()
    conn.close()
    log_action(f"Unlock {username}")
    return redirect("/admin")

# RESET PASS
@app.route("/reset/<username>")
def reset(username):
    if session.get("role")!="admin":
        return "Không có quyền"
    conn=sqlite3.connect(DB)
    c=conn.cursor()
    c.execute("UPDATE users SET password=? WHERE username=?",
              (generate_password_hash("123456"),username))
    conn.commit()
    conn.close()
    log_action(f"Reset password {username}")
    return redirect("/admin")

# CHANGE PASSWORD
@app.route("/change_password", methods=["GET","POST"])
def change_password():
    if "user" not in session:
        return redirect("/login")

    if request.method=="POST":
        new=generate_password_hash(request.form["new"])
        conn=sqlite3.connect(DB)
        c=conn.cursor()
        c.execute("UPDATE users SET password=? WHERE username=?",
                  (new,session["user"]))
        conn.commit()
        conn.close()
        log_action(f"{session['user']} đổi mật khẩu")
        return redirect("/dashboard")

    return render_template_string(base_style+"""
    <div class="box">
    <h2>Đổi mật khẩu</h2>
    <form method="post">
    <input name="new" type="password"><br>
    <button>Đổi</button>
    </form>
    </div>
    """)

# LOGS
@app.route("/logs")
def logs():
    if session.get("role")!="admin":
        return "Không có quyền"

    conn=sqlite3.connect(DB)
    c=conn.cursor()
    c.execute("SELECT * FROM logs ORDER BY id DESC")
    data=c.fetchall()
    conn.close()

    return render_template_string(base_style+"""
    <div class="box">
    <h2>System Logs</h2>
    <table border="1">
    {% for l in data %}
    <tr><td>{{l[1]}}</td><td>{{l[2]}}</td></tr>
    {% endfor %}
    </table>
    <br><a href="/admin">Back</a>
    </div>
    """,data=data)

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ================= RUN =================

if __name__=="__main__":
    app.run(host="0.0.0.0",port=5000)
