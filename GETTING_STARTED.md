# Getting Started with Lakehouse

This guide will walk you through setting up and using the Lakehouse platform.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.9 or higher
- At least 8GB RAM allocated to Docker

## Step 1: Start the Lakehouse Services

Start all services using Docker Compose:

```bash
docker-compose up -d
```

This will start:
- MinIO (S3-compatible storage)
- Spark Master and Worker
- Unity Catalog
- Trino

Wait for all services to be healthy (this may take 1-2 minutes):

```bash
docker-compose ps
```

## Step 2: Install the Python Client

```bash
cd client
pip install -e .
```

Or install directly from the root:

```bash
pip install -e ./client
```

## Step 3: Verify the Setup

Check that all services are accessible:

### MinIO Console
Open http://localhost:9001 in your browser
- Username: minioadmin
- Password: minioadmin

### Spark Master UI
Open http://localhost:8080

### Trino UI
Open http://localhost:8082

### Unity Catalog
The Unity Catalog API is available at http://localhost:8081

## Step 4: Run Your First Example

```bash
cd examples
python quickstart.py
```

This will:
1. Create sample data
2. Upload it to MinIO as Parquet
3. Create a Delta table
4. Register it in Unity Catalog
5. Query it via Trino

## Step 5: Explore More Examples

### Basic Usage
Comprehensive examples of all client features:
```bash
python basic_usage.py
```

### Advanced Usage
Partitioning, optimization, views, and analytics:
```bash
python advanced_usage.py
```

## Using the Python Client

### Simple Example

```python
from lakehouse_client import LakehouseClient

# Initialize
client = LakehouseClient()

# Upload data
s3_uri = client.upload_parquet('data.csv', 'raw-data', 'my-data')

# Create Delta table
client.create_delta_table(
    s3_path=s3_uri,
    catalog='main',
    schema='default',
    table='my_table'
)

# Query
results = client.query_to_dataframe("SELECT * FROM delta.main.default.my_table")
print(results)
```

### One-Step Workflow

```python
# Upload + Create Table + Register in Unity Catalog
result = client.ingest_and_create_table(
    file_path='data.csv',
    bucket='raw-data',
    catalog='main',
    schema='default',
    table='my_table'
)
```

## Common Operations

### List Available Data

```python
# List catalogs
catalogs = client.list_catalogs()

# List schemas
schemas = client.list_schemas('delta')

# List tables
tables = client.list_tables('delta', 'main.default')
```

### Table Metadata

```python
# Describe table structure
structure = client.describe_table('my_table', 'delta', 'main.default')

# Get table statistics
stats = client.get_table_stats('my_table', 'delta', 'main.default')
print(f"Rows: {stats['row_count']}")
```

### Optimize Tables

```python
# Compact small files
client.optimize_table('main', 'default', 'my_table')

# Clean up old versions
client.vacuum_table('main', 'default', 'my_table', retention_hours=168)
```

## Architecture Overview

```
Your Data (CSV/JSON/Parquet)
          ↓
    Python Client
          ↓
    MinIO (S3 Storage)
          ↓
    Spark (Process & Create Delta Tables)
          ↓
    Unity Catalog (Register Tables)
          ↓
    Trino (Query Engine)
          ↓
    Query Results
```

## Troubleshooting

### Services Not Starting

Check logs:
```bash
docker-compose logs <service-name>
```

### Connection Errors

Ensure all services are running:
```bash
docker-compose ps
```

Restart services if needed:
```bash
docker-compose restart
```

### Python Dependencies

If you encounter import errors:
```bash
pip install -r client/requirements.txt
```

### Port Conflicts

If ports 8080, 8081, 8082, 9000, or 9001 are already in use, modify `docker-compose.yml` to use different ports.

## Stopping the Services

```bash
docker-compose down
```

To remove all data:
```bash
docker-compose down -v
```

## Next Steps

- Read the full API documentation in the client README
- Explore advanced examples
- Check out the architecture diagram in the main README
- Integrate the client into your data pipelines

## Support

For issues and questions:
- Check the troubleshooting section
- Review example scripts
- Open an issue on GitHub
