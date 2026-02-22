from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Login & Register</title>
<style>
*{
margin:0;
padding:0;
box-sizing:border-box;
font-family:Arial;
}

body{
display:flex;
justify-content:center;
align-items:center;
height:100vh;
background:linear-gradient(45deg,#0f2027,#2c5364);
}

.container{
position:relative;
width:850px;
height:500px;
background:#fff;
border-radius:20px;
overflow:hidden;
box-shadow:0 15px 40px rgba(0,0,0,0.3);
}

.form-box{
position:absolute;
width:50%;
height:100%;
display:flex;
justify-content:center;
align-items:center;
flex-direction:column;
padding:40px;
transition:.6s ease-in-out;
}

.login{ right:0; }
.register{ left:0; }

h2{ margin-bottom:20px; }

input{
width:100%;
padding:12px;
margin:10px 0;
border-radius:8px;
border:1px solid #ccc;
}

button{
padding:12px 40px;
border:none;
border-radius:25px;
background:#2c5364;
color:#fff;
cursor:pointer;
margin-top:10px;
}

.overlay{
position:absolute;
width:50%;
height:100%;
background:linear-gradient(45deg,#0f2027,#2c5364);
color:#fff;
display:flex;
justify-content:center;
align-items:center;
flex-direction:column;
text-align:center;
padding:40px;
transition:.6s ease-in-out;
}

.overlay.left{ left:0; }
.overlay.right{ right:0; }

.container.active .login{ transform:translateX(-100%); }
.container.active .register{ transform:translateX(100%); }
.container.active .overlay.left{ transform:translateX(100%); }
.container.active .overlay.right{ transform:translateX(-100%); }

</style>
</head>
<body>

<div class="container" id="container">

<div class="form-box register">
<h2>Registration</h2>
<input type="text" placeholder="Username">
<input type="password" placeholder="Password">
<button>Register</button>
</div>

<div class="form-box login">
<h2>Login</h2>
<input type="text" placeholder="Username">
<input type="password" placeholder="Password">
<button>Login</button>
</div>

<div class="overlay left">
<h2>Hello, Welcome!</h2>
<p>Don't have an account?</p>
<button onclick="toggle()">Register</button>
</div>

<div class="overlay right">
<h2>Welcome Back!</h2>
<p>Already have an account?</p>
<button onclick="toggle()">Login</button>
</div>

</div>

<script>
function toggle(){
document.getElementById("container").classList.toggle("active");
}
</script>

</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
