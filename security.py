from flask import request

login_attempts = {}
MAX_ATTEMPTS = 5

def check_login_attempt():
    ip = request.remote_addr

    if ip not in login_attempts:
        login_attempts[ip] = 0

    if login_attempts[ip] >= MAX_ATTEMPTS:
        return False

    return True

def record_failed_attempt():
    ip = request.remote_addr
    login_attempts[ip] += 1

def reset_attempt():
    ip = request.remote_addr
    login_attempts[ip] = 0
