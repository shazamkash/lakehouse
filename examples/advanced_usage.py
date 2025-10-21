"""
Advanced usage example demonstrating partitioning, optimization, and views.
"""

from lakehouse_client import LakehouseClient
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_time_series_data(num_records=10000):
    """Generate sample time series data."""
    start_date = datetime(2024, 1, 1)
    dates = [start_date + timedelta(days=i % 365) for i in range(num_records)]

    data = pd.DataFrame({
        'timestamp': dates,
        'year': [d.year for d in dates],
        'month': [d.month for d in dates],
        'day': [d.day for d in dates],
        'sensor_id': np.random.randint(1, 11, num_records),
        'temperature': np.random.normal(20, 5, num_records),
        'humidity': np.random.normal(60, 10, num_records),
        'pressure': np.random.normal(1013, 20, num_records),
    })

    return data


def main():
    print("Advanced Lakehouse Usage Examples")
    print("=" * 60)

    # Initialize client
    client = LakehouseClient()

    # Example 1: Partitioned Delta Tables
    print("\nExample 1: Creating Partitioned Delta Table")
    print("-" * 60)

    # Generate time series data
    sensor_data = generate_time_series_data(10000)
    sensor_data.to_csv('sensor_data.csv', index=False)

    print(f"Generated {len(sensor_data)} sensor readings")

    # Upload to MinIO
    s3_uri = client.upload_parquet(
        file_path='sensor_data.csv',
        bucket='raw-data',
        object_name='sensor_data',
    )

    # Create partitioned Delta table
    delta_path = client.create_delta_table(
        s3_path=s3_uri,
        catalog='main',
        schema='analytics',
        table='sensor_readings',
        partition_by=['year', 'month'],  # Partition by year and month
    )

    print(f"Created partitioned table: main.analytics.sensor_readings")
    print(f"Partitioned by: year, month")

    # Example 2: Querying Partitioned Data
    print("\n\nExample 2: Efficient Queries on Partitioned Data")
    print("-" * 60)

    # Query specific partition (much faster due to partition pruning)
    monthly_avg = client.query_to_dataframe("""
        SELECT
            year,
            month,
            AVG(temperature) as avg_temp,
            AVG(humidity) as avg_humidity,
            AVG(pressure) as avg_pressure,
            COUNT(*) as reading_count
        FROM delta.main.analytics.sensor_readings
        WHERE year = 2024 AND month = 6
        GROUP BY year, month
    """)

    print("\nJune 2024 averages:")
    print(monthly_avg)

    # Example 3: Creating Views
    print("\n\nExample 3: Creating Views")
    print("-" * 60)

    # Create a view for high temperature readings
    client.query_engine.create_view(
        view_name='high_temp_readings',
        sql="""
            SELECT
                timestamp,
                sensor_id,
                temperature,
                humidity,
                pressure
            FROM delta.main.analytics.sensor_readings
            WHERE temperature > 25
        """,
        catalog='delta',
        schema='main.analytics',
    )

    print("Created view: high_temp_readings")

    # Query the view
    high_temp_count = client.query_to_dataframe("""
        SELECT sensor_id, COUNT(*) as high_temp_count
        FROM delta.main.analytics.high_temp_readings
        GROUP BY sensor_id
        ORDER BY high_temp_count DESC
    """)

    print("\nHigh temperature readings by sensor:")
    print(high_temp_count)

    # Example 4: Table Optimization
    print("\n\nExample 4: Table Optimization")
    print("-" * 60)

    # Get table stats before optimization
    stats_before = client.get_table_stats('sensor_readings', 'delta', 'main.analytics')
    print(f"Rows in table: {stats_before.get('row_count')}")

    # Optimize the table (compact small files)
    print("\nOptimizing table...")
    client.optimize_table('main', 'analytics', 'sensor_readings')
    print("Table optimized - small files compacted")

    # Example 5: Incremental Data Load (Append Mode)
    print("\n\nExample 5: Incremental Data Load")
    print("-" * 60)

    # Generate more data
    new_data = generate_time_series_data(1000)
    new_data.to_csv('new_sensor_data.csv', index=False)

    # Upload to MinIO
    new_s3_uri = client.upload_parquet(
        file_path='new_sensor_data.csv',
        bucket='raw-data',
        object_name='sensor_data_new',
    )

    # Append to existing Delta table
    client.delta.create_delta_table(
        s3_path=new_s3_uri,
        catalog='main',
        schema='analytics',
        table='sensor_readings',
        mode='append',  # Append mode instead of overwrite
        partition_by=['year', 'month'],
    )

    print("Appended 1000 new records to table")

    # Verify new count
    stats_after = client.get_table_stats('sensor_readings', 'delta', 'main.analytics')
    print(f"New row count: {stats_after.get('row_count')}")

    # Example 6: Complex Analytics Query
    print("\n\nExample 6: Complex Analytics")
    print("-" * 60)

    analytics_query = """
        WITH monthly_stats AS (
            SELECT
                year,
                month,
                sensor_id,
                AVG(temperature) as avg_temp,
                STDDEV(temperature) as std_temp,
                MIN(temperature) as min_temp,
                MAX(temperature) as max_temp
            FROM delta.main.analytics.sensor_readings
            GROUP BY year, month, sensor_id
        )
        SELECT
            sensor_id,
            COUNT(*) as months_active,
            AVG(avg_temp) as overall_avg_temp,
            AVG(std_temp) as avg_variation,
            MIN(min_temp) as all_time_low,
            MAX(max_temp) as all_time_high
        FROM monthly_stats
        GROUP BY sensor_id
        ORDER BY sensor_id
    """

    analytics_result = client.query_to_dataframe(analytics_query)
    print("\nSensor Analytics:")
    print(analytics_result)

    # Example 7: Data Quality Checks
    print("\n\nExample 7: Data Quality Checks")
    print("-" * 60)

    quality_checks = client.query_to_dataframe("""
        SELECT
            COUNT(*) as total_records,
            COUNT(DISTINCT sensor_id) as unique_sensors,
            SUM(CASE WHEN temperature IS NULL THEN 1 ELSE 0 END) as null_temp,
            SUM(CASE WHEN humidity IS NULL THEN 1 ELSE 0 END) as null_humidity,
            SUM(CASE WHEN temperature < -50 OR temperature > 50 THEN 1 ELSE 0 END) as outlier_temp,
            SUM(CASE WHEN humidity < 0 OR humidity > 100 THEN 1 ELSE 0 END) as outlier_humidity
        FROM delta.main.analytics.sensor_readings
    """)

    print("\nData Quality Report:")
    print(quality_checks)

    # Example 8: Working with Multiple File Formats
    print("\n\nExample 8: Multiple Format Support")
    print("-" * 60)

    # JSON data
    json_data = [
        {'id': 1, 'product': 'Laptop', 'price': 999.99},
        {'id': 2, 'product': 'Mouse', 'price': 29.99},
        {'id': 3, 'product': 'Keyboard', 'price': 79.99},
    ]

    json_df = pd.DataFrame(json_data)
    json_df.to_json('products.json', orient='records', lines=True)

    # Upload and create table from JSON
    result = client.ingest_and_create_table(
        file_path='products.json',
        bucket='raw-data',
        catalog='main',
        schema='sales',
        table='products',
    )

    print(f"Created table from JSON: {result['table']}")

    # Query the products
    products = client.query_to_dataframe("SELECT * FROM delta.main.sales.products")
    print("\nProducts:")
    print(products)

    # Example 9: List All Tables
    print("\n\nExample 9: Catalog Exploration")
    print("-" * 60)

    print("\nAll catalogs:")
    for catalog in client.list_catalogs():
        print(f"  {catalog}")

    print("\nSchemas in 'delta' catalog:")
    try:
        for schema in client.list_schemas('delta'):
            print(f"  {schema}")
            tables = client.list_tables('delta', schema)
            if tables:
                for table in tables:
                    print(f"    - {table}")
    except Exception as e:
        print(f"  (Error listing schemas: {e})")

    print("\n" + "=" * 60)
    print("Advanced Examples Complete!")
    print("=" * 60)

    # Cleanup
    client.close()


if __name__ == "__main__":
    main()
