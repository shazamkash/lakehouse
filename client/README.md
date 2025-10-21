# Lakehouse Client

Python client library for interacting with the Lakehouse platform.

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from lakehouse_client import LakehouseClient

# Initialize the client
client = LakehouseClient(
    minio_endpoint="http://localhost:9000",
    minio_access_key="minioadmin",
    minio_secret_key="minioadmin",
    spark_master="spark://localhost:7077",
    trino_host="localhost",
    trino_port=8082,
    unity_catalog_url="http://localhost:8081"
)

# Upload a file as Parquet
client.upload_parquet(
    file_path="data.csv",
    bucket="raw-data",
    object_name="my-dataset"
)

# Create a Delta table from S3 data
client.create_delta_table(
    s3_path="s3a://raw-data/my-dataset.parquet",
    catalog="main",
    schema="default",
    table="my_table"
)

# Query the Delta table
results = client.query("SELECT * FROM delta.main.default.my_table LIMIT 10")
for row in results:
    print(row)
```

## Features

- Upload CSV/JSON/Parquet files to MinIO as Parquet
- Convert S3 objects to Delta tables
- Register tables in Unity Catalog
- Query Delta tables using Trino
- Full type hints and documentation

## API Reference

See the main documentation for detailed API reference.
