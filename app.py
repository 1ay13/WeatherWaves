import requests
import string
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'thisisasecret'
db = SQLAlchemy(app)


class City(db.Model) :
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50),nullable=False)

def get_weather_data(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid=b21a2633ddaac750a77524f91fe104e7"
    r = requests.get(url).json()
    return r

@app.route('/')
def index_get():
    cities = City.query.all()

    weather_data = []

    for city in cities:
        r = get_weather_data(city.name)
        print(r)
        timestamp = r['dt']
        dt_object = datetime.utcfromtimestamp(timestamp)
        weather = {
            'city' : city.name,
            'temperature' : r['main']['temp'],
            'main': r['weather'][0]['main'],
            'description' : r['weather'][0]['description'],
            'icon' : r['weather'][0]['icon'],
            'Feels_like' : r['main']['feels_like'],
            'temperature_min': r['main']['temp_min'],
            'temperature_max': r['main']['temp_max'],
            'pressure': r['main']['pressure'],
            'humidity': r['main']['humidity'],
            'wind_speed': r['wind']['speed'],
            'wind_dir': r['wind']['deg'],
            'lat': r['coord']['lat'],
            'lon': r['coord']['lon'],
            'timestamp': dt_object
        }
        weather_data.append(weather)

    return render_template('weather.html', weather_data=weather_data)

@app.route('/', methods=['POST'])
def index_post():
    err_msg = ''
    new_city = request.form.get('city')
    new_city = new_city.lower()
    new_city = string.capwords(new_city)
    if new_city:
        existing_city = City.query.filter_by(name=new_city).first()
        
        if not existing_city:
            new_city_data = get_weather_data(new_city)
            if new_city_data['cod'] == 200:
                new_city_obj = City(name=new_city)

                db.session.add(new_city_obj)
                db.session.commit()
            else:
                err_msg = 'That is not a valid city!'
        else:
            err_msg = 'City already exists in the database!'

    if err_msg:
        flash(err_msg, 'error')
    else:
        flash('City added successfully!', 'success')

    return redirect(url_for('index_get'))

@app.route('/delete/<name>')
def delete_city( name ):
    city = City.query.filter_by(name=name).first()
    db.session.delete(city)
    db.session.commit()

    flash(f'Successfully deleted { city.name }!', 'success')
    return redirect(url_for('index_get'))

@app.route('/city/<name>')
def city_weather(name):
    city = City.query.filter_by(name=name).first()
    if not city:
        flash('City not found!', 'error')
        return redirect(url_for('index_get'))

    weather_data = get_weather_data(city.name)

    if weather_data['cod'] == 200:
        timestamp = weather_data['dt']
        dt_object = datetime.utcfromtimestamp(timestamp)
        weather = {
            'city': city.name,
            'main': weather_data['weather'][0]['main'],
            'temperature': weather_data['main']['temp'],
            'description': weather_data['weather'][0]['description'],
            'icon': weather_data['weather'][0]['icon'],
            'Feels_like': weather_data['main']['feels_like'],
            'temperature_min': weather_data['main']['temp_min'],
            'temperature_max': weather_data['main']['temp_max'],
            'pressure': weather_data['main']['pressure'],
            'humidity': weather_data['main']['humidity'],
            'wind_speed': weather_data['wind']['speed'],
            'wind_dir': weather_data['wind']['deg'],
            'lat': weather_data['coord']['lat'],
            'lon': weather_data['coord']['lon'],
            'timestamp': dt_object,
        }
    else:
        flash('Failed to retrieve weather data for the city!', 'error')
        return redirect(url_for('index_get'))

    return render_template('city_weather.html', weather=weather)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        app.run(debug=True,host='localhost', port=5300)