# Server-Side Scripts

These scripts run **on the remote server** (10.16.36.36) and perform operations that would otherwise require Java to be installed on the client machine.

## create_delta_table.py

Creates Delta tables from Parquet files in MinIO by executing PySpark code inside the Spark Docker container.

### Usage

```bash
python create_delta_table.py <s3_path> <catalog> <schema> <table> [--mode MODE]
```

### Parameters

- `s3_path`: S3 path to source Parquet file (e.g., `s3a://raw-data/products.parquet`)
- `catalog`: Catalog name (e.g., `main`)
- `schema`: Schema name (e.g., `default`)
- `table`: Table name (e.g., `products`)
- `--mode`: Write mode - `overwrite` (default) or `append`

### Examples

#### Create New Table

```bash
python create_delta_table.py \\
    s3a://raw-data/products.parquet \\
    main \\
    default \\
    products
```

#### Append to Existing Table

```bash
python create_delta_table.py \\
    s3a://raw-data/new_products.parquet \\
    main \\
    default \\
    products \\
    --mode append
```

### How It Works

1. Generates PySpark code to read Parquet and create Delta table
2. Writes the code to a temporary file inside the Spark container
3. Executes the code using `spark-submit` in the container
4. Creates catalog and schema if they don't exist
5. Registers the table in Unity Catalog

### Requirements

- Docker must be running
- Lakehouse services must be started (`docker-compose up -d`)
- Source Parquet file must exist in MinIO

### Complete Workflow

#### On Your Local Machine

```python
from lakehouse_client import SimpleLakehouseClient

client = SimpleLakehouseClient()

# Upload data to MinIO
s3_uri = client.upload_parquet('data.csv', 'raw-data', 'my_data')
print(f"Uploaded to: {s3_uri}")
# Output: s3a://raw-data/my_data.parquet
```

#### On the Remote Server (10.16.36.36)

```bash
# SSH to server
ssh user@10.16.36.36

# Navigate to lakehouse directory
cd /path/to/lakehouse

# Create Delta table
python server/create_delta_table.py \\
    s3a://raw-data/my_data.parquet \\
    main \\
    default \\
    my_data
```

#### Back on Your Local Machine

```python
# Query the data
results = client.query_to_dataframe(
    "SELECT * FROM delta.main.default.my_data"
)
print(results)
```

### Output

The script provides detailed output:

```
Creating Delta table: main.default.products
Source: s3a://raw-data/products.parquet
Mode: overwrite

Script written to container: /tmp/create_delta_products.py
Executing Spark job...

Reading data from s3a://raw-data/products.parquet
Schema:
root
 |-- product: string (nullable = true)
 |-- sales: long (nullable = true)
 |-- region: string (nullable = true)

Writing Delta table to s3a://warehouse/main/default/products
Catalog 'main' is ready
Schema 'main.default' is ready
Table registered: main.default.products

Table info:
+--------------------+--------------------+-------+
|col_name            |data_type           |comment|
+--------------------+--------------------+-------+
|product             |string              |null   |
|sales               |bigint              |null   |
|region              |string              |null   |
+--------------------+--------------------+-------+

Delta table created successfully: main.default.products
Location: s3a://warehouse/main/default/products

✓ Delta table created successfully!
```

### Troubleshooting

#### Container Not Found

```
Error: No such container: lakehouse-spark-master
```

**Solution**: Start the services
```bash
docker-compose up -d
```

#### S3 File Not Found

```
AnalysisException: Path does not exist: s3a://raw-data/file.parquet
```

**Solution**: Verify the file was uploaded
```python
from lakehouse_client import SimpleLakehouseClient
client = SimpleLakehouseClient()
files = client.list_objects('raw-data')
print(files)
```

#### Permission Denied

```
Error writing script: Permission denied
```

**Solution**: Ensure Docker is running and accessible
```bash
docker ps
```

### Advanced Usage

#### With Partitioning

Currently, the script doesn't support partitioning. To create partitioned tables, modify the PySpark code in the script:

```python
# In create_delta_table.py, modify the write line:
df.write.format("delta") \\
    .mode("{mode}") \\
    .partitionBy("year", "month") \\  # Add this
    .save(delta_path)
```

#### Custom Spark Configuration

To add custom Spark configuration:

```bash
# Edit the exec_cmd in create_delta_table.py
exec_cmd = [
    "docker", "exec", "lakehouse-spark-master",
    "spark-submit",
    "--master", "local[*]",
    "--conf", "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension",
    "--conf", "spark.executor.memory=4g",  # Add custom configs
    "--conf", "spark.driver.memory=2g",
    "--packages", "io.delta:delta-core_2.12:2.4.0",
    script_path
]
```

## Future Scripts

Planned server-side scripts:

- `optimize_table.py` - Run OPTIMIZE on Delta tables
- `vacuum_table.py` - Run VACUUM on Delta tables
- `merge_data.py` - Perform Delta MERGE operations
- `create_view.py` - Create Trino views

## Why Server-Side Scripts?

**Problem**: PySpark requires Java to be installed on the client machine

**Solution**: Run Spark operations on the server where Spark is already running in Docker

**Benefits**:
- ✓ No Java installation required on client
- ✓ Works from any machine (Windows, Mac, Linux)
- ✓ Leverages existing Spark cluster
- ✓ Consistent environment

**Trade-off**:
- Must SSH to server to run scripts
- Less convenient than all-local operations

For local development where you have Java installed, you can use the full `LakehouseClient` which includes Delta operations without needing these scripts.

See [JAVA_SETUP.md](../JAVA_SETUP.md) for more information about Java requirements and alternatives.
