from pymongo import MongoClient
from config import Config

client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]

pincode_collection = db["pincodes"]

def create_indexes():
    pincode_collection.create_index("pincode")
    pincode_collection.create_index("district")
    pincode_collection.create_index("statename")
    pincode_collection.create_index("circlename")
    pincode_collection.create_index("regionname")
    pincode_collection.create_index("divisionname")

def get_by_pincode(pincode):
    return list(pincode_collection.find(
        {"pincode": int(pincode)}, {"_id": 0}
    ))

def get_by_state(state):
    return list(pincode_collection.find(
        {"statename": {"$regex": state, "$options": "i"}},
        {"_id": 0}
    ))

def get_by_district(district):
    return list(pincode_collection.find(
        {"district": {"$regex": district, "$options": "i"}},
        {"_id": 0}
    ))

def get_by_circle(circle):
    return list(pincode_collection.find(
        {"circlename": {"$regex": circle, "$options": "i"}},
        {"_id": 0}
    ))

def get_by_state_and_district(state, district):
    return list(pincode_collection.find(
        {
            "statename": {"$regex": state, "$options": "i"},
            "district": {"$regex": district, "$options": "i"}
        },
        {"_id": 0}
    ))

def get_by_state_and_circle(state, circle):
    return list(pincode_collection.find(
        {
            "statename": {"$regex": state, "$options": "i"},
            "circlename": {"$regex": circle, "$options": "i"}
        },
        {"_id": 0}
    ))

def get_by_state_district_division(state, district, division):
    return list(pincode_collection.find(
        {
            "statename": {"$regex": state, "$options": "i"},
            "district": {"$regex": district, "$options": "i"},
            "divisionname": {"$regex": division, "$options": "i"}
        },
        {"_id": 0}
    ))

def get_post_offices_by_pincode(pincode):
    return list(pincode_collection.find(
        {"pincode": int(pincode)},
        {"_id": 0, "officename": 1, "officetype": 1, "delivery": 1}
    ))


def get_nearby_pincodes(lat, lng, radius_deg=0.15, limit=20):
    """Find unique PIN codes near given coordinates.
    radius_deg ~0.15 is roughly 15-17km."""
    pipeline = [
        {"$match": {
            "latitude": {"$gte": lat - radius_deg, "$lte": lat + radius_deg},
            "longitude": {"$gte": lng - radius_deg, "$lte": lng + radius_deg},
        }},
        {"$group": {
            "_id": "$pincode",
            "pincode": {"$first": "$pincode"},
            "officename": {"$first": "$officename"},
            "district": {"$first": "$district"},
            "latitude": {"$first": "$latitude"},
            "longitude": {"$first": "$longitude"},
            "delivery": {"$first": "$delivery"},
        }},
        {"$limit": limit}
    ]
    return list(pincode_collection.aggregate(pipeline))