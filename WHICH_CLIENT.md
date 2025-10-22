# Which Client Should I Use?

The Lakehouse platform provides **two Python clients** for different use cases. Here's how to choose:

## Quick Decision Tree

```
Do you have a remote Spark cluster (e.g., 10.16.36.36)?
│
├─ YES → Use SimpleLakehouseClient
│         ✓ No local Java needed
│         ✓ No local Spark needed
│         ✓ Perfect for remote deployments
│
└─ NO → Do you have Java 17+ installed locally?
         │
         ├─ YES → Use LakehouseClient
         │         ✓ Full features
         │         ✓ Create Delta tables from local machine
         │
         └─ NO → Use SimpleLakehouseClient
                   ✓ Simpler setup
                   ✓ Use server-side scripts for Delta operations
```

## Option 1: SimpleLakehouseClient (Recommended for Remote Servers)

### When to Use
- ✅ Connecting to a remote Spark cluster (e.g., 10.16.36.36)
- ✅ Don't want to install Java locally
- ✅ Want lightweight client dependencies
- ✅ Production deployments
- ✅ CI/CD pipelines

### What It Does
- Upload/download data to MinIO ✓
- Query tables via Trino ✓
- List tables, catalogs, schemas ✓
- Create Delta tables via server-side script ⚠️ (SSH required)

### What It DOESN'T Do
- ❌ Create Delta tables directly (use server script instead)
- ❌ Run Spark jobs from local machine
- ❌ Require Java/Spark locally

### Example Usage

```python
from lakehouse_client import SimpleLakehouseClient
import os

# Set remote server
os.environ['LAKEHOUSE_HOST'] = '10.16.36.36'

# Initialize (no Spark session created)
client = SimpleLakehouseClient()

# Upload data
s3_uri = client.upload_parquet('data.csv', 'raw-data', 'dataset')

# Create Delta table on server (via SSH)
# ssh user@10.16.36.36
# python server/create_delta_table.py s3a://raw-data/dataset.parquet main default my_table

# Query data
results = client.query_to_dataframe("SELECT * FROM delta.main.default.my_table")
print(results)
```

### Dependencies
```
boto3       # MinIO/S3
pandas      # DataFrames
pyarrow     # Parquet
trino       # Queries
```

**NO PySpark or Java required!**

---

## Option 2: LakehouseClient (Full Features, Requires Java)

### When to Use
- ✅ Local development
- ✅ Have Java 17+ installed
- ✅ Want to create Delta tables from your machine
- ✅ Need full PySpark functionality
- ✅ Rapid prototyping

### What It Does
- Upload/download data to MinIO ✓
- Query tables via Trino ✓
- Create Delta tables directly ✓
- Run Spark jobs from local machine ✓
- Full PySpark integration ✓

### What It Requires
- ✅ Java 17+ installed locally
- ✅ PySpark installed
- ✅ Delta-Spark installed
- ✅ Local Spark can connect to remote cluster

### Example Usage

```python
from lakehouse_client import LakehouseClient

# Initialize (creates local Spark session)
client = LakehouseClient()

# Upload data
s3_uri = client.upload_parquet('data.csv', 'raw-data', 'dataset')

# Create Delta table (runs locally, connects to remote Spark)
client.create_delta_table(
    s3_path=s3_uri,
    catalog='main',
    schema='default',
    table='my_table'
)

# Query data
results = client.query_to_dataframe("SELECT * FROM delta.main.default.my_table")
print(results)
```

### Dependencies
```
boto3       # MinIO/S3
pandas      # DataFrames
pyarrow     # Parquet
pyspark     # Spark
delta-spark # Delta Lake
trino       # Queries
```

**Requires Java 17+ and PySpark!**

---

## Comparison Table

| Feature | SimpleLakehouseClient | LakehouseClient |
|---------|----------------------|-----------------|
| Upload to MinIO | ✅ Yes | ✅ Yes |
| Query via Trino | ✅ Yes | ✅ Yes |
| Create Delta tables locally | ❌ No (use server script) | ✅ Yes |
| Requires Java locally | ❌ No | ✅ Yes (17+) |
| Requires PySpark locally | ❌ No | ✅ Yes |
| Package downloads | ❌ None | ⚠️ Downloads Delta JARs |
| Setup complexity | ✅ Simple | ⚠️ Complex |
| Works offline | ✅ Yes | ⚠️ Needs internet for JARs |
| Production ready | ✅ Yes | ✅ Yes (if Java available) |
| CI/CD friendly | ✅ Yes | ⚠️ Needs Java in container |

---

## Common Issues and Solutions

### Issue: "java.lang.UnsupportedClassVersionError"

**Symptom:**
```
java.lang.UnsupportedClassVersionError: class file version 61.0
this version only recognizes up to 55.0
```

**Solution:**
You're using `LakehouseClient` but don't have Java 17.

