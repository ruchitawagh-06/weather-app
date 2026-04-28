from flask import Flask, render_template, request, redirect, session, jsonify
import requests, os

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from openai import OpenAI

app = Flask(__name__)
app.secret_key = "1234"

# DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(200))

with app.app_context():
    db.create_all()

API_KEY = os.environ.get("API_KEY")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ================= LOGIN =================

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        user = User(username=request.form["username"],
                    password=generate_password_hash(request.form["password"]))
        db.session.add(user)
        db.session.commit()
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            session["user"] = user.username
            return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

# ================= HOME =================

@app.route("/", methods=["GET","POST"])
def home():
    if "user" not in session:
        return redirect("/login")

    weather=None; forecast=None; temps=[]; labels=[]

    if request.method=="POST":
        city=request.form["city"]

        url=f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        res=requests.get(url).json()

        if str(res.get("cod"))=="200":
            weather={
                "city":city,
                "temp":res["main"]["temp"],
                "desc":res["weather"][0]["description"]
            }

        f_url=f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
        f_res=requests.get(f_url).json()

        if str(f_res.get("cod"))=="200":
            forecast=[]
            for i in range(0,40,8):
                day=f_res["list"][i]
                forecast.append({
                    "temp":day["main"]["temp"],
                    "desc":day["weather"][0]["description"]
                })
                temps.append(day["main"]["temp"])
                labels.append(f"Day {len(labels)+1}")

    return render_template("index.html", weather=weather,
                           forecast=forecast, temps=temps, labels=labels)

# ================= LOCATION =================

@app.route("/location")
def location():
    lat=request.args.get("lat")
    lon=request.args.get("lon")

    url=f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    res=requests.get(url).json()

    return jsonify({"city": res.get("name")})

# ================= AI CHAT =================

@app.route("/chat", methods=["POST"])
def chat():
    data=request.get_json()
    msg=data.get("msg")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"You are a weather assistant"},
                {"role":"user","content":msg}
            ]
        )
        reply=response.choices[0].message.content
    except:
        reply="AI error"

    return jsonify({"reply":reply})

# ================= RUN =================

if __name__=="__main__":
    port=int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0", port=port)
