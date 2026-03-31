from pymongo import MongoClient
from config import Config

client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]

# Collections
pincode_collection = db["pincodes"]

def get_by_pincode(pincode):
    """Fetch all records matching a PIN code"""
    return list(pincode_collection.find({"Pincode": int(pincode)}, {"_id": 0}))

def get_by_district(district):
    """Fetch all records matching a district name"""
    return list(pincode_collection.find(
        {"District": {"$regex": district, "$options": "i"}},
        {"_id": 0}
    ))

def get_by_state(state):
    """Fetch all records matching a state name"""
    return list(pincode_collection.find(
        {"StateName": {"$regex": state, "$options": "i"}},
        {"_id": 0}
    ))