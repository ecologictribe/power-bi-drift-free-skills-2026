"""Synthetic zoo dataset generator. Run: python generate_zoo_data.py"""
import pandas as pd
import numpy as np
from datetime import datetime
import random
import os

np.random.seed(77)
random.seed(77)
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

species = [('Lion', 'Mammal', 'Vulnerable'), ('Tiger', 'Mammal', 'Endangered'),
           ('Giraffe', 'Mammal', 'Vulnerable'), ('Zebra', 'Mammal', 'Near Threatened'),
           ('Penguin', 'Bird', 'Near Threatened'), ('Parrot', 'Bird', 'Least Concern'),
           ('Flamingo', 'Bird', 'Least Concern'), ('Python', 'Reptile', 'Least Concern'),
           ('Tortoise', 'Reptile', 'Endangered'), ('Crocodile', 'Reptile', 'Vulnerable'),
           ('Elephant', 'Mammal', 'Endangered'), ('Kangaroo', 'Mammal', 'Least Concern')]
species_df = pd.DataFrame(
    [{'SpeciesID': i + 1, 'SpeciesName': n, 'Category': c, 'Status': s,
      'DailyFoodKg': round(random.uniform(1, 30), 1)} for i, (n, c, s) in enumerate(species)])

habs = [('Savannah', 40), ('Jungle', 30), ('Aviary', 50), ('Reptile House', 25),
        ('Aquatic', 20), ('Nocturnal', 15)]
enclosures_df = pd.DataFrame(
    [{'EnclosureID': i + 1, 'EnclosureName': h, 'Habitat': h, 'Capacity': cap}
     for i, (h, cap) in enumerate(habs)])

animals = []
for aid in range(1, 121):
    sp = random.randint(1, len(species))
    animals.append({'AnimalID': aid, 'SpeciesID': sp,
                    'EnclosureID': random.randint(1, len(habs)),
                    'Gender': random.choices(['Male', 'Female'], weights=[0.5, 0.5])[0],
                    'BirthDate': random.choice(date_range),
                    'WeightKg': round(random.uniform(2, 900), 1),
                    'Health': random.choices(['Good', 'Fair'], weights=[0.9, 0.1])[0]})
animals_df = pd.DataFrame(animals)

tickets = ['Adult', 'Child', 'Senior']
visits, vid = [], 1
for date in date_range:
    base_n = 60 if date.dayofweek < 5 else 150
    for t in tickets:
        n = max(1, int(base_n * random.uniform(0.2, 0.5)))
        price = {'Adult': 25, 'Child': 12, 'Senior': 15}[t]
        visits.append({'VisitID': vid, 'VisitDate': date, 'TicketType': t,
                       'Visitors': n, 'Revenue': round(n * price, 2)})
        vid += 1
visits_df = pd.DataFrame(visits)

for name, df in [('Animals', animals_df), ('Species', species_df),
                 ('Enclosures', enclosures_df), ('Visits', visits_df), ('Dates', dates_df)]:
    df.to_csv(os.path.join(data_dir, f'{name}.csv'), index=False)
    print(f'{name}.csv: {len(df)} rows')
