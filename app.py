from flask import Flask, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from security import check_login_attempt, record_failed_attempt, reset_attempt
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

USER = "admin"
PASSWORD_HASH = generate_password_hash("123456")

@app.route("/")
def home():
    if "user" in session:
        return f"Xin chao {session['user']}! <br><a href='/logout'>Dang xuat</a>"
    return "Ban chua dang nhap <br><a href='/login'>Dang nhap</a>"

@app.route("/login", methods=["GET", "POST"])
def login():

    if not check_login_attempt():
        return "Ban da thu sai qua nhieu lan!"

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == USER and check_password_hash(PASSWORD_HASH, password):
            session["user"] = username
            reset_attempt()
            return redirect(url_for("home"))
        else:
            record_failed_attempt()
            return "Sai tai khoan hoac mat khau!"

    return '''
        <form method="post">
            <input type="text" name="username" placeholder="Tai khoan"><br>
            <input type="password" name="password" placeholder="Mat khau"><br>
            <input type="submit" value="Dang nhap">
        </form>
    '''

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run()
