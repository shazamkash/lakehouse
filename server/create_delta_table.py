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
from delta import configure_spark_with_delta_pip

# Create Spark session
builder = SparkSession.builder.appName("CreateDeltaTable")

spark = configure_spark_with_delta_pip(builder).getOrCreate()

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

# Create catalog and schema if they don't exist
try:
    spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")
    print(f"Catalog '{catalog}' is ready")
except Exception as e:
    print(f"Catalog note: {{e}}")

try:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
    print(f"Schema '{catalog}.{schema}' is ready")
except Exception as e:
    print(f"Schema note: {{e}}")

# Register table
full_table_name = f"{catalog}.{schema}.{table}"
spark.sql(f"DROP TABLE IF EXISTS {{full_table_name}}")

create_table_sql = f\\"\\"\\"
CREATE TABLE {{full_table_name}}
USING DELTA
LOCATION '{{delta_path}}'
\\"\\"\\"

spark.sql(create_table_sql)
print(f"Table registered: {{full_table_name}}")

# Show table info
print("\\nTable info:")
spark.sql(f"DESCRIBE EXTENDED {{full_table_name}}").show(truncate=False)

print(f"\\nDelta table created successfully: {{full_table_name}}")
print(f"Location: {{delta_path}}")

spark.stop()
"""

    # Save PySpark code to temporary file
    script_path = f"/tmp/create_delta_{table}.py"

    print(f"Creating Delta table: {catalog}.{schema}.{table}")
    print(f"Source: {s3_path}")
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
    exec_cmd = [
        "docker", "exec", "lakehouse-spark-master",
        "spark-submit",
        "--master", "local[*]",
        "--conf", "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension",
        "--conf", "spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog",
        "--packages", "io.delta:delta-core_2.12:2.4.0",
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
