from flask import Flask, render_template, request, redirect, session
import requests

app = Flask(__name__)
app.secret_key = "1234"

API_KEY = "54ff43f30c3097a69d22d7f5ff91701f"

# 🤖 AI Suggestion
def chatbot(temp, desc):
    desc = desc.lower()
    if "rain" in desc:
        return "☔ Carry an umbrella"
    elif temp > 35:
        return "🔥 Stay hydrated"
    elif temp < 15:
        return "🧥 Wear warm clothes"
    else:
        return "🌤 Weather looks pleasant!"

# 🔐 Home
@app.route("/", methods=["GET", "POST"])
def home():
    if "user" not in session:
        return redirect("/login")

    weather = None
    forecast = None
    temps = []
    labels = []
    map_url = None
    advice = None

    if request.method == "POST":
        city = request.form["city"]

        map_url = f"https://www.google.com/maps?q={city}"

        # 🌦 Weather
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        res = requests.get(url).json()

        if res.get("cod") == 200:
            weather = {
                "city": city.upper(),
                "temp": res["main"]["temp"],
                "humidity": res["main"]["humidity"],
                "desc": res["weather"][0]["description"]
            }

            advice = chatbot(weather["temp"], weather["desc"])

        # 📊 Forecast
        f_url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
        f_res = requests.get(f_url).json()

        if f_res.get("cod") == "200" and "list" in f_res:
            forecast = []

            for i in range(0, 40, 8):
                day = f_res["list"][i]
                forecast.append({
                    "temp": day["main"]["temp"],
                    "desc": day["weather"][0]["description"]
                })

            for i in range(len(forecast)):
                temps.append(forecast[i]["temp"])
                labels.append(f"Day {i+1}")

    return render_template("index.html",
                           weather=weather,
                           forecast=forecast,
                           temps=temps,
                           labels=labels,
                           map_url=map_url,
                           advice=advice)

# 🔐 Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "1234":
            session["user"] = "admin"
            return redirect("/")
    return render_template("login.html")

# 🔓 Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

app.run(debug=True)