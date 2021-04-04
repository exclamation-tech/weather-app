import sys
import requests
import os

from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
app.secret_key = "9AB956&7pi3!DgsFjc33"
db = SQLAlchemy(app)

app_id = os.environ.get("API_KEY")
weather_api_url = "http://api.openweathermap.org/data/2.5/weather"


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return self.name


db.create_all()


def use_weather_api(new_city):
    r = requests.get(weather_api_url, params={"q": f"{new_city},", "appid": app_id, "units": "metric"})
    data = r.json()
    if data["dt"] > (data["sys"]["sunset"] + 3600) or data["dt"] < (data["sys"]["sunrise"] - 3600):
        time = "night"
    elif (data["dt"] < data["sys"]["sunset"] + 3600) and (data["dt"] > data["sys"]["sunset"] - 3600) or (
            data["dt"] < data["sys"]["sunrise"] + 3600) and (data["dt"] > data["sys"]["sunrise"] - 3600):
        time = "evening-morning"
    else:
        time = "day"
    weather_data = {
        "city": new_city,
        "temp": round(data["main"]["temp"]),
        "state": data["weather"][0]["description"],
        "time": time
    }
    return weather_data


@app.route('/delete/<city_name>', methods=['POST'])
def delete(city_name):
    city = City.query.filter_by(name=city_name).first()
    db.session.delete(city)
    db.session.commit()
    return redirect('/')


@app.route('/add', methods=['POST'])
def add_city():
    new_city = City(name=request.form["city_name"].title())
    r = requests.get(weather_api_url, params={"q": f"{new_city},", "appid": app_id})
    if r:
        try:
            db.session.add(new_city)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("The city has already been added to the list!")
    else:
        flash("The city doesn't exist!")
    return redirect('/')


@app.route('/', methods=['POST', 'GET'])
def index():
    weather_data = []

    for city in City.query.all():
        weather_data.append(use_weather_api(str(city)))

    return render_template("index.html", weather=weather_data)


# don't change the following way to run flask:
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
