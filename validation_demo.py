"""Demonstrate MongoDB schema validation and unique indexes."""

from datetime import datetime
from pymongo.errors import DuplicateKeyError, WriteError
from pymongo.database import Database


def run_validation_tests(db: Database) -> None:
    """Attempt representative invalid documents and report expected outcomes."""
    farmer = db.farmers.find_one()
    tests = [
        ("bad phone", {"name": "Test Farmer", "phone": "12345", "land_acres": 2,
                       "address": {"village": "Demo", "district": "Demo"}, "registered_on": datetime.utcnow()}),
        ("negative land", {"name": "Test Farmer", "phone": "9876543210", "land_acres": -2,
                           "address": {"village": "Demo", "district": "Demo"}, "registered_on": datetime.utcnow()}),
        ("missing name", {"phone": "9876543211", "land_acres": 2,
                          "address": {"village": "Demo", "district": "Demo"}, "registered_on": datetime.utcnow()}),
        ("duplicate phone", {"name": "Duplicate", "phone": farmer["phone"], "land_acres": 2,
                             "address": {"village": "Demo", "district": "Demo"}, "registered_on": datetime.utcnow()}),
    ]
    for label, document in tests:
        try:
            db.farmers.insert_one(document)
            print(f"FAIL - {label}: document was accepted")
        except (DuplicateKeyError, WriteError) as exc:
            print(f"PASS - {label}: rejected ({exc.__class__.__name__})")

