from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <html>
        <head>
            <title>Trang chủ</title>
        </head>
        <body>
            <h1>Xin chào</h1>
            <p>Chào mừng bạn đến với trang web Python của tôi.</p>
        </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True)
