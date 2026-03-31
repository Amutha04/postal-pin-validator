from pymongo import MongoClient
from config import Config

client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]

# Collections
pincode_collection = db["pincodes"]

def create_indexes():
    """Create indexes for faster lookups"""
    pincode_collection.create_index("pincode")
    pincode_collection.create_index("district")
    pincode_collection.create_index("statename")

def get_by_pincode(pincode):
    """Fetch all records matching a PIN code"""
    return list(pincode_collection.find(
        {"pincode": int(pincode)},
        {"_id": 0}
    ))

def get_by_district(district):
    """Fetch all records matching a district name"""
    return list(pincode_collection.find(
        {"district": {"$regex": district, "$options": "i"}},
        {"_id": 0}
    ))

def get_by_state(state):
    """Fetch all records matching a state name"""
    return list(pincode_collection.find(
        {"statename": {"$regex": state, "$options": "i"}},
        {"_id": 0}
    ))

def get_post_offices_by_pincode(pincode):
    """Fetch all post offices for a PIN code"""
    return list(pincode_collection.find(
        {"pincode": int(pincode)},
        {"_id": 0, "officename": 1, "officetype": 1, "delivery": 1}
    ))