# Deployment Scenarios Guide

This guide explains how to use the Lakehouse platform in different deployment scenarios.

## Scenario 1: Running Client ON the Server (Your Current Setup)

**Setup:**
- Server: 10.16.36.36
- Docker services running on: 10.16.36.36
- Python client running on: 10.16.36.36 (same server)

### ✅ Correct Approach

Use `SimpleLakehouseClient` + `server/create_delta_table.py`:

```python
from lakehouse_client import SimpleLakehouseClient

# Connect to localhost since you're on the same server
client = SimpleLakehouseClient(
    minio_endpoint="http://localhost:9000",
    trino_host="localhost",
    trino_port=8082
)

# Upload data
s3_uri = client.upload_parquet('data.csv', 'raw-data', 'dataset')

# Create Delta table using the server script
import subprocess
subprocess.run([
    'python', 'server/create_delta_table.py',
    s3_uri, 'main', 'default', 'my_table'
])

# Query data
results = client.query_to_dataframe("SELECT * FROM delta.main.default.my_table")
```

### 📝 Complete Example

```bash
# On the server (10.16.36.36)
cd /path/to/lakehouse
python examples/quickstart_on_server.py
```

### ❌ What NOT to Do

**DON'T use `LakehouseClient`** - It will try to:
1. Create a local Spark session
2. Download Delta Lake JARs from Maven
3. Hang indefinitely if no internet access

```python
# ❌ WRONG - Will hang!
from lakehouse_client import LakehouseClient
client = LakehouseClient()  # Tries to create local Spark session
```

---

## Scenario 2: Running Client from Your Laptop (Remote Access)

**Setup:**
- Server: 10.16.36.36
- Docker services running on: 10.16.36.36
- Python client running on: Your laptop

### ✅ Correct Approach

Use `SimpleLakehouseClient` with `LAKEHOUSE_HOST` environment variable:

```bash
# On your laptop
export LAKEHOUSE_HOST=10.16.36.36
```

```python
from lakehouse_client import SimpleLakehouseClient

# Will automatically connect to 10.16.36.36
client = SimpleLakehouseClient()

# Upload data (from laptop to remote MinIO)
s3_uri = client.upload_parquet('data.csv', 'raw-data', 'dataset')
print(f"File uploaded to remote server: {s3_uri}")

# For Delta table creation, SSH to server and run:
# ssh user@10.16.36.36
# python server/create_delta_table.py s3a://raw-data/dataset.parquet main default my_table

# Query data (from laptop to remote Trino)
results = client.query_to_dataframe("SELECT * FROM delta.main.default.my_table")
```

### 📝 Complete Example

```bash
# On your laptop
export LAKEHOUSE_HOST=10.16.36.36
cd /path/to/lakehouse
python examples/quickstart_remote.py
```

### ❌ What NOT to Do

**DON'T use `LakehouseClient`** without Java 17+ installed:

```python
# ❌ WRONG - Requires Java 17+ on your laptop
from lakehouse_client import LakehouseClient
client = LakehouseClient()
```

---

## Scenario 3: Local Development (All on Localhost)

**Setup:**
- Server: localhost
- Docker services running on: localhost
- Python client running on: localhost

### ✅ Approach A: SimpleLakehouseClient (Recommended)

```python
from lakehouse_client import SimpleLakehouseClient

# Everything runs on localhost
client = SimpleLakehouseClient()

# Upload, create table, query
s3_uri = client.upload_parquet('data.csv', 'raw-data', 'dataset')

# Create Delta table
import subprocess
subprocess.run([
    'python', 'server/create_delta_table.py',
    s3_uri, 'main', 'default', 'my_table'
])

results = client.query_to_dataframe("SELECT * FROM delta.main.default.my_table")
```

### ✅ Approach B: LakehouseClient (If You Have Java 17+)

```python
from lakehouse_client import LakehouseClient

# Requires Java 17+ installed
client = LakehouseClient()

# Full functionality
s3_uri = client.upload_parquet('data.csv', 'raw-data', 'dataset')
client.create_delta_table(s3_uri, 'main', 'default', 'my_table')
results = client.query_to_dataframe("SELECT * FROM delta.main.default.my_table")
```

---

## Decision Matrix

| Where Client Runs | Where Docker Runs | Use | Configuration |
|-------------------|-------------------|-----|---------------|
| Server (10.16.36.36) | Same server | `SimpleLakehouseClient` | `localhost` endpoints |
| Laptop | Remote server (10.16.36.36) | `SimpleLakehouseClient` | `LAKEHOUSE_HOST=10.16.36.36` |
| Localhost | Localhost | `SimpleLakehouseClient` | Default (localhost) |
| Localhost | Localhost | `LakehouseClient` | Default + Java 17+ |

---

## Your Current Issue Explained

### What's Happening

You're running this code **ON the server** (10.16.36.36):

```python
from lakehouse_client import LakehouseClient  # ❌ Wrong choice

client = LakehouseClient()
```

The `LakehouseClient`:
1. Tries to create a **local Spark session** on your server
2. Attempts to download Delta Lake JARs from Maven:
   ```
   io.delta#delta-spark_2.13 added as a dependency
   :: resolving dependencies ::
   ```