**Fix:**
```python
# Switch to SimpleLakehouseClient
from lakehouse_client import SimpleLakehouseClient  # Changed!
client = SimpleLakehouseClient()
```

Or install Java 17: See [JAVA_SETUP.md](JAVA_SETUP.md)

---

### Issue: "Code hangs at Ivy resolving dependencies"

**Symptom:**
```
:: resolving dependencies :: org.apache.spark#spark-submit-parent-...
confs: [default]
(hangs here)
```

**Solution:**
`LakehouseClient` is trying to download Delta Lake JARs from Maven.

**Fix:**
```python
# Use SimpleLakehouseClient instead
from lakehouse_client import SimpleLakehouseClient
client = SimpleLakehouseClient()
```

Or ensure you have internet access and Maven repositories are reachable.

---

### Issue: "Cannot create Delta table"

**With SimpleLakehouseClient:**

The SimpleLakehouseClient doesn't create Delta tables directly. Use the server-side script:

```bash
# On remote server (10.16.36.36)
python server/create_delta_table.py \
    s3a://raw-data/dataset.parquet \
    main \
    default \
    my_table
```

**With LakehouseClient:**

Ensure Java 17+ is installed:
```bash
java -version  # Should show 17 or higher
```

---

## Workflow Comparison

### SimpleLakehouseClient Workflow

```
Local Machine                  Remote Server (10.16.36.36)
─────────────                  ────────────────────────────

1. Upload data to MinIO
   client.upload_parquet()
                               2. Create Delta table
                                  python server/create_delta_table.py

3. Query via Trino
   client.query_to_dataframe()
```

### LakehouseClient Workflow

```
Local Machine                  Remote Server (10.16.36.36)
─────────────                  ────────────────────────────

1. Upload data to MinIO
   client.upload_parquet()

2. Create Delta table          → Submits job to remote Spark
   client.create_delta_table()   (requires Java 17+ locally)

3. Query via Trino
   client.query_to_dataframe()
```

---

## Recommendations

### For Your Setup (Remote Server at 10.16.36.36)

**Use SimpleLakehouseClient:**

```python
from lakehouse_client import SimpleLakehouseClient
import os

# Set remote server
os.environ['LAKEHOUSE_HOST'] = '10.16.36.36'

client = SimpleLakehouseClient()
```

**Why?**
- ✅ No Java installation needed on your laptop
- ✅ Works from Windows, Mac, Linux
- ✅ Simpler dependencies
- ✅ No package downloads
- ✅ Perfect for remote deployments

**For Delta tables:**
- SSH to server and run `server/create_delta_table.py`
- Or create an API endpoint for Delta table creation

---

### For Local Development

**Use LakehouseClient:**

```python
from lakehouse_client import LakehouseClient

client = LakehouseClient()
```

**Prerequisites:**
1. Install Java 17: See [JAVA_SETUP.md](JAVA_SETUP.md)
2. Verify: `java -version`
3. Install client: `pip install -e ./client`

**Why?**
- ✅ Full features
- ✅ Create Delta tables directly
- ✅ Rapid development
- ✅ Complete local control

---

## Migration

### Switching from LakehouseClient to SimpleLakehouseClient

**Before:**
```python
from lakehouse_client import LakehouseClient

client = LakehouseClient()
s3_uri = client.upload_parquet('data.csv', 'raw-data', 'dataset')

# This requires local Spark/Java
client.create_delta_table(
    s3_path=s3_uri,
    catalog='main',
    schema='default',
    table='my_table'
)
```

**After:**
```python
from lakehouse_client import SimpleLakehouseClient

client = SimpleLakehouseClient()
s3_uri = client.upload_parquet('data.csv', 'raw-data', 'dataset')

# Use server-side script instead
print(f"Run on server: python server/create_delta_table.py {s3_uri} main default my_table")
```

---

## Quick Reference

### Import Statement

```python
# For remote server (no Java needed)
from lakehouse_client import SimpleLakehouseClient

# For local development (requires Java 17+)
from lakehouse_client import LakehouseClient
```

### Configuration

Both clients support environment variables:

```bash
export LAKEHOUSE_HOST=10.16.36.36
export LAKEHOUSE_MINIO_ACCESS_KEY=minioadmin
export LAKEHOUSE_MINIO_SECRET_KEY=minioadmin
```

Or use `.env` file:
```bash
cp .env.example .env
# Edit .env
```

---

## Summary

| Scenario | Use | Why |
|----------|-----|-----|
| Remote server deployment | `SimpleLakehouseClient` | No Java needed |
| No Java installed | `SimpleLakehouseClient` | Simpler setup |
| Production | `SimpleLakehouseClient` | Lightweight |
| Local development with Java 17+ | `LakehouseClient` | Full features |
| Need to create Delta tables locally | `LakehouseClient` | Direct creation |

**For your current setup (10.16.36.36):** Use `SimpleLakehouseClient`! 🎯
