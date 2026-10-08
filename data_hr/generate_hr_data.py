"""Synthetic HR dataset generator. Run: python generate_hr_data.py"""
import pandas as pd
import numpy as np
from datetime import datetime
import random
import os

np.random.seed(21)
random.seed(21)
data_dir = os.path.dirname(os.path.abspath(__file__))

start_date = datetime(2023, 1, 1)
end_date = datetime(2024, 12, 31)
date_range = pd.date_range(start=start_date, end=end_date, freq='D')
dates_df = pd.DataFrame({
    'Date': date_range, 'Year': date_range.year, 'Quarter': date_range.quarter,
    'Month': date_range.month, 'MonthName': date_range.strftime('%B'),
    'DayOfWeek': date_range.day_name(), 'DayOfMonth': date_range.day,
    'WeekOfYear': date_range.isocalendar().week.astype(int),
    'IsWeekend': date_range.dayofweek >= 5})

depts = [('Engineering', 'New York'), ('Sales', 'Chicago'), ('Support', 'Dallas'),
         ('HR', 'Boston'), ('Finance', 'New York'), ('Marketing', 'Seattle')]
departments_df = pd.DataFrame(
    [{'DepartmentID': i + 1, 'DeptName': d, 'Location': loc} for i, (d, loc) in enumerate(depts)])

levels = ['Junior', 'Mid', 'Senior', 'Lead']
band = {'Junior': (40, 70), 'Mid': (65, 100), 'Senior': (95, 140), 'Lead': (130, 180)}
employees = []
for eid in range(1, 601):
    lvl = random.choices(levels, weights=[0.35, 0.35, 0.2, 0.1])[0]
    lo, hi = band[lvl]
    employees.append({
        'EmployeeID': eid,
        'Gender': random.choices(['Male', 'Female'], weights=[0.55, 0.45])[0],
        'Age': random.randint(22, 60),
        'DepartmentID': random.randint(1, len(depts)),
        'JobLevel': lvl,
        'HireDate': random.choice(date_range),
        'Salary': round(random.uniform(lo, hi) * 1000, 2),
        'Attrition': random.choices(['Yes', 'No'], weights=[0.18, 0.82])[0]})
employees_df = pd.DataFrame(employees)

# Recruitment funnel: one row per stage reached (cumulative counts per stage)
stages = [('Applied', 0), ('Screened', 1), ('Interviewed', 2), ('Offered', 3), ('Hired', 4)]
terminal_w = [0.35, 0.25, 0.2, 0.1, 0.1]
apps, aid = [], 1
for _ in range(1500):
    term = random.choices(range(5), weights=terminal_w)[0]
    dept = random.randint(1, len(depts))
    date = random.choice(date_range)
    for s in range(term + 1):
        apps.append({'ApplicationID': aid, 'DepartmentID': dept,
                     'Stage': stages[s][0], 'StageOrder': stages[s][1],
                     'ApplicationDate': date})
    aid += 1
recruitment_df = pd.DataFrame(apps)

for name, df in [('Employees', employees_df), ('Departments', departments_df),
                 ('Recruitment', recruitment_df), ('Dates', dates_df)]:
    df.to_csv(os.path.join(data_dir, f'{name}.csv'), index=False)
    print(f'{name}.csv: {len(df)} rows')
