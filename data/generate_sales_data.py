import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Create data directory if it doesn't exist
data_dir = os.path.dirname(os.path.abspath(__file__))

# Generate Date dimension
print("Generating Date dimension...")
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
    'IsWeekend': date_range.dayofweek >= 5
})

# Generate Products dimension
print("Generating Products dimension...")
categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books']
subcategories = {
    'Electronics': ['Phones', 'Laptops', 'Tablets', 'Headphones', 'Cameras'],
    'Clothing': ['Shirts', 'Pants', 'Dresses', 'Jackets', 'Shoes'],
    'Home & Garden': ['Furniture', 'Decor', 'Kitchen', 'Garden', 'Lighting'],
    'Sports': ['Fitness', 'Outdoor', 'Team Sports', 'Water Sports', 'Winter Sports'],
    'Books': ['Fiction', 'Non-Fiction', 'Children', 'Technical', 'Comics']
}

products = []
product_id = 1

for category in categories:
    for subcategory in subcategories[category]:
        for i in range(10):  # 10 products per subcategory
            product_name = f"{subcategory} Product {i+1}"
            unit_price = round(random.uniform(10, 500), 2)
            cost = round(unit_price * random.uniform(0.4, 0.7), 2)
            products.append({
                'ProductID': product_id,
                'ProductName': product_name,
                'Category': category,
                'SubCategory': subcategory,
                'UnitPrice': unit_price,
                'Cost': cost
            })
            product_id += 1

products_df = pd.DataFrame(products)

# Generate Customers dimension
print("Generating Customers dimension...")
regions = ['North', 'South', 'East', 'West']
segments = ['Consumer', 'Corporate', 'Home Office']
cities = {
    'North': ['New York', 'Boston', 'Philadelphia', 'Pittsburgh', 'Hartford'],
    'South': ['Miami', 'Atlanta', 'Dallas', 'Houston', 'Nashville'],
    'East': ['Chicago', 'Detroit', 'Cleveland', 'Columbus', 'Indianapolis'],
    'West': ['Los Angeles', 'San Francisco', 'Seattle', 'Denver', 'Phoenix']
}

customers = []
customer_id = 1

for region in regions:
    for segment in segments:
        for city in cities[region]:
            for i in range(5):  # 5 customers per city-segment combination
                customer_name = f"Customer {customer_id}"
                customers.append({
                    'CustomerID': customer_id,
                    'CustomerName': customer_name,
                    'Region': region,
                    'Segment': segment,
                    'City': city
                })
                customer_id += 1

customers_df = pd.DataFrame(customers)

# Generate Orders fact table
print("Generating Orders fact table...")
order_statuses = ['Completed', 'Processing', 'Shipped', 'Cancelled']
status_weights = [0.6, 0.2, 0.15, 0.05]

orders = []
order_id = 1

# Generate orders for each date
for date in date_range:
    # Variable number of orders per day (more on weekdays)
    if date.dayofweek < 5:  # Weekday
        num_orders = random.randint(5, 20)
    else:  # Weekend
        num_orders = random.randint(2, 8)
    
    for _ in range(num_orders):
        customer = random.choice(customers)
        product = random.choice(products)
        quantity = random.randint(1, 5)
        amount = round(product['UnitPrice'] * quantity, 2)
        cost = round(product['Cost'] * quantity, 2)
        status = random.choices(order_statuses, weights=status_weights, k=1)[0]
        
        orders.append({
            'OrderID': order_id,
            'CustomerID': customer['CustomerID'],
            'ProductID': product['ProductID'],
            'OrderDate': date,
            'Quantity': quantity,
            'Amount': amount,
            'Cost': cost,
            'Status': status
        })
        order_id += 1

orders_df = pd.DataFrame(orders)

# Save to CSV files
print("Saving data to CSV files...")
orders_df.to_csv(os.path.join(data_dir, 'Orders.csv'), index=False)
customers_df.to_csv(os.path.join(data_dir, 'Customers.csv'), index=False)
products_df.to_csv(os.path.join(data_dir, 'Products.csv'), index=False)
dates_df.to_csv(os.path.join(data_dir, 'Dates.csv'), index=False)

print(f"Data generation complete!")
print(f"Generated {len(orders_df)} orders")
print(f"Generated {len(customers_df)} customers")
print(f"Generated {len(products_df)} products")
print(f"Generated {len(dates_df)} dates")
print(f"\nFiles saved to: {data_dir}")
print("  - Orders.csv")
print("  - Customers.csv")
print("  - Products.csv")
print("  - Dates.csv")
