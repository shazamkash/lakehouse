"""
Quickstart for Remote Server - UPDATED

This version uses SimpleLakehouseClient which does NOT require:
- Local Spark installation
- Java installation
- Delta Lake package downloads

Perfect for remote server deployments!
"""

from lakehouse_client import SimpleLakehouseClient  # Changed from LakehouseClient
import pandas as pd
import os

print("=" * 70)
print("Lakehouse Quickstart - Remote Server")
print("=" * 70)
print()

# Check environment
lakehouse_host = os.getenv('LAKEHOUSE_HOST', 'localhost')
print(f"LAKEHOUSE_HOST: {lakehouse_host}")
print()

# Create sample data
print("Step 1: Creating sample data...")
data = pd.DataFrame({
    'product': ['A', 'B', 'C', 'D', 'E'],
    'sales': [100, 200, 150, 300, 250],
    'region': ['North', 'South', 'East', 'West', 'North']
})
data.to_csv('products.csv', index=False)
print("✓ Sample data created")
print()

# Initialize SimpleLakehouseClient (no Spark/Java needed!)
print("Step 2: Initializing SimpleLakehouseClient...")
client = SimpleLakehouseClient()  # This won't create a local Spark session
print("✓ Client initialized (no local Spark needed)")
print()

# Upload to MinIO
print("Step 3: Uploading to MinIO on remote server...")
s3_uri = client.upload_parquet(
    file_path='products.csv',
    bucket='raw-data',
    object_name='products'
)
print(f"✓ Uploaded to: {s3_uri}")
print()

# Instructions for Delta table creation
print("=" * 70)
print("Step 4: Create Delta Table")
print("=" * 70)
print()
print("Now SSH to your remote server and run:")
print()
print(f"  ssh user@{lakehouse_host}")
print(f"  cd /path/to/lakehouse")
print(f"  python server/create_delta_table.py \\")
print(f"      {s3_uri} \\")
print(f"      main \\")
print(f"      default \\")
print(f"      products")
print()

# Wait for user
input("Press Enter after creating the Delta table on the server...")
print()

# Query the data
print("=" * 70)
print("Step 5: Querying via Trino")
print("=" * 70)
print()

try:
    # List tables
    print("Listing tables...")
    tables = client.list_tables('delta', 'main.default')
    print(f"Tables: {tables}")
    print()

    if 'products' in tables or True:  # Try anyway
        # Query data
        print("Querying products table...")
        df = client.query_to_dataframe(
            "SELECT * FROM delta.main.default.products"
        )
        print("\nData:")
        print(df)
        print()

        # Aggregate query
        print("Sales by region:")
        summary = client.query_to_dataframe("""
            SELECT region, SUM(sales) as total_sales
            FROM delta.main.default.products
            GROUP BY region
            ORDER BY total_sales DESC
        """)
        print(summary)
        print()

        print("=" * 70)
        print("✓ Success! All operations completed.")
        print("=" * 70)

except Exception as e:
    print(f"⚠ Error: {e}")
    print()
    print("Make sure:")
    print("1. Delta table was created on the server")
    print("2. Trino is running")
    print(f"3. LAKEHOUSE_HOST is set to: {lakehouse_host}")

client.close()
