import os
from flask import Flask, request, jsonify, g
from flask_pymongo import PyMongo
from flask_dance.consumer import OAuth2ConsumerBlueprint
from ldap3 import Server, Connection, ALL
import bcrypt
import jwt
from functools import wraps
from datetime import datetime

app = Flask(__name__)

app.config["MONGO_URI"] = "mongodb://localhost:27017/mydatabase"
app.config["SECRET_KEY"] = "your_jwt_secret_key"

mongo = PyMongo(app)
users_collection = mongo.db.users
communities_collection = mongo.db.communities

# JWT Token Authentication
def authenticate_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        if not token:
            return jsonify({"error": "Missing token"}), 401
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            user = users_collection.find_one({"_id": data["user_id"]})
            if not user:
                raise Exception("User not found")
            g.user = user
        except Exception as e:
            return jsonify({"error": "Invalid token"}), 403
        return f(*args, **kwargs)
    return decorated

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

def generate_token(user_id):
    return jwt.encode({"user_id": user_id}, app.config["SECRET_KEY"], algorithm="HS256")

# User registration
@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    email = data.get("email")

    # Check if the email ends with @cuchd.in
    if not email.endswith("@cuchd.in"):
        return jsonify({"error": "Invalid Credentials"}), 400

    hashed_password = hash_password(data["password"])
    user_id = users_collection.insert_one({
        "name": data["name"],
        "email": email,
        "password": hashed_password
    }).inserted_id
    return jsonify({"message": "User created", "user_id": str(user_id)})

# User login
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    # Check if the email ends with @cuchd.in
    if not email.endswith("@cuchd.in"):
        return jsonify({"error": "Invalid Credentials"}), 400

    user = users_collection.find_one({"email": email})
    if user and verify_password(password, user["password"]):
        token = generate_token(user["_id"])
        return jsonify({"token": token})
    return jsonify({"error": "Invalid credentials"}), 401

# Create a community
@app.route("/communities", methods=["POST"])
@authenticate_token
def create_community():
    data = request.get_json()
    community_id = communities_collection.insert_one({
        "name": data["name"],
        "createdBy": g.user["email"],
        "createdAt": datetime.utcnow()
    }).inserted_id
    return jsonify({"message": "Community created", "community_id": str(community_id)})

# Get all communities
@app.route("/communities", methods=["GET"])
@authenticate_token
def get_communities():
    communities = list(communities_collection.find())
    return jsonify(communities)

# Start the Flask app
if __name__ == "__main__":
    app.run(debug=True)