3. **Hangs** because:
   - No internet access to download JARs, OR
   - Maven repository is slow/unreachable, OR
   - Firewall blocking Maven Central

### Solution

Switch to `SimpleLakehouseClient`:

```python
from lakehouse_client import SimpleLakehouseClient  # ✅ Correct

# Connect to localhost (same server)
client = SimpleLakehouseClient(
    minio_endpoint="http://localhost:9000",
    trino_host="localhost"
)
```

And use the server-side script for Delta tables:

```bash
python server/create_delta_table.py \
    s3a://raw-data/products.parquet \
    main \
    default \
    products
```

---

## Step-by-Step Fix for Your Current Situation

### Step 1: Stop the Hanging Process

```bash
# Press Ctrl+C to stop the hanging script
^C
```

### Step 2: Use the Correct Example

```bash
# On the server (10.16.36.36)
cd /path/to/lakehouse

# Pull latest code
git pull origin claude/lakehouse-as-a-service-011CULDtY8bng5zaJbPADrb9

# Run the correct example
python examples/quickstart_on_server.py
```

This script:
- ✅ Uses `SimpleLakehouseClient` (no local Spark)
- ✅ Connects to `localhost` (same server)
- ✅ Uses `server/create_delta_table.py` for Delta tables
- ✅ No JAR downloads needed
- ✅ No internet required

### Step 3: Verify Services Are Running

```bash
# Check all services are up
docker-compose ps

# Should show all services running:
# - lakehouse-minio
# - lakehouse-spark-master
# - lakehouse-spark-worker
# - lakehouse-trino
# - lakehouse-unity-catalog
```

### Step 4: Run the Fixed Script

```bash
python examples/quickstart_on_server.py
```

Expected output:
```
======================================================================
Lakehouse Quickstart - Running ON Server
======================================================================

Step 1: Creating sample data...
✓ Sample data created

Step 2: Initializing client (connecting to localhost services)...
✓ Client initialized

Step 3: Uploading to MinIO...
✓ Uploaded to: s3a://raw-data/products.parquet

Step 4: Creating Delta table via Spark container...
Running: python server/create_delta_table.py s3a://raw-data/products.parquet main default products

Creating Delta table: main.default.products
Source: s3a://raw-data/products.parquet
...
✓ Delta table created successfully

Step 5: Querying data via Trino...
Query 1: All products
  product  sales region
0       A    100  North
1       B    200  South
...

✓ Success! All operations completed.
```

---

## Architecture Diagrams

### ❌ What Was Happening (Wrong)

```
Server (10.16.36.36)
├── Docker Services
│   ├── MinIO (port 9000)
│   ├── Spark Master (port 7077)
│   └── Trino (port 8082)
│
└── Python Client (LakehouseClient)
    └── Tries to create LOCAL Spark session
        └── Downloads JARs from Maven ❌ HANGS
```

### ✅ Correct Architecture

```
Server (10.16.36.36)
├── Docker Services
│   ├── MinIO (localhost:9000)
│   ├── Spark Master (localhost:7077)
│   └── Trino (localhost:8082)
│
└── Python Client (SimpleLakehouseClient)
    ├── Connects to localhost:9000 (MinIO) ✅
    ├── Uses server/create_delta_table.py
    │   └── Executes in Spark container ✅
    └── Connects to localhost:8082 (Trino) ✅
```

---

## Quick Reference

### Running ON the Server

```bash
# Initialize client
from lakehouse_client import SimpleLakehouseClient

client = SimpleLakehouseClient(
    minio_endpoint="http://localhost:9000",
    trino_host="localhost",
    trino_port=8082
)
```

### Running FROM Your Laptop

```bash
# Set remote server IP
export LAKEHOUSE_HOST=10.16.36.36

# Initialize client
from lakehouse_client import SimpleLakehouseClient
client = SimpleLakehouseClient()  # Auto-connects to 10.16.36.36
```

---

## Troubleshooting

### Client Hangs at "resolving dependencies"

**Problem:** Using `LakehouseClient` which downloads JARs

**Solution:**
```python
# Change this:
from lakehouse_client import LakehouseClient  # ❌

# To this:
from lakehouse_client import SimpleLakehouseClient  # ✅
```

### Cannot Connect to Services

**Problem:** Using wrong endpoints (10.16.36.36 instead of localhost)

**Solution:**
```python
# When running ON the server, use localhost:
client = SimpleLakehouseClient(
    minio_endpoint="http://localhost:9000",  # Not 10.16.36.36!
    trino_host="localhost"
)
```

### Docker Services Not Running

**Problem:** Services haven't been started

**Solution:**
```bash
docker-compose up -d
docker-compose ps  # Verify all running
```

---

## Summary

| Your Situation | Use This | Why |
|----------------|----------|-----|
| Running ON server | `SimpleLakehouseClient` + localhost | No local Spark needed |
| Running FROM laptop | `SimpleLakehouseClient` + remote IP | No Java needed locally |
| Local development | `SimpleLakehouseClient` OR `LakehouseClient` | Choose based on Java availability |

**For your current setup:** Use `examples/quickstart_on_server.py` 🎯
