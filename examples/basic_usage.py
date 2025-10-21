"""
Basic usage example for the Lakehouse Client.

This script demonstrates:
1. Uploading a data file as Parquet to MinIO
2. Creating a Delta table from the Parquet file
3. Registering the table in Unity Catalog
4. Querying the table via Trino

For remote server deployment:
- Set environment variable: export LAKEHOUSE_HOST=10.16.36.36
- Or pass explicit parameters to LakehouseClient()
"""

from lakehouse_client import LakehouseClient
import pandas as pd

# Optional: Load environment variables from .env file
# from dotenv import load_dotenv
# load_dotenv()


def main():
    # Initialize the client
    print("Initializing Lakehouse Client...")

    # Option 1: Use environment variables (recommended for remote deployment)
    # Just set LAKEHOUSE_HOST and the client will configure automatically
    client = LakehouseClient()

    # Option 2: Explicit configuration (uncomment to use)
    # client = LakehouseClient(
    #     minio_endpoint="http://10.16.36.36:9000",
    #     minio_access_key="minioadmin",
    #     minio_secret_key="minioadmin",
    #     spark_master="spark://10.16.36.36:7077",
    #     trino_host="10.16.36.36",
    #     trino_port=8082,
    #     unity_catalog_url="http://10.16.36.36:8081",
    # )

    # Example 1: Create and upload a sample dataset
    print("\n" + "="*60)
    print("Example 1: Upload Data to MinIO")
    print("="*60)

    # Create sample data
    sample_data = pd.DataFrame({
        'id': range(1, 101),
        'name': [f'User_{i}' for i in range(1, 101)],
        'age': [20 + (i % 50) for i in range(1, 101)],
        'city': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'] * 20,
        'score': [75 + (i % 25) for i in range(1, 101)],
    })

    # Save to CSV
    sample_data.to_csv('sample_data.csv', index=False)
    print("Created sample dataset with 100 rows")

    # Upload as Parquet to MinIO
    s3_uri = client.upload_parquet(
        file_path='sample_data.csv',
        bucket='raw-data',
        object_name='users',
    )
    print(f"Uploaded to: {s3_uri}")

    # Example 2: Create Delta Table
    print("\n" + "="*60)
    print("Example 2: Create Delta Table")
    print("="*60)

    delta_path = client.create_delta_table(
        s3_path=s3_uri,
        catalog='main',
        schema='default',
        table='users',
    )
    print(f"Delta table created at: {delta_path}")

    # Example 3: Query via Trino
    print("\n" + "="*60)
    print("Example 3: Query Delta Table")
    print("="*60)

    # Simple query
    print("\nQuery 1: Select first 5 rows")
    results_df = client.query_to_dataframe(
        "SELECT * FROM delta.main.default.users LIMIT 5"
    )
    print(results_df)

    # Aggregation query
    print("\nQuery 2: Count by city")
    city_counts = client.query_to_dataframe(
        "SELECT city, COUNT(*) as count FROM delta.main.default.users GROUP BY city"
    )
    print(city_counts)

    # Statistical query
    print("\nQuery 3: Average score by age group")
    age_stats = client.query_to_dataframe("""
        SELECT
            CASE
                WHEN age < 30 THEN '20s'
                WHEN age < 40 THEN '30s'
                WHEN age < 50 THEN '40s'
                ELSE '50+'
            END as age_group,
            AVG(score) as avg_score,
            COUNT(*) as count
        FROM delta.main.default.users
        GROUP BY 1
        ORDER BY age_group
    """)
    print(age_stats)

    # Example 4: Table Metadata
    print("\n" + "="*60)
    print("Example 4: Table Metadata")
    print("="*60)

    # List catalogs
    print("\nAvailable catalogs:")
    catalogs = client.list_catalogs()
    for catalog in catalogs:
        print(f"  - {catalog}")

    # Describe table
    print("\nTable structure:")
    table_desc = client.describe_table('users', 'delta', 'main.default')
    print(table_desc)

    # Table statistics
    print("\nTable statistics:")
    stats = client.get_table_stats('users', 'delta', 'main.default')
    print(f"  Row count: {stats.get('row_count')}")
    print(f"  Column count: {stats.get('columns')}")

    # Example 5: Complete Workflow (shortcut method)
    print("\n" + "="*60)
    print("Example 5: Complete Workflow (One-Step Ingest)")
    print("="*60)

    # Create another sample dataset
    transactions = pd.DataFrame({
        'transaction_id': range(1, 51),
        'user_id': [i % 100 + 1 for i in range(1, 51)],
        'amount': [100 + (i * 10) % 500 for i in range(1, 51)],
        'date': pd.date_range('2024-01-01', periods=50, freq='D'),
    })

    transactions.to_csv('transactions.csv', index=False)

    # Use the one-step ingest method
    result = client.ingest_and_create_table(
        file_path='transactions.csv',
        bucket='raw-data',
        catalog='main',
        schema='default',
        table='transactions',
    )

    print(f"S3 URI: {result['s3_uri']}")
    print(f"Delta path: {result['delta_path']}")
    print(f"Table: {result['table']}")

    # Query the new table
    print("\nQuerying transactions table:")
    txn_summary = client.query_to_dataframe("""
        SELECT
            COUNT(*) as total_transactions,
            SUM(amount) as total_amount,
            AVG(amount) as avg_amount,
            MIN(amount) as min_amount,
            MAX(amount) as max_amount
        FROM delta.main.default.transactions
    """)
    print(txn_summary)

    # Example 6: Join Query
    print("\n" + "="*60)
    print("Example 6: Join Query")
    print("="*60)

    join_query = """
        SELECT
            u.name,
            u.city,
            COUNT(t.transaction_id) as num_transactions,
            SUM(t.amount) as total_spent
        FROM delta.main.default.users u
        LEFT JOIN delta.main.default.transactions t ON u.id = t.user_id
        GROUP BY u.name, u.city
        HAVING COUNT(t.transaction_id) > 0
        ORDER BY total_spent DESC
        LIMIT 10
    """

    top_spenders = client.query_to_dataframe(join_query)
    print("\nTop 10 spenders:")
    print(top_spenders)

    print("\n" + "="*60)
    print("Demo Complete!")
    print("="*60)

    # Clean up
    client.close()


if __name__ == "__main__":
    main()
