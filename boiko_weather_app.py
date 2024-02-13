import datetime as dt
import json

import requests
from flask import Flask, jsonify, request

# create your API token, and set it up in Postman collection as part of the Body section
API_TOKEN = ""
# you can get API keys for free here - https://www.visualcrossing.com/weather-api
RSA_KEY = ""

app = Flask(__name__)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


def get_weather_info(location: str, date: str):
    url_base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
    url = f"{url_base_url}/{location}/{date}"
    
    params = {
        "unitGroup": "metric",
        "elements": "datetime,name,tempmax,tempmin,temp,humidity,windspeed,winddir,pressure,cloudcover",
        "include": "days",
        "key": RSA_KEY,
        "contentType": "json"
    }
    
    response = requests.get(url, params=params)

    if response.status_code == requests.codes.ok:
        return json.loads(response.text)
    else:
        raise InvalidUsage(response.text, status_code=response.status_code)


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def home_page():
    return "<p><h2>KMA L2: python weather SaaS.</h2></p>"


@app.route("/content/api/v1/integration/weather", methods=["POST"])
def weather_endpoint():
    json_data = request.get_json()
    
    if json_data.get("token") is None:
        raise InvalidUsage("token is required", status_code=400)
    
    token = json_data.get("token")
    
    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)
    
    requester_name = ""
    if json_data.get("requester_name"):
        requester_name = json_data.get("requester_name")

    location = ""
    if json_data.get("location"):
        location = json_data.get("location")

    date = ""
    if json_data.get("date"):
        date = json_data.get("date")
        
    weather_info = get_weather_info(location, date)
    weather_data = weather_info['days'][0]
    
    temp = weather_data['temp']
    temp_min = weather_data['tempmin']
    temp_max = weather_data['tempmax']
    humidity = weather_data['humidity']
    windspeed = weather_data['windspeed']
    winddir = weather_data['winddir']
    pressure = weather_data['pressure']
    cloudcover = weather_data['cloudcover']
    
    weather_result = {
        "temp_c": temp,
        "temp_min_c": temp_min,
        "temp_max_c": temp_max,
        "humidity": humidity,
        "windspeed": windspeed,
        "winddirection": winddir,
        "pressure": pressure,
        "cloudcover": cloudcover
    }

    timestamp = dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    result = {
        "requester_name": requester_name,
        "timestamp": timestamp,
        "location": location,
        "date": date,
        "weather": weather_result
    }

    return result
