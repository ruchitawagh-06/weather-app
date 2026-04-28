from flask import Flask, render_template, request, jsonify, redirect, session
import requests, os

app = Flask(__name__)
app.secret_key = "secret123"

API_KEY = os.environ.get("API_KEY")  # OpenWeather key

# ================= HOME =================
@app.route("/", methods=["GET", "POST"])
def home():

    weather = None
    forecast = None
    temps = []
    labels = []

    if request.method == "POST":
        city = request.form.get("city")

        # CURRENT WEATHER
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        res = requests.get(url).json()

        if str(res.get("cod")) == "200":
            weather = {
                "city": city,
                "temp": res["main"]["temp"],
                "desc": res["weather"][0]["description"],
                "lat": res["coord"]["lat"],   # IMPORTANT
                "lon": res["coord"]["lon"]    # IMPORTANT
            }

        # FORECAST (5 days)
        f_url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
        f_res = requests.get(f_url).json()

        if str(f_res.get("cod")) == "200":
            forecast = []

            # Pick every 8th item (~1 per day)
            for i in range(0, 40, 8):
                item = f_res["list"][i]

                forecast.append({
                    "temp": item["main"]["temp"],
                    "desc": item["weather"][0]["description"]
                })

                temps.append(item["main"]["temp"])
                labels.append(f"Day {len(labels)+1}")

    return render_template(
        "index.html",
        weather=weather,
        forecast=forecast,
        temps=temps,
        labels=labels,
        api_key=API_KEY   # for map layers
    )


# ================= LOCATION =================
@app.route("/location")
def location():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    res = requests.get(url).json()

    return jsonify({
        "city": res.get("name"),
        "temp": res["main"]["temp"],
        "desc": res["weather"][0]["description"]
    })


# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
