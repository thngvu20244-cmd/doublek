from flask import Flask, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from security import check_login_attempt, record_failed_attempt, reset_attempt
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ===== TÀI KHOẢN =====
USER = "admin"
PASSWORD_HASH = generate_password_hash("123456")

# ===== TRANG CHỦ =====
@app.route("/")
def home():
    if "user" in session:
        return f"Xin chào {session['user']} <br><a href='/logout'>Đăng xuất</a>"
    return "Bạn chưa đăng nhập <br><a href='/login'>Đăng nhập</a>"

# ===== ĐĂNG NHẬP =====
@app.route("/login", methods=["GET", "POST"])
def login():

    if not check_login_attempt():
        return "Bạn đã thử sai quá nhiều lần!"

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == USER and check_password_hash(PASSWORD_HASH, password):
            session["user"] = username
            reset_attempt()
            return redirect(url_for("home"))
        else:
            record_failed_attempt()
            return "Sai tài khoản hoặc mật khẩu!"

    return '''
        <form method="post">
            <input type="text" name="username" placeholder="Tài khoản"><br>
            <input type="password" name="password" placeholder="Mật khẩu"><br>
            <input type="submit" value="Đăng nhập">
        </form>
    '''

# ===== ĐĂ
