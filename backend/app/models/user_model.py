from bson import ObjectId
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]
users_collection = db["users"]

users_collection.create_index("email", unique=True)


def serialize_user(user):
    return {
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
    }


def create_user(name, email, password):
    doc = {
        "name": name.strip(),
        "email": email.strip().lower(),
        "password_hash": generate_password_hash(password),
    }
    result = users_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return serialize_user(doc)


def get_user_by_email(email):
    if not email:
      return None
    return users_collection.find_one({"email": email.strip().lower()})


def get_user_by_id(user_id):
    try:
        return users_collection.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None


def verify_user_password(user, password):
    return check_password_hash(user.get("password_hash", ""), password)
