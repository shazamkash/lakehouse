"""
Quickstart Example - No Java Required

This example uses SimpleLakehouseClient which only requires:
- MinIO (for data storage)
- Trino (for querying)

No local Java/Spark installation needed!

For Delta table creation, use the server-side script on the remote server:
    python server/create_delta_table.py s3a://raw-data/products.parquet main default products

Steps:
1. Upload data to MinIO (from local machine)
2. Create Delta table (on server via script)
3. Query data (from local machine)
"""

from lakehouse_client import SimpleLakehouseClient
import pandas as pd
import os

# Optional: Load environment variables from .env file
# from dotenv import load_dotenv
# load_dotenv()

print("=" * 70)
print("Lakehouse Quickstart - No Java Required")
print("=" * 70)
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

# Initialize simple client (no Java/Spark needed)
print("Step 2: Initializing client...")
print(f"LAKEHOUSE_HOST: {os.getenv('LAKEHOUSE_HOST', 'localhost')}")
client = SimpleLakehouseClient()
print("✓ Client initialized")
print()

# Upload to MinIO as Parquet
print("Step 3: Uploading data to MinIO...")
s3_uri = client.upload_parquet(
    file_path='products.csv',
    bucket='raw-data',
    object_name='products'
)
print(f"✓ Data uploaded to: {s3_uri}")
print()

# Instructions for Delta table creation
print("=" * 70)
print("Step 4: Create Delta Table (run this on the remote server)")
print("=" * 70)
print()
print("SSH into your server (10.16.36.36) and run:")
print()
print("  cd /path/to/lakehouse")
print(f"  python server/create_delta_table.py \\")
print(f"      {s3_uri} \\")
print(f"      main \\")
print(f"      default \\")
print(f"      products")
print()
print("This will create the Delta table in the Spark container.")
print()

# Wait for user confirmation
input("Press Enter after you've created the Delta table on the server...")
print()

# Query the data
print("=" * 70)
print("Step 5: Querying data via Trino")
print("=" * 70)
print()

try:
    print("Listing available tables...")
    tables = client.list_tables('delta', 'main.default')
    print(f"Tables in delta.main.default: {tables}")
    print()

    if 'products' in tables:
        print("Querying products table...")
        df = client.query_to_dataframe(
            "SELECT * FROM delta.main.default.products"
        )
        print("\nProducts data:")
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
    else:
        print("⚠ Table 'products' not found. Make sure you created it on the server.")
        print()

except Exception as e:
    print(f"⚠ Error querying data: {e}")
    print()
    print("Make sure:")
    print("1. The Delta table was created successfully")
    print("2. Trino is running and accessible")
    print()

print("=" * 70)
print("Summary")
print("=" * 70)
print()
print("✓ No Java required on local machine")
print("✓ Data uploaded to MinIO")
print("✓ Delta table created on server")
print("✓ Data queried via Trino")
print()
print("This workflow is perfect for remote deployments where you don't")
print("want to install Java/Spark locally.")
print()

client.close()
