# 🌾 Mandi Crop Sales & Price Tracker

A menu-driven MongoDB application for recording Punjab farmers, mandis, crop sales,
payments, and price intelligence.

## Quick start

1. Install Python 3.10+ and MongoDB 5.0+.
2. Start MongoDB locally, or set `MONGO_URI` to an Atlas connection string.
3. Run:

```powershell
pip install -r requirements.txt
python main.py
```

Choose **Load Sample Data** first. The seed creates 12 mandis, 30 farmers, and 90
sales using repeatable original data.

## Run the desktop GUI

The project supports both interfaces against the same MongoDB database:

```powershell
python main.py --gui
```

You can also launch it directly:

```powershell
python gui.py
```

The GUI provides live tabs for Farmers, Mandis, Sales, Analytics, and Tools.
Adding, updating, deleting, seeding, or validating data in either the CLI or GUI
is immediately reflected in the other interface after refresh.

## Database design

`farmers` embeds address and bank information. `mandis` embeds commodities and
facilities. `sales` references farmers and mandis while embedding crop details.
This avoids duplicating shared data while keeping sale-specific facts together.

All collections use strict `$jsonSchema` validation. Unique indexes protect farmer
phone numbers and mandi names; reference indexes make sales lookups efficient.

## Features

- CRUD-ready data model with cascade deletion for farmer sales.
- Repeatable seed data with realistic crop prices and pending payments.
- Validation demonstration using MongoDB rejection errors.
- Aggregations for farmer revenue, crop prices, monthly trends, top farmers,
  wheat price buckets, district quantities, and pending payments.
- Rich terminal dashboard with Indian currency formatting.
- Tkinter desktop GUI with forms, tables, live counters, reports, and confirmation dialogs.

## Viva/demo flow

1. Explain embedding versus referencing.
2. Load sample data and show the three collections in Compass.
3. Run the validation demonstration.
4. Explain how `total_amount` is calculated.
5. Compare average crop prices and pending payments.
6. Open `db.py`, `crud.py`, and `analytics.py` to show PyMongo operations.
