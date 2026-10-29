"""MongoDB connection, validators, and indexes."""

from pymongo import MongoClient
from pymongo.database import Database

from config import DB_NAME, MONGO_URI

VALIDATORS = {
    "farmers": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["name", "phone", "land_acres", "address", "registered_on"],
            "properties": {
                "name": {"bsonType": "string", "minLength": 2},
                "phone": {"bsonType": "string", "pattern": "^[0-9]{10}$"},
                "land_acres": {"bsonType": ["double", "int", "long", "decimal"], "minimum": 0.1},
                "address": {
                    "bsonType": "object",
                    "required": ["village", "district"],
                    "properties": {
                        "village": {"bsonType": "string"},
                        "district": {"bsonType": "string"},
                        "pincode": {"bsonType": "string", "pattern": "^[0-9]{6}$"},
                    },
                },
                "bank": {"bsonType": "object"},
                "registered_on": {"bsonType": "date"},
            },
        }
    },
    "mandis": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["name", "district", "commodities"],
            "properties": {
                "name": {"bsonType": "string", "minLength": 2},
                "district": {"bsonType": "string"},
                "commodities": {"bsonType": "array", "minItems": 1, "items": {"bsonType": "string"}},
                "facilities": {"bsonType": "array", "items": {"bsonType": "string"}},
            },
        }
    },
    "sales": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "farmer_id", "mandi_id", "crop", "quantity_quintals",
                "rate_per_quintal", "total_amount", "sale_date",
            ],
            "properties": {
                "farmer_id": {"bsonType": "objectId"},
                "mandi_id": {"bsonType": "objectId"},
                "crop": {
                    "bsonType": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {"enum": ["Wheat", "Paddy", "Maize", "Cotton", "Sugarcane", "Mustard"]},
                        "variety": {"bsonType": "string"},
                        "quality_grade": {"enum": ["A", "B", "C"]},
                    },
                },
                "quantity_quintals": {"bsonType": ["double", "int", "long", "decimal"], "minimum": 0.01},
                "rate_per_quintal": {"bsonType": ["double", "int", "long", "decimal"], "minimum": 0.01},
                "total_amount": {"bsonType": ["double", "int", "long", "decimal"], "minimum": 0},
                "sale_date": {"bsonType": "date"},
                "payment_status": {"enum": ["Paid", "Pending"]},
            },
        }
    },
}


def get_db() -> Database:
    """Connect to MongoDB, verify connectivity, and return the application database."""
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    client.admin.command("ping")
    db = client[DB_NAME]
    setup_collections(db)
    return db


def setup_collections(db: Database) -> None:
    """Create or update validated collections and their indexes idempotently."""
    existing = set(db.list_collection_names())
    for name, validator in VALIDATORS.items():
        if name not in existing:
            db.create_collection(name, validator=validator, validationLevel="strict", validationAction="error")
        else:
            db.command("collMod", name, validator=validator, validationLevel="strict", validationAction="error")
    db.farmers.create_index("phone", unique=True, name="uq_farmer_phone")
    db.farmers.create_index([("address.district", 1), ("address.village", 1)])
    db.mandis.create_index("name", unique=True, name="uq_mandi_name")
    db.sales.create_index([("crop.name", 1), ("sale_date", -1)])
    db.sales.create_index("farmer_id")
    db.sales.create_index("mandi_id")


def reset_database(db: Database) -> None:
    """Drop the three application collections and recreate their validators."""
    for name in VALIDATORS:
        db.drop_collection(name)
    setup_collections(db)

