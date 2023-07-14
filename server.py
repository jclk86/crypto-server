import os
import json
from flask import Flask, request, jsonify
from bson import json_util, ObjectId
import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")
cluster_name = os.getenv("MONGODB_CLUSTER")

cluster = MongoClient(database_url)
db = getattr(cluster, cluster_name)
collection = db["users"]

app = Flask(__name__)


def parse_json(data):
    return json.loads(json_util.dumps(data))


class Users:
    @staticmethod
    @app.route('/users', methods=['GET'])
    # Add the fields you want returned into the pipeline -ex: "email": 1
    def get_users():
        pipeline = [
            {"$project": {"_id": {"$toString": "$_id"}, "name": 1}}
        ]
        users = list(collection.aggregate(pipeline))
        return jsonify({"users": users})

    @staticmethod
    @app.route('/users', methods=['POST'])
    def create_user():
        data = request.get_json()
        collection.insert_one(data)
        return jsonify({"message": "User created successfully"})

    @staticmethod
    @app.route('/users/<user_id>', methods=['GET'])
    def get_user(user_id):
        user = collection.find_one({"_id": ObjectId(user_id)})
        if user:
            user['_id'] = str(user['_id'])
            return jsonify({"user": user})
        else:
            return jsonify({"message": "User not found"})

    @staticmethod
    @app.route('/users/<user_id>', methods=['PUT'])
    def update_user(user_id):
        data = request.get_json()
        collection.update_one({"_id": ObjectId(user_id)}, {"$set": data})
        return jsonify({"message": "User updated successfully"})

    @staticmethod
    @app.route('/users/<user_id>', methods=['DELETE'])
    def delete_user(user_id):
        result = collection.delete_one({"_id": ObjectId(user_id)})
        if result.deleted_count == 1:
            return jsonify({"message": "User deleted successfully"})
        else:
            return jsonify({"message": "User not found"})


if __name__ == "__main__":
    app.run(debug=True)