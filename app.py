from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Login</title>
<style>
body{
display:flex;
justify-content:center;
align-items:center;
height:100vh;
background:#2c5364;
font-family:Arial;
}

.box{
background:#fff;
padding:40px;
border-radius:15px;
width:320px;
text-align:center;
box-shadow:0 10px 30px rgba(0,0,0,0.3);
}

input{
width:100%;
padding:10px;
margin:10px 0;
border-radius:8px;
border:1px solid #ccc;
}

button{
width:100%;
padding:10px;
border:none;
border-radius:8px;
background:#2c5364;
color:#fff;
cursor:pointer;
margin-top:10px;
}

.google{
background:#DB4437;
}

.facebook{
background:#1877F2;
}

.social button{
margin-top:10px;
}
</style>
</head>

<body>

<div class="box">
<h2>Login</h2>

<input type="text" placeholder="Username">
<input type="password" placeholder="Password">
<button>Login</button>

<button class="google">Login with Google</button>
<button class="facebook">Login with Facebook</button>

</div>

</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
