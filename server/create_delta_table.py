#!/usr/bin/env python3
"""
Server-side script to create Delta tables.

This script runs ON THE SERVER (10.16.36.36) and creates Delta tables
from Parquet files in MinIO. It uses the Spark container directly,
avoiding the need for Java on the client machine.

Usage:
    python create_delta_table.py <s3_path> <catalog> <schema> <table>

Example:
    python create_delta_table.py \\
        s3a://raw-data/products.parquet \\
        main \\
        default \\
        products
"""

import sys
import subprocess
import argparse


def create_delta_table(s3_path, catalog, schema, table, mode="overwrite"):
    """
    Create a Delta table by executing PySpark code inside the Spark container.

    Args:
        s3_path: S3 path to source data (e.g., s3a://raw-data/file.parquet)
        catalog: Catalog name
        schema: Schema name
        table: Table name
        mode: Write mode (overwrite, append)
    """

    # PySpark code to create Delta table
    pyspark_code = f"""
from pyspark.sql import SparkSession

# Create Spark session with Delta Lake, S3/MinIO, and Unity Catalog configuration
# Unity Catalog provides centralized metadata management and governance
# JARs are already pre-loaded in /opt/bitnami/spark/jars/
spark = SparkSession.builder \\
    .appName("CreateDeltaTable") \\
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \\
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \\
    .config("spark.sql.catalog.unity", "io.unitycatalog.spark.UCSingleCatalog") \\
    .config("spark.sql.catalog.unity.uri", "http://unity-catalog:8080") \\
    .config("spark.sql.defaultCatalog", "unity") \\
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \\
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \\
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \\
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \\
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \\
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \\
    .config("spark.sql.warehouse.dir", "s3a://warehouse/") \\
    .getOrCreate()

# Read source data
print(f"Reading data from {s3_path}")
df = spark.read.parquet("{s3_path}")

# Show schema
print("Schema:")
df.printSchema()

# Construct Delta table path
delta_path = f"s3a://warehouse/{catalog}/{schema}/{table}"

print(f"Writing Delta table to {{delta_path}}")
df.write.format("delta").mode("{mode}").save(delta_path)

# Create schema in Unity Catalog if it doesn't exist
try:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS unity.{schema}")
    print(f"\\nSchema 'unity.{schema}' ready in Unity Catalog")
except Exception as e:
    print(f"\\nSchema creation note: {{e}}")

# Register table in Unity Catalog
# Using three-level namespace: catalog.schema.table
full_table_name = f"unity.{schema}.{table}"

try:
    spark.sql(f"DROP TABLE IF EXISTS {{full_table_name}}")
    print(f"Dropped existing table if present: {{full_table_name}}")
except Exception as e:
    print(f"Drop table note: {{e}}")

# Create external table pointing to Delta location
create_table_sql = f'''
CREATE TABLE {{full_table_name}}
USING DELTA
LOCATION '{{delta_path}}'
'''

spark.sql(create_table_sql)
print(f"\\nTable registered in Unity Catalog: {{full_table_name}}")

# Show table info
print("\\nTable info:")
spark.sql(f"DESCRIBE EXTENDED {{full_table_name}}").show(20, truncate=False)

# Show sample data
print("\\nSample data (first 5 rows):")
spark.sql(f"SELECT * FROM {{full_table_name}} LIMIT 5").show(truncate=False)

print(f"\\nDelta table created successfully!")
print(f"Storage location: {{delta_path}}")
print(f"Unity Catalog table: {{full_table_name}}")
print(f"Query via Trino: SELECT * FROM unity.{schema}.{table}")

spark.stop()
"""

    # Save PySpark code to temporary file
    script_path = f"/tmp/create_delta_{table}.py"

    print(f"Creating Delta table in Unity Catalog")
    print(f"Unity Catalog table: unity.{schema}.{table}")
    print(f"Source: {s3_path}")
    print(f"Storage: s3a://warehouse/{catalog}/{schema}/{table}")
    print(f"Mode: {mode}")
    print()

    # Write script to container
    write_cmd = [
        "docker", "exec", "-i", "lakehouse-spark-master",
        "bash", "-c", f"cat > {script_path}"
    ]

    try:
        subprocess.run(
            write_cmd,
            input=pyspark_code.encode(),
            check=True,
            capture_output=True
        )
        print(f"Script written to container: {script_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error writing script: {e}")
        print(f"stderr: {e.stderr.decode()}")
        return False

    # Execute PySpark script in container
    # Note: Delta Lake 3.3.0 JARs are pre-installed in the Docker image (no download needed)
    exec_cmd = [
        "docker", "exec", "lakehouse-spark-master",
        "spark-submit",
        "--master", "local[*]",
        "--conf", "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension",
        "--conf", "spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog",
        # JARs are pre-loaded in /opt/bitnami/spark/jars/ - no --packages needed
        script_path
    ]

    print("Executing Spark job...")
    print()

    try:
        result = subprocess.run(
            exec_cmd,
            check=True,
            capture_output=False  # Show output in real-time
        )
        print()
        print("✓ Delta table created successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print()
        print(f"✗ Error creating Delta table")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Create Delta tables from Parquet files in MinIO"
    )
    parser.add_argument(
        "s3_path",
        help="S3 path to source data (e.g., s3a://raw-data/file.parquet)"
    )
    parser.add_argument("catalog", help="Catalog name (e.g., main)")
    parser.add_argument("schema", help="Schema name (e.g., default)")
    parser.add_argument("table", help="Table name (e.g., products)")
    parser.add_argument(
        "--mode",
        default="overwrite",
        choices=["overwrite", "append"],
        help="Write mode (default: overwrite)"
    )

    args = parser.parse_args()

    success = create_delta_table(
        args.s3_path,
        args.catalog,
        args.schema,
        args.table,
        args.mode
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
