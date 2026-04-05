"""Import postal dataset CSV into MongoDB.

Usage:
    python scripts/import_data.py [path_to_csv]

If no path is given, looks for dataset/india_postal.csv
Downloads the dataset automatically if not found.
"""
import csv
import sys
import os
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from pymongo import MongoClient
from config import Config

DATASET_URL = "https://raw.githubusercontent.com/dropdevrahul/pincodes-india/main/pincode.csv"
DEFAULT_CSV = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'india_postal.csv')


def download_dataset(path):
    """Download India postal dataset if not present"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print(f"Downloading dataset from {DATASET_URL}...")
    urllib.request.urlretrieve(DATASET_URL, path)
    print(f"Downloaded to {path}")


def import_data(csv_path):
    client = MongoClient(Config.MONGO_URI)
    db = client[Config.DB_NAME]
    collection = db["pincodes"]

    # Drop existing data for clean import
    collection.drop()

    records = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        # Normalize headers to lowercase
        reader.fieldnames = [h.lower() for h in reader.fieldnames]

        for row in reader:
            try:
                row['pincode'] = int(row['pincode'])
            except (ValueError, KeyError):
                continue
            for field in ['latitude', 'longitude']:
                try:
                    row[field] = float(row[field]) if row.get(field) else None
                except (ValueError, TypeError):
                    row[field] = None
            records.append(row)

            if len(records) == 10000:
                collection.insert_many(records)
                print(f"  Inserted {collection.count_documents({})} records...")
                records = []

    if records:
        collection.insert_many(records)

    total = collection.count_documents({})
    print(f"Done! Total records: {total}")

    collection.create_index("pincode")
    collection.create_index("district")
    collection.create_index("statename")
    collection.create_index("circlename")
    collection.create_index("regionname")
    collection.create_index("divisionname")
    print("Indexes created.")


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV

    if not os.path.exists(csv_path):
        download_dataset(csv_path)

    import_data(csv_path)
