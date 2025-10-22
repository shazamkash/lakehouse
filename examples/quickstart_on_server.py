"""
Quickstart for Running ON THE SERVER

This script is designed to run ON the server (10.16.36.36) where Docker services are deployed.
It uses SimpleLakehouseClient to avoid creating a local Spark session, and instead uses
the server-side script to interact with the Spark Docker containers.

Usage:
    python quickstart_on_server.py
"""

import subprocess
import pandas as pd
from lakehouse_client import SimpleLakehouseClient

print("=" * 70)
print("Lakehouse Quickstart - Running ON Server")
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

# Initialize SimpleLakehouseClient
# Since we're on the server, use localhost
print("Step 2: Initializing client (connecting to localhost services)...")
client = SimpleLakehouseClient(
    minio_endpoint="http://localhost:9000",
    trino_host="localhost",
    trino_port=8082
)
print("✓ Client initialized")
print()

# Upload to MinIO
print("Step 3: Uploading to MinIO...")
s3_uri = client.upload_parquet(
    file_path='products.csv',
    bucket='raw-data',
    object_name='products'
)
print(f"✓ Uploaded to: {s3_uri}")
print()

# Create Delta table using server-side script
print("Step 4: Creating Delta table via Spark container...")
print()

create_cmd = [
    'python',
    'server/create_delta_table.py',
    s3_uri,
    'main',
    'default',
    'products'
]

print(f"Running: {' '.join(create_cmd)}")
print()

try:
    result = subprocess.run(
        create_cmd,
        check=True,
        capture_output=False  # Show output in real-time
    )
    print()
    print("✓ Delta table created successfully")
except subprocess.CalledProcessError as e:
    print()
    print(f"✗ Error creating Delta table: {e}")
    print("Make sure Docker services are running: docker-compose ps")
    exit(1)

print()

# Query the data
print("Step 5: Querying data via Trino...")
print()

try:
    # Note: Tables are discovered by Trino via file-based metastore
    # Query format: delta.schema.table

    # Query all data
    print("Query 1: All products")
    df = client.query_to_dataframe(
        "SELECT * FROM delta.default.products"
    )
    print(df)
    print()

    # Aggregate query
    print("Query 2: Sales by region")
    summary = client.query_to_dataframe("""
        SELECT region, SUM(sales) as total_sales
        FROM delta.default.products
        GROUP BY region
        ORDER BY total_sales DESC
    """)
    print(summary)
    print()

    print("=" * 70)
    print("✓ Success! All operations completed.")
    print("=" * 70)

except Exception as e:
    print(f"✗ Error querying data: {e}")
    print()
    print("Troubleshooting:")
    print("1. Check Trino is running: docker-compose ps trino")
    print("2. Check Trino logs: docker-compose logs trino")
    print("3. Verify table exists: docker exec lakehouse-trino trino --execute 'SHOW TABLES FROM delta.default'")

finally:
    client.close()

print()
print("Workflow Summary:")
print("1. ✓ Created sample data")
print("2. ✓ Uploaded to MinIO (localhost:9000)")
print("3. ✓ Created Delta table (via Spark container)")
print("4. ✓ Queried data (via Trino at localhost:8082)")
print()
print("All operations completed using localhost services!")
