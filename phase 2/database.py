import uuid
from pymongo import MongoClient
import config


client = MongoClient(config.MONGO_URI)
db = client[config.MONGO_DB]

rules_col = db["construction_rules"]
logs_col = db["comparison_logs"]


# --- Rules ---

def insert_rules(rules):
    if not rules:
        return 0
    rules_col.insert_many(rules)
    return len(rules)

def get_all_rules():
    return list(rules_col.find({}, {"_id": 0}))

def find_by_category(category):
    return list(rules_col.find({"category": {"$regex": category, "$options": "i"}}, {"_id": 0}))

def find_by_categories(categories):
    pattern = "|".join(categories)
    return list(rules_col.find({"category": {"$regex": pattern, "$options": "i"}}, {"_id": 0}))

def get_categories():
    return sorted(rules_col.distinct("category"))

def clear_rules():
    rules_col.delete_many({})


# --- Logs ---

def log_comparison(entry):
    entry["log_id"] = str(uuid.uuid4())
    logs_col.insert_one(entry)
    return entry["log_id"]

def get_logs():
    return list(logs_col.find({}, {"_id": 0}))
