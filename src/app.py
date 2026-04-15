import os
from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planet, Favorite
import requests
from requests.exceptions import RequestException

app = Flask(__name__)
app.url_map.strict_slashes = False

# Configuración de DB
db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

@app.route('/')
def sitemap():
    return generate_sitemap(app)

# --- GET ENDPOINTS (Listar y detalle) ---

@app.route('/people', methods=['GET'])
def get_all_people():
    people = People.query.all()
    return jsonify([p.serialize() for p in people]), 200

@app.route('/people/<int:people_id>', methods=['GET'])
def get_one_person(people_id):
    person = People.query.get(people_id)
    if not person: return jsonify({"msg": "Person not found"}), 404
    return jsonify(person.serialize()), 200

@app.route('/planets', methods=['GET'])
def get_all_planets():
    planets = Planet.query.all()
    return jsonify([p.serialize() for p in planets]), 200

@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_one_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if not planet: return jsonify({"msg": "Planet not found"}), 404
    return jsonify(planet.serialize()), 200

@app.route('/users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    return jsonify([u.serialize() for u in users]), 200

@app.route('/users/favorites', methods=['GET'])
def get_user_favorites():
    # Asumimos usuario 1 por defecto (sin auth)
    favs = Favorite.query.filter_by(user_id=1).all()
    return jsonify([f.serialize() for f in favs]), 200

# --- FAVORITES ENDPOINTS (POST y DELETE) ---

@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_fav_planet(planet_id):
    new_fav = Favorite(user_id=1, planet_id=planet_id)
    db.session.add(new_fav)
    db.session.commit()
    return jsonify({"msg": "Planet added"}), 201

@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_fav_person(people_id):
    new_fav = Favorite(user_id=1, people_id=people_id)
    db.session.add(new_fav)
    db.session.commit()
    return jsonify({"msg": "Person added"}), 201

@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def del_fav_planet(planet_id):
    fav = Favorite.query.filter_by(user_id=1, planet_id=planet_id).first()
    if not fav: return jsonify({"msg": "Not found"}), 404
    db.session.delete(fav)
    db.session.commit()
    return jsonify({"msg": "Deleted"}), 200

@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def del_fav_person(people_id):
    fav = Favorite.query.filter_by(user_id=1, people_id=people_id).first()
    if not fav: return jsonify({"msg": "Not found"}), 404
    db.session.delete(fav)
    db.session.commit()
    return jsonify({"msg": "Deleted"}), 200

# --- POPULATION ENDPOINTS (Para llenar tu base de datos) ---

@app.route("/people/population", methods=["POST"])
def people_population():
    url = "https://www.swapi.tech/api/people?page=1&limit=83"
    try:
        response = requests.get(url, timeout=15).json()
        for item in response.get("results", []):
            det = requests.get(item["url"]).json()["result"]["properties"]
            if not People.query.filter_by(name=det["name"]).first():
                new_p = People(name=det["name"], height=det["height"], mass=det["mass"], gender=det["gender"], birth_year=det["birth_year"])
                db.session.add(new_p)
        db.session.commit()
        return jsonify({"msg": "People populated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/planets/population", methods=["POST"])
def planets_population():
    url = "https://swapi.tech"
    try:
        response = requests.get(url, timeout=15).json()
        for item in response.get("results", []):
            det = requests.get(item["url"]).json()["result"]["properties"]
            if not Planet.query.filter_by(name=det["name"]).first():
                new_pl = Planet(name=det["name"], climate=det["climate"], terrain=det["terrain"], population=det["population"])
                db.session.add(new_pl)
        db.session.commit()
        return jsonify({"msg": "Planets populated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=True)