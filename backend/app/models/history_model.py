from datetime import datetime, timezone
from bson import ObjectId
from pymongo import MongoClient
from config import Config

client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]
history_collection = db["validation_history"]

history_collection.create_index([("user_id", 1), ("created_at", -1)])


def serialize_history(doc):
    return {
        "id": str(doc["_id"]),
        "date": doc.get("date", ""),
        "time": doc.get("time", ""),
        "source": doc.get("source", ""),
        "filename": doc.get("filename", "-"),
        "status": doc.get("status", ""),
        "pincode": doc.get("pincode", "-"),
        "district": doc.get("district", "-"),
        "state": doc.get("state", "-"),
        "suggestion": doc.get("suggestion", "-"),
        "message": doc.get("message", ""),
        "ocr_engine": doc.get("ocr_engine", "-"),
    }


def list_history(user_id, limit=250):
    docs = history_collection.find(
        {"user_id": str(user_id)}
    ).sort("created_at", -1).limit(limit)
    return [serialize_history(doc) for doc in docs]


def add_history(user_id, row):
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": str(user_id),
        "date": row.get("date", now.date().isoformat()),
        "time": row.get("time", ""),
        "source": row.get("source", ""),
        "filename": row.get("filename", "-"),
        "status": row.get("status", ""),
        "pincode": row.get("pincode", "-"),
        "district": row.get("district", "-"),
        "state": row.get("state", "-"),
        "suggestion": row.get("suggestion", "-"),
        "message": row.get("message", ""),
        "ocr_engine": row.get("ocr_engine", "-"),
        "created_at": now,
    }
    result = history_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return serialize_history(doc)


def clear_history(user_id):
    history_collection.delete_many({"user_id": str(user_id)})
