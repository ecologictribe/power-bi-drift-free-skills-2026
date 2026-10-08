"""Synthetic inventory dataset generator. Run: python generate_inventory_data.py"""
import pandas as pd
import numpy as np
from datetime import datetime
import random
import os

np.random.seed(7)
random.seed(7)
data_dir = os.path.dirname(os.path.abspath(__file__))

# Dates (reuse same shape as sales model)
start_date = datetime(2023, 1, 1)
end_date = datetime(2024, 12, 31)
date_range = pd.date_range(start=start_date, end=end_date, freq='D')
dates_df = pd.DataFrame({
    'Date': date_range,
    'Year': date_range.year,
    'Quarter': date_range.quarter,
    'Month': date_range.month,
    'MonthName': date_range.strftime('%B'),
    'DayOfWeek': date_range.day_name(),
    'DayOfMonth': date_range.day,
    'WeekOfYear': date_range.isocalendar().week.astype(int),
    'IsWeekend': date_range.dayofweek >= 5,
})

# Warehouses
regions = ['North', 'South', 'East', 'West']
cities = {'North': ['New York', 'Boston'], 'South': ['Miami', 'Dallas'],
          'East': ['Chicago', 'Columbus'], 'West': ['Seattle', 'Denver']}
warehouses = []
wid = 1
for region in regions:
    for city in cities[region]:
        warehouses.append({'WarehouseID': wid, 'WarehouseName': f'{city} DC',
                           'Region': region, 'City': city,
                           'Capacity': random.randint(10000, 50000)})
        wid += 1
warehouses_df = pd.DataFrame(warehouses)

# Suppliers
countries = ['USA', 'Germany', 'China', 'Mexico', 'India']
suppliers = [{'SupplierID': i + 1, 'SupplierName': f'Supplier {i + 1}',
              'Country': random.choice(countries),
              'LeadTimeDays': random.randint(2, 30)} for i in range(30)]
suppliers_df = pd.DataFrame(suppliers)

# Products (each has a primary supplier -> chain Transactions > Products > Suppliers)
categories = {'Hardware': ['Tools', 'Fasteners', 'Electrical'],
              'Office': ['Paper', 'Furniture', 'Supplies'],
              'Retail': ['Apparel', 'Footwear', 'Accessories']}
products = []
pid = 1
for cat, subs in categories.items():
    for sub in subs:
        for i in range(16):
            cost = round(random.uniform(2, 200), 2)
            products.append({'ProductID': pid,
                             'ProductName': f'{sub} Item {i + 1}',
                             'Category': cat, 'SubCategory': sub,
                             'SupplierID': random.randint(1, 30),
                             'UnitCost': cost,
                             'UnitPrice': round(cost * random.uniform(1.2, 2.0), 2),
                             'ReorderLevel': random.randint(20, 200)})
            pid += 1
products_df = pd.DataFrame(products)

# InventoryTransactions fact table
txn_types = ['Purchase', 'Sale', 'Adjustment', 'Return']
weights = [0.35, 0.5, 0.05, 0.10]
txns = []
tid = 1
for date in date_range:
    n = random.randint(4, 14) if date.dayofweek < 5 else random.randint(1, 5)
    for _ in range(n):
        p = random.choice(products)
        t = random.choices(txn_types, weights=weights, k=1)[0]
        qty = random.randint(1, 50)
        if t == 'Adjustment':
            qty = random.randint(-20, 20) or 5
        total = round(abs(qty) * p['UnitCost'], 2)
        txns.append({'TransactionID': tid, 'ProductID': p['ProductID'],
                     'WarehouseID': random.randint(1, len(warehouses)),
                     'TransactionDate': date, 'TransactionType': t,
                     'Quantity': qty, 'UnitCost': p['UnitCost'], 'TotalValue': total})
        tid += 1
txns_df = pd.DataFrame(txns)

for name, df in [('InventoryTransactions', txns_df), ('Products', products_df),
                 ('Warehouses', warehouses_df), ('Suppliers', suppliers_df),
                 ('Dates', dates_df)]:
    df.to_csv(os.path.join(data_dir, f'{name}.csv'), index=False)
    print(f'{name}.csv: {len(df)} rows')
