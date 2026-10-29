"""CRUD operations for farmers, mandis, and sales."""

from datetime import datetime
from typing import Any

from bson import ObjectId
from pymongo.database import Database


def add_farmer(db: Database, name: str, phone: str, land_acres: float, village: str, district: str,
               pincode: str = "", bank_name: str = "", account_last4: str = "") -> ObjectId:
    """Insert a farmer with embedded address and optional bank details."""
    doc: dict[str, Any] = {
        "name": name, "phone": phone, "land_acres": land_acres,
        "address": {"village": village, "district": district, "pincode": pincode},
        "registered_on": datetime.utcnow(),
    }
    if bank_name or account_last4:
        doc["bank"] = {"bank_name": bank_name, "account_last4": account_last4}
    return db.farmers.insert_one(doc).inserted_id


def add_mandi(db: Database, name: str, district: str, commodities: list[str],
              facilities: list[str] | None = None) -> ObjectId:
    """Insert a mandi with embedded commodity and facility arrays."""
    return db.mandis.insert_one({
        "name": name, "district": district, "commodities": commodities,
        "facilities": facilities or [],
    }).inserted_id


def add_sale(db: Database, farmer_phone: str, mandi_name: str, crop_name: str, variety: str,
             grade: str, qty: float, rate: float, sale_date: datetime, payment_status: str) -> ObjectId:
    """Resolve references, calculate revenue, and insert a sale."""
    farmer = db.farmers.find_one({"phone": farmer_phone}, {"_id": 1})
    mandi = db.mandis.find_one({"name": mandi_name}, {"_id": 1, "commodities": 1})
    if not farmer or not mandi:
        raise ValueError("Farmer phone or mandi name was not found.")
    if crop_name not in mandi["commodities"]:
        raise ValueError("That mandi does not trade the selected crop.")
    return db.sales.insert_one({
        "farmer_id": farmer["_id"], "mandi_id": mandi["_id"],
        "crop": {"name": crop_name, "variety": variety, "quality_grade": grade},
        "quantity_quintals": qty, "rate_per_quintal": rate,
        "total_amount": qty * rate, "sale_date": sale_date,
        "payment_status": payment_status,
    }).inserted_id


def bulk_add_sales(db: Database, documents: list[dict[str, Any]]) -> None:
    """Insert many prepared sales in one unordered batch."""
    if documents:
        db.sales.insert_many(documents, ordered=False)


def list_farmers(db: Database, village: str | None = None, district: str | None = None) -> list[dict]:
    """List farmers, optionally filtered by village or district."""
    query: dict[str, Any] = {}
    if village:
        query["address.village"] = village
    if district:
        query["address.district"] = district
    return list(db.farmers.find(query, {"name": 1, "phone": 1, "land_acres": 1, "address": 1}).sort("name", 1))


def get_farmer_by_phone(db: Database, phone: str) -> dict | None:
    """Find one farmer by unique phone number."""
    return db.farmers.find_one({"phone": phone})


def list_sales(db: Database, crop: str | None = None, start: datetime | None = None,
               end: datetime | None = None, limit: int = 20) -> list[dict]:
    """List recent sales with optional crop and date filters."""
    query: dict[str, Any] = {}
    if crop:
        query["crop.name"] = crop
    if start or end:
        query["sale_date"] = {}
        if start:
            query["sale_date"]["$gte"] = start
        if end:
            query["sale_date"]["$lte"] = end
    return list(db.sales.find(query).sort("sale_date", -1).limit(limit))


def update_sale_rate(db: Database, sale_id: str, new_rate: float) -> int:
    """Update a sale rate and recompute its total using an update pipeline."""
    result = db.sales.update_one(
        {"_id": ObjectId(sale_id)},
        [{"$set": {"rate_per_quintal": new_rate,
                   "total_amount": {"$multiply": ["$quantity_quintals", new_rate]}}}],
    )
    return result.modified_count


def update_land(db: Database, phone: str, new_acres: float) -> int:
    """Update a farmer's land holding."""
    return db.farmers.update_one({"phone": phone}, {"$set": {"land_acres": new_acres}}).modified_count


def mark_pending_as_paid(db: Database, mandi_name: str) -> int:
    """Mark all pending sales at a named mandi as paid."""
    mandi = db.mandis.find_one({"name": mandi_name}, {"_id": 1})
    if not mandi:
        return 0
    return db.sales.update_many({"mandi_id": mandi["_id"], "payment_status": "Pending"},
                                {"$set": {"payment_status": "Paid"}}).modified_count


def add_facility(db: Database, mandi_name: str, facility: str) -> int:
    """Add a facility without creating duplicates."""
    return db.mandis.update_one({"name": mandi_name}, {"$addToSet": {"facilities": facility}}).modified_count


def upsert_mandi_commodity(db: Database, mandi_name: str, commodity: str) -> None:
    """Demonstrate an upsert while adding a commodity idempotently."""
    db.mandis.update_one({"name": mandi_name}, {"$addToSet": {"commodities": commodity}},
                         upsert=True)


def delete_sale(db: Database, sale_id: str) -> int:
    """Delete one sale by ObjectId."""
    return db.sales.delete_one({"_id": ObjectId(sale_id)}).deleted_count


def delete_farmer(db: Database, phone: str) -> int:
    """Delete a farmer and cascade-delete sales referencing that farmer."""
    farmer = db.farmers.find_one({"phone": phone}, {"_id": 1})
    if not farmer:
        return 0
    db.sales.delete_many({"farmer_id": farmer["_id"]})
    return db.farmers.delete_one({"_id": farmer["_id"]}).deleted_count


def delete_old_pending_sales(db: Database, before_date: datetime) -> int:
    """Delete pending sales older than a supplied date."""
    return db.sales.delete_many({"payment_status": "Pending", "sale_date": {"$lt": before_date}}).deleted_count

