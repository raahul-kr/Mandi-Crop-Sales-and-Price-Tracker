"""Repeatable, original sample data for demonstrations."""

import random
from datetime import datetime, timedelta

from pymongo.database import Database

from db import reset_database


def seed_all(db: Database) -> None:
    """Reset collections and insert 12 mandis, 30 farmers, and 90 sales."""
    reset_database(db)
    random.seed(42)
    districts = ["Ludhiana", "Khanna", "Jagraon", "Amritsar", "Patiala", "Bathinda",
                 "Sangrur", "Moga", "Jalandhar", "Ferozepur", "Barnala", "Mansa"]
    crops = ["Wheat", "Paddy", "Maize", "Cotton", "Sugarcane", "Mustard"]
    facilities = ["Weighing Bridge", "Cold Storage", "Drinking Water", "Rest Area", "Digital Auction"]
    mandi_docs = [{"name": f"{d} Harvest Hub", "district": d,
                   "commodities": random.sample(crops, random.randint(2, 4)),
                   "facilities": random.sample(facilities, random.randint(2, 4))} for d in districts]
    db.mandis.insert_many(mandi_docs)
    first = ["Gurpreet", "Harpreet", "Jaspreet", "Maninder", "Simran", "Balwinder", "Navjot", "Sukhwinder"]
    last = ["Singh", "Kaur", "Gill", "Sandhu", "Brar", "Dhillon"]
    farmer_docs = []
    for i in range(30):
        farmer_docs.append({"name": f"{random.choice(first)} {random.choice(last)}",
                            "phone": f"{random.randint(6, 9)}{i:09d}",
                            "land_acres": round(random.uniform(1, 25), 1),
                            "address": {"village": f"{random.choice(districts)} Village", "district": random.choice(districts),
                                        "pincode": f"{140000 + i:06d}"},
                            "bank": {"bank_name": random.choice(["SBI", "PNB", "HDFC", "Punjab & Sind Bank"]),
                                     "account_last4": f"{1000 + i:04d}"},
                            "registered_on": datetime.utcnow() - timedelta(days=random.randint(30, 700))})
    db.farmers.insert_many(farmer_docs)
    mandis = list(db.mandis.find())
    farmers = list(db.farmers.find())
    ranges = {"Wheat": (2200, 2600), "Paddy": (2100, 2500), "Maize": (1900, 2300),
              "Cotton": (6500, 7800), "Sugarcane": (350, 420), "Mustard": (5200, 6000)}
    sales = []
    for _ in range(90):
        mandi = random.choice(mandis)
        crop = random.choice(mandi["commodities"])
        low, high = ranges[crop]
        qty = round(random.uniform(5, 120), 1)
        rate = random.randint(low, high)
        sales.append({"farmer_id": random.choice(farmers)["_id"], "mandi_id": mandi["_id"],
                      "crop": {"name": crop, "variety": "Local Select", "quality_grade": random.choice(["A", "B", "C"])},
                      "quantity_quintals": qty, "rate_per_quintal": rate, "total_amount": qty * rate,
                      "sale_date": datetime.utcnow() - timedelta(days=random.randint(0, 365)),
                      "payment_status": "Pending" if random.random() < 0.25 else "Paid"})
    db.sales.insert_many(sales)
    print(f"Seed complete: {db.mandis.count_documents({})} mandis, {db.farmers.count_documents({})} farmers, {db.sales.count_documents({})} sales.")

