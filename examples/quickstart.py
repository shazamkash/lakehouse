"""
Quickstart example - Minimal code to get started with Lakehouse.

For remote server deployment:
1. Set environment variable: export LAKEHOUSE_HOST=10.16.36.36
2. Or copy .env.example to .env and update LAKEHOUSE_HOST
3. Client will automatically use the remote server
"""

from lakehouse_client import LakehouseClient
import pandas as pd

# Optional: Load environment variables from .env file
# Uncomment these lines if using .env file:
# from dotenv import load_dotenv
# load_dotenv()

# Create sample data
data = pd.DataFrame({
    'product': ['A', 'B', 'C', 'D', 'E'],
    'sales': [100, 200, 150, 300, 250],
    'region': ['North', 'South', 'East', 'West', 'North']
})

# Save to CSV
data.to_csv('products.csv', index=False)

# Initialize client
# If LAKEHOUSE_HOST is set, client will connect to remote server automatically
# Otherwise, defaults to localhost
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
