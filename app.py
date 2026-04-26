from flask import Flask, render_template, request, redirect, session
import requests
import os

app = Flask(__name__)
app.secret_key = "1234"
API_KEY = os.environ.get("API_KEY") # 🔐 safer for deployment


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
            # 🌦 Current weather
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
            else:
                error = "❌ City not found"

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

        except Exception as e:
            print("ERROR:", e)
            error = "⚠ Something went wrong"

    return render_template("index.html",
                           weather=weather,
                           forecast=forecast,
                           temps=temps,
                           labels=labels,
                           advice=advice,
                           error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == "admin" and request.form.get("password") == "1234":
            session["user"] = "admin"
            return redirect("/")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


# 🚀 Render compatible
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
