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

<!-- Icon -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">

<style>
body{
display:flex;
justify-content:center;
align-items:center;
height:100vh;
background:linear-gradient(45deg,#0f2027,#2c5364);
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

.social{
display:flex;
justify-content:space-between;
margin-top:15px;
}

.social button{
width:48%;
background:#fff;
border:1px solid #ccc;
color:#333;
font-weight:bold;
}

.google i{ color:#DB4437; }
.facebook i{ color:#1877F2; }

.social button:hover{
background:#f2f2f2;
}
</style>
</head>

<body>

<div class="box">
<h2>Login</h2>

<input type="text" placeholder="Username">
<input type="password" placeholder="Password">
<button>Login</button>

<p style="margin-top:15px;">Or login with</p>

<div class="social">
<button class="google"><i class="fab fa-google"></i> Google</button>
<button class="facebook"><i class="fab fa-facebook-f"></i> Facebook</button>
</div>

</div>

</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
