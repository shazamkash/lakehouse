"""
Quickstart example - Minimal code to get started with Lakehouse.
"""

from lakehouse_client import LakehouseClient
import pandas as pd

# Create sample data
data = pd.DataFrame({
    'product': ['A', 'B', 'C', 'D', 'E'],
    'sales': [100, 200, 150, 300, 250],
    'region': ['North', 'South', 'East', 'West', 'North']
})

# Save to CSV
data.to_csv('products.csv', index=False)

# Initialize client
client = LakehouseClient()

# One-step ingest: Upload to MinIO + Create Delta table + Register in Unity Catalog
result = client.ingest_and_create_table(
    file_path='products.csv',
    bucket='raw-data',
    catalog='main',
    schema='default',
    table='products'
)

print(f"Table created: {result['table']}")

# Query the data
df = client.query_to_dataframe("SELECT * FROM delta.main.default.products")
print("\nData:")
print(df)

# Aggregate query
summary = client.query_to_dataframe("""
    SELECT region, SUM(sales) as total_sales
    FROM delta.main.default.products
    GROUP BY region
    ORDER BY total_sales DESC
""")

print("\nSales by region:")
print(summary)

client.close()
