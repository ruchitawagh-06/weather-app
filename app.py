from flask import Flask, render_template, request, redirect, session, jsonify
import requests
import os

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "1234"   # change in production

# =========================
# DATABASE CONFIG
# =========================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

with app.app_context():
    db.create_all()

# =========================
# API KEY
# =========================
API_KEY = os.environ.get("API_KEY")

# =========================
# WEATHER HELPER
# =========================
def chatbot(temp, desc):
    desc = desc.lower()
    if "rain" in desc:
        return "☔ Carry umbrella"
    elif temp > 35:
        return "🔥 Stay hydrated"
    elif temp < 15:
        return "🧥 Wear warm clothes"
    return "🌤 Nice weather"


# =========================
# REGISTER
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        if User.query.filter_by(username=username).first():
            return "User already exists"

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()

        if user and check_password_hash(user.password, request.form["password"]):
            session["user"] = user.username
            return redirect("/")
        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error)


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


# =========================
# PROFILE
# =========================
@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect("/login")

    return render_template("profile.html", user=session["user"])


# =========================
# HOME (WEATHER DASHBOARD)
# =========================
@app.route("/", methods=["GET", "POST"])
def home():
    if "user" not in session:
        return redirect("/login")

    weather = None
    forecast = None
    temps = []
    labels = []
    advice = None
    error = None

    if request.method == "POST":
        city = request.form.get("city")

        try:
            # Current weather
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
            res = requests.get(url).json()

            if str(res.get("cod")) == "200":
                weather = {
                    "city": city.upper(),
                    "temp": res["main"]["temp"],
                    "humidity": res["main"]["humidity"],
                    "desc": res["weather"][0]["description"]
                }
                advice = chatbot(weather["temp"], weather["desc"])
            else:
                error = "City not found"

            # Forecast
            f_url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
            f_res = requests.get(f_url).json()

            if str(f_res.get("cod")) == "200":
                forecast = []

                for i in range(0, 40, 8):
                    day = f_res["list"][i]

                    forecast.append({
                        "temp": day["main"]["temp"],
                        "desc": day["weather"][0]["description"]
                    })

                    temps.append(day["main"]["temp"])
                    labels.append(f"Day {len(labels)+1}")

        except Exception as e:
            print("ERROR:", e)
            error = "Something went wrong"

    return render_template("index.html",
                           weather=weather,
                           forecast=forecast,
                           temps=temps,
                           labels=labels,
                           advice=advice,
                           error=error)


# =========================
# LOCATION API (lat/lon → city)
# =========================
@app.route("/location")
def location():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        res = requests.get(url).json()

        return jsonify({"city": res.get("name")})

    except Exception as e:
        print("Location error:", e)
        return jsonify({"city": None})


# =========================
# AI CHATBOT
# =========================
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    msg = data.get("msg", "").lower()

    if "hot" in msg:
        reply = "🔥 It's hot, stay hydrated!"
    elif "rain" in msg:
        reply = "☔ Carry an umbrella"
    elif "cold" in msg:
        reply = "🧥 Wear warm clothes"
    else:
        reply = "🌤 Weather looks normal"

    return jsonify({"reply": reply})


# =========================
# RUN APP (Render Compatible)
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
