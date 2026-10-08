"""Synthetic finance dataset generator. Run: python generate_finance_data.py"""
import pandas as pd
import numpy as np
from datetime import datetime
import random
import os

np.random.seed(33)
random.seed(33)
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

accounts = [
    ('Product Revenue', 'Revenue'), ('Service Revenue', 'Revenue'),
    ('Other Income', 'Revenue'), ('Materials', 'COGS'), ('Labor', 'COGS'),
    ('Salaries', 'Opex'), ('Rent', 'Opex'), ('Marketing', 'Opex'),
    ('Travel', 'Opex'), ('IT', 'Opex'), ('Tax', 'Other')]
base = {'Product Revenue': 500, 'Service Revenue': 200, 'Other Income': 30,
        'Materials': 180, 'Labor': 150, 'Salaries': 220, 'Rent': 40,
        'Marketing': 60, 'Travel': 25, 'IT': 35, 'Tax': 45}
accounts_df = pd.DataFrame(
    [{'AccountID': i + 1, 'AccountName': n, 'AccountType': t} for i, (n, t) in enumerate(accounts)])
ccs = ['North Ops', 'South Ops', 'East Ops', 'West Ops', 'HQ', 'R&D']
costcenters_df = pd.DataFrame(
    [{'CostCenterID': i + 1, 'CCName': c} for i, c in enumerate(ccs)])

entries, eid = [], 1
for m in months:
    growth = 1 + 0.15 * ((m.year - 2023) * 12 + m.month) / 24
    for ai, (name, _typ) in enumerate(accounts):
        for ci in range(len(ccs)):
            budget = round(base[name] * growth * random.uniform(0.12, 0.22), 2)
            actual = round(budget * random.uniform(0.85, 1.15), 2)
            day = random.randint(1, 28)
            for scenario, amt in (('Budget', budget), ('Actual', actual)):
                entries.append({'EntryID': eid, 'AccountID': ai + 1, 'CostCenterID': ci + 1,
                                'EntryDate': datetime(m.year, m.month, day),
                                'Scenario': scenario, 'Amount': amt})
                eid += 1
ledger_df = pd.DataFrame(entries)

for name, df in [('Ledger', ledger_df), ('Accounts', accounts_df),
                 ('CostCenters', costcenters_df), ('Dates', dates_df)]:
    df.to_csv(os.path.join(data_dir, f'{name}.csv'), index=False)
    print(f'{name}.csv: {len(df)} rows')
