from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# Google API key - bunu kendi anahtarınla değiştir
GOOGLE_API_KEY = "AIzaSyDkBvNWG5Us1s8UAncf1VNYsXm2I8GCjeg"

user_places = []

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/user_places", methods=["POST"])
def add_user_place():
    data = request.get_json()
    user_places.append(data)
    return jsonify({"message": "Yer eklendi", "place": data})

@app.route("/api/user_places", methods=["GET"])
def get_user_places():
    return jsonify(user_places)

@app.route("/api/public_places", methods=["GET"])
def get_public_places():
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = """
    [out:json][timeout:25];
    (
      node["wheelchair"="yes"](39.9,32.8,40.0,32.9);
    );
    out body;
    """
    try:
        response = requests.get(overpass_url, params={'data': query})
        data = response.json()

        places = []
        for idx, element in enumerate(data.get("elements", []), start=1):
            name = element.get("tags", {}).get("name", "İsimsiz Mekan")
            lat = element.get("lat")
            lon = element.get("lon")
            places.append({
                "id": idx,
                "name": name,
                "lat": lat,
                "lon": lon,
                "accessible": True
            })
        return jsonify(places)
    except Exception as e:
        return jsonify({"error": "Veri çekilemedi", "details": str(e)}), 500

def get_google_accessible_places(lat, lon, radius=5000):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lon}",
        "radius": radius,
        "keyword": "wheelchair accessible",
        "key": GOOGLE_API_KEY
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        results = response.json().get("results", [])
        places = []
        for idx, place in enumerate(results, start=1):
            places.append({
                "id": idx,
                "name": place.get("name"),
                "lat": place["geometry"]["location"]["lat"],
                "lon": place["geometry"]["location"]["lng"],
                "address": place.get("vicinity"),
                "accessible": True
            })
        return places
    else:
        return []

@app.route("/api/google_places", methods=["GET"])
def google_places():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    radius = request.args.get("radius", default=5000, type=int)

    if lat is None or lon is None:
        return jsonify({"error": "lat ve lon parametreleri gerekli"}), 400

    places = get_google_accessible_places(lat, lon, radius)
    return jsonify(places)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
