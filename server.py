import os
import json
from flask import Flask, request, jsonify
from bson import json_util, ObjectId, Binary
from pymongo import MongoClient
from bcrypt import gensalt, hashpw, checkpw
from dotenv import load_dotenv

load_dotenv()
# Environment
database_url = os.getenv("DATABASE_URL")
cluster_name = os.getenv("MONGODB_CLUSTER")

# db connection
cluster = MongoClient(database_url)
db = getattr(cluster, cluster_name)
users_collection = db["users"]

app = Flask(__name__)

# No in use yet


def parse_json(data):
    return json.loads(json_util.dumps(data))

# # Convert BSON data to Python dictionary using json_util
# data_python = json_util.loads(json_util.dumps(data_bson))

# # Serialize Python dictionary to JSON response using jsonify()
# response = jsonify(data_python)


class Users:
    @app.route('/users', methods=['GET'])
    # Add the fields you want returned into the pipeline -ex: "email": 1
    def get_users():
        pipeline = [
            {"$project": {"_id": {"$toString": "$_id"}, "name": 1}}
        ]
        users = list(users_collection.aggregate(pipeline))
        return jsonify({"users": users})

    @app.route('/registration', methods=['POST'])
    def register_user():
        data = request.get_json()

        email = data["email"].lower().strip()  # format email
        plaintext_password = data["password"]

        # Check if existing email
        user_exists = users_collection.find_one({"email": email})

        if user_exists:
            return jsonify({"message": "Email already exists. Please login."})

        # Hash the password and add a salt
        encoded_password = plaintext_password.encode('utf-8')

        salt = gensalt()
        hashed_password = hashpw(
            encoded_password, salt)

        decoded_password = hashed_password.decode("utf-8")

        users_collection.insert_one({
            'email': email,
            'hashed_password': decoded_password,
            'salt': salt
        })
        return jsonify({"message": "User created successfully"})

    # Make login route
    @app.route('/login', methods=['POST'])
    def login():
        data = request.get_json()
        email = data["email"].lower()
        plaintext_password = data["password"]

        user = users_collection.find_one({"email": email})

        if not user:
            return jsonify({"message": "Email does not exist. Please register for an account!"})

        stored_hashed_password = user.get("hashed_password")
        stored_salt = user.get("salt")

        # Hash the provided password using the retrieved salt
        # https://stackoverflow.com/questions/63229401/invalit-salt-in-bcrypt-when-i-checkpw
        hashed_password_attempt = hashpw(
            plaintext_password.encode('utf-8'), stored_salt)

        if checkpw(hashed_password_attempt, stored_hashed_password.encode("utf-8")):
            return jsonify({"message": "You've successfully logged in!"})
        else:
            return jsonify({"message": "Sorry, you failed to login!"})

    @app.route('/users/<user_id>', methods=['GET'])
    def get_user(user_id):
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if user:
            user['_id'] = str(user['_id'])
            return jsonify({"user": user})
        else:
            return jsonify({"message": "User not found"})

    @app.route('/users/<user_id>', methods=['PUT'])
    def update_user(user_id):
        data = request.get_json()
        users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": data})
        return jsonify({"message": "User updated successfully"})

    @app.route('/users/<user_id>', methods=['DELETE'])
    def delete_user(user_id):
        result = users_collection.delete_one({"_id": ObjectId(user_id)})
        if result.deleted_count == 1:
            return jsonify({"message": "User deleted successfully"})
        else:
            return jsonify({"message": "User not found"})


if __name__ == "__main__":
    app.run(debug=True)
