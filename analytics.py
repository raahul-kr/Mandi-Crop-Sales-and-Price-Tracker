"""Aggregation reports used by the dashboard."""

from pymongo.database import Database


def revenue_per_farmer(db: Database) -> list[dict]:
    """Group revenue and quantity by farmer, then join names for a readable report."""
    return list(db.sales.aggregate([
        {"$group": {"_id": "$farmer_id", "total_revenue": {"$sum": "$total_amount"},
                    "total_quintals": {"$sum": "$quantity_quintals"}, "num_sales": {"$sum": 1}}},
        {"$lookup": {"from": "farmers", "localField": "_id", "foreignField": "_id", "as": "farmer"}},
        {"$unwind": "$farmer"},
        {"$project": {"_id": 0, "farmer": "$farmer.name", "village": "$farmer.address.village",
                      "total_revenue": 1, "total_quintals": 1, "num_sales": 1}},
        {"$sort": {"total_revenue": -1}},
    ]))


def avg_price_per_crop_per_mandi(db: Database) -> list[dict]:
    """Calculate average rate by crop and mandi for price comparison."""
    return list(db.sales.aggregate([
        {"$group": {"_id": {"crop": "$crop.name", "mandi_id": "$mandi_id"},
                    "avg_rate": {"$avg": "$rate_per_quintal"}, "sales_count": {"$sum": 1}}},
        {"$lookup": {"from": "mandis", "localField": "_id.mandi_id", "foreignField": "_id", "as": "mandi"}},
        {"$unwind": "$mandi"},
        {"$project": {"_id": 0, "crop": "$_id.crop", "mandi": "$mandi.name",
                      "avg_rate": {"$round": ["$avg_rate", 2]}, "sales_count": 1}},
        {"$sort": {"crop": 1, "avg_rate": -1}},
    ]))


def monthly_sales_trend(db: Database, crop: str | None = None) -> list[dict]:
    """Summarize monthly quantity, revenue, and average price, optionally for one crop."""
    pipeline = []
    if crop:
        pipeline.append({"$match": {"crop.name": crop}})
    pipeline += [
        {"$group": {"_id": {"$dateToString": {"format": "%Y-%m", "date": "$sale_date"}},
                    "total_quintals": {"$sum": "$quantity_quintals"},
                    "revenue": {"$sum": "$total_amount"}, "avg_rate": {"$avg": "$rate_per_quintal"}}},
        {"$sort": {"_id": 1}},
    ]
    return list(db.sales.aggregate(pipeline))


def top_n_farmers(db: Database, n: int = 5) -> list[dict]:
    """Return the highest-earning farmers using the revenue grouping."""
    rows = revenue_per_farmer(db)
    return rows[:n]


def wheat_price_distribution(db: Database) -> list[dict]:
    """Create a bucket histogram of Wheat rates."""
    return list(db.sales.aggregate([
        {"$match": {"crop.name": "Wheat"}},
        {"$bucket": {"groupBy": "$rate_per_quintal", "boundaries": [1500, 2000, 2200, 2400, 2600, 3000],
                     "default": "Other", "output": {"count": {"$sum": 1},
                     "total_quintals": {"$sum": "$quantity_quintals"}}}},
    ]))


def district_wise_quantity(db: Database) -> list[dict]:
    """Join mandi districts and group sold quantity and revenue by crop."""
    return list(db.sales.aggregate([
        {"$lookup": {"from": "mandis", "localField": "mandi_id", "foreignField": "_id", "as": "mandi"}},
        {"$unwind": "$mandi"},
        {"$group": {"_id": {"district": "$mandi.district", "crop": "$crop.name"},
                    "total_quintals": {"$sum": "$quantity_quintals"}, "revenue": {"$sum": "$total_amount"}}},
        {"$sort": {"_id.district": 1, "total_quintals": -1}},
    ]))


def pending_payments_summary(db: Database) -> list[dict]:
    """Show outstanding payment value grouped by mandi."""
    return list(db.sales.aggregate([
        {"$match": {"payment_status": "Pending"}},
        {"$group": {"_id": "$mandi_id", "pending_amount": {"$sum": "$total_amount"}, "sales": {"$sum": 1}}},
        {"$lookup": {"from": "mandis", "localField": "_id", "foreignField": "_id", "as": "mandi"}},
        {"$unwind": "$mandi"},
        {"$project": {"_id": 0, "mandi": "$mandi.name", "pending_amount": 1, "sales": 1}},
        {"$sort": {"pending_amount": -1}},
    ]))

