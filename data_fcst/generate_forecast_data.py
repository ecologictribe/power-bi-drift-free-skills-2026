"""Synthetic consumption + DiD dataset generator. Run: python generate_forecast_data.py
Design: 4 warehouses (2 Treatment under new replenishment policy from 2024-07-01,
2 Control). Monthly grain, Actual + Forecast scenarios side by side.
"""
import pandas as pd
import numpy as np
from datetime import datetime
import random
import os

np.random.seed(99)
random.seed(99)
data_dir = os.path.dirname(os.path.abspath(__file__))

start_date = datetime(2023, 1, 1)
end_date = datetime(2024, 12, 31)
months = pd.date_range(start=start_date, end=end_date, freq='MS')
date_range = pd.date_range(start=start_date, end=end_date, freq='D')
dates_df = pd.DataFrame({
    'Date': date_range, 'Year': date_range.year, 'Quarter': date_range.quarter,
    'Month': date_range.month, 'MonthName': date_range.strftime('%B'),
    'DayOfWeek': date_range.day_name(), 'DayOfMonth': date_range.day,
    'WeekOfYear': date_range.isocalendar().week.astype(int),
    'IsWeekend': date_range.dayofweek >= 5})

warehouses_df = pd.DataFrame([
    {'WarehouseID': 1, 'WarehouseName': 'North Hub', 'Group': 'Treatment'},
    {'WarehouseID': 2, 'WarehouseName': 'South Hub', 'Group': 'Treatment'},
    {'WarehouseID': 3, 'WarehouseName': 'East Depot', 'Group': 'Control'},
    {'WarehouseID': 4, 'WarehouseName': 'West Depot', 'Group': 'Control'}])

cats = ['Fasteners', 'Tools', 'Electrical', 'Plumbing']
products_df = pd.DataFrame(
    [{'ProductID': i + 1, 'ProductName': f'{c} SKU-{i + 1}', 'Category': c}
     for i, c in enumerate(cats * 10)])

rows, rid = [], 1
for m in months:
    post = m >= datetime(2024, 7, 1)
    for wid in range(1, 5):
        treat = wid <= 2
        for pid in range(1, 41):
            base = random.uniform(80, 400)
            actual = base * (0.78 if (treat and post) else 1.0) * random.uniform(0.85, 1.15)
            forecast = base * random.uniform(0.9, 1.1)
            stockout = max(0, int(random.uniform(0, 6) - (3 if (treat and post) else 0)))
            for scenario, qty in (('Actual', round(actual, 1)), ('Forecast', round(forecast, 1))):
                rows.append({'RowID': rid, 'ProductID': pid, 'WarehouseID': wid,
                             'ConsDate': m, 'Scenario': scenario,
                             'ConsumptionQty': qty, 'StockoutDays': stockout if scenario == 'Actual' else 0})
                rid += 1
cons_df = pd.DataFrame(rows)

for name, df in [('Consumption', cons_df), ('Warehouses', warehouses_df),
                 ('Products', products_df), ('Dates', dates_df)]:
    df.to_csv(os.path.join(data_dir, f'{name}.csv'), index=False)
    print(f'{name}.csv: {len(df)} rows')
