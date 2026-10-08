"""Synthetic marketing dataset generator. Run: python generate_marketing_data.py"""
import pandas as pd
import numpy as np
from datetime import datetime
import random
import os

np.random.seed(55)
random.seed(55)
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

channels = [('Google Ads', 'Paid'), ('Meta Ads', 'Paid'), ('Email', 'Owned'),
            ('Organic Search', 'Organic'), ('Referral', 'Organic'), ('Events', 'Owned')]
channels_df = pd.DataFrame(
    [{'ChannelID': i + 1, 'Channel': c, 'Category': k} for i, (c, k) in enumerate(channels)])

camps = ['Spring Launch', 'Summer Sale', 'Festive Push', 'Winter Clearance',
         'Brand Always-On', 'Retargeting Q3', 'New Year Blast', 'Monsoon Drive']
campaigns_df = pd.DataFrame(
    [{'CampaignID': i + 1, 'CampaignName': c, 'Channel': random.choice(channels)[0],
      'Budget': round(random.uniform(20000, 120000), 2)} for i, c in enumerate(camps)])

rows, sid = [], 1
eff = {1: 3.2, 2: 2.8, 3: 4.5, 4: 3.8, 5: 2.2, 6: 1.8}  # revenue multiple per channel
for date in date_range:
    for ch in range(1, 7):
        if random.random() < (0.85 if date.dayofweek < 5 else 0.5):
            spend = round(random.uniform(200, 2500), 2)
            imp = int(spend * random.uniform(8, 15))
            clicks = int(imp * random.uniform(0.02, 0.06))
            conv = int(clicks * random.uniform(0.05, 0.2))
            rows.append({'SpendID': sid, 'ChannelID': ch,
                         'CampaignID': random.randint(1, len(camps)),
                         'SpendDate': date, 'Spend': spend, 'Impressions': imp,
                         'Clicks': clicks, 'Conversions': conv,
                         'Revenue': round(spend * eff[ch] * random.uniform(0.7, 1.3), 2)})
            sid += 1
spend_df = pd.DataFrame(rows)

for name, df in [('DailySpend', spend_df), ('Channels', channels_df),
                 ('Campaigns', campaigns_df), ('Dates', dates_df)]:
    df.to_csv(os.path.join(data_dir, f'{name}.csv'), index=False)
    print(f'{name}.csv: {len(df)} rows')
