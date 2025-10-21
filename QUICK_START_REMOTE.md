# Quick Start: Remote Server Deployment (10.16.36.36)

This guide shows you how to quickly deploy and use the Lakehouse on your remote server.

## 🚀 On the Remote Server (10.16.36.36)

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd lakehouse

# 2. Pull the latest changes with remote deployment support
git checkout claude/lakehouse-as-a-service-011CULDtY8bng5zaJbPADrb9

# 3. Start all services
docker-compose up -d

# 4. Verify services are running
docker-compose ps

# 5. Check logs if needed
docker-compose logs --tail=50
```

## 💻 On Your Local Machine

### Option 1: Using Environment Variable (Simplest)

```bash
# 1. Set the remote server IP
export LAKEHOUSE_HOST=10.16.36.36

# 2. Install the Python client
cd lakehouse
pip install -e ./client

# 3. Run an example
cd examples
python quickstart.py
```

### Option 2: Using .env File (Recommended)

```bash
# 1. Create .env file from template
cp .env.example .env

# 2. Edit .env and set:
#    LAKEHOUSE_HOST=10.16.36.36

# 3. Install python-dotenv
pip install python-dotenv

# 4. Install the client
pip install -e ./client

# 5. Use in your Python code:
```

```python
from dotenv import load_dotenv
from lakehouse_client import LakehouseClient

load_dotenv()  # Load from .env file
client = LakehouseClient()  # Automatically uses 10.16.36.36
```

### Option 3: Explicit Configuration

```python
from lakehouse_client import LakehouseClient

client = LakehouseClient(
    minio_endpoint="http://10.16.36.36:9000",
    spark_master="spark://10.16.36.36:7077",
    trino_host="10.16.36.36",
    unity_catalog_url="http://10.16.36.36:8081",
)
```

## 🌐 Web Access

Access these UIs from your browser:

- **MinIO Console**: http://10.16.36.36:9001
  - User: `minioadmin` / Pass: `minioadmin`

- **Spark UI**: http://10.16.36.36:8080

- **Trino UI**: http://10.16.36.36:8082

## 📝 Complete Example

```python
# Set environment (or use .env file)
import os
os.environ['LAKEHOUSE_HOST'] = '10.16.36.36'

from lakehouse_client import LakehouseClient
import pandas as pd

# Initialize client
client = LakehouseClient()

# Create sample data
data = pd.DataFrame({
    'id': [1, 2, 3, 4, 5],
    'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
    'score': [95, 87, 92, 88, 91]
})
data.to_csv('test_data.csv', index=False)

# Upload to MinIO on remote server
s3_uri = client.upload_parquet('test_data.csv', 'raw-data', 'test')
print(f"Uploaded to: {s3_uri}")

# Create Delta table on remote server
client.create_delta_table(
    s3_path=s3_uri,
    catalog='main',
    schema='default',
    table='test_table'
)
print("Delta table created!")

# Query from remote server
results = client.query_to_dataframe(
    "SELECT * FROM delta.main.default.test_table"
)
print(results)
```

## 🔧 How It Works

### Internal Communication (Service-to-Service)
Services inside Docker use internal names:
- `http://minio:9000`
- `spark://spark-master:7077`
- `unity-catalog:8080`

### External Communication (Client-to-Service)
Your Python client uses the remote IP:
- `http://10.16.36.36:9000` (MinIO)
- `spark://10.16.36.36:7077` (Spark)
- `10.16.36.36:8082` (Trino)
- `http://10.16.36.36:8081` (Unity Catalog)

**The Python client handles this automatically when you set `LAKEHOUSE_HOST`!**

## 🔍 Troubleshooting

### Can't Connect to Services

```bash
# Check if services are running on remote server
ssh user@10.16.36.36 "docker-compose ps"

# Test connectivity from your machine
curl http://10.16.36.36:9000/minio/health/live
```

### Verify Configuration

```python
from lakehouse_client import LakehouseClient
import os

print(f"LAKEHOUSE_HOST: {os.getenv('LAKEHOUSE_HOST')}")

client = LakehouseClient()
print(f"MinIO endpoint: {client.storage.endpoint}")
print(f"Spark MinIO endpoint: {client.delta.minio_endpoint}")
```

Expected output:
```
LAKEHOUSE_HOST: 10.16.36.36
MinIO endpoint: http://10.16.36.36:9000
Spark MinIO endpoint: http://minio:9000
```

### Firewall Issues

On the remote server, ensure ports are open:

```bash
sudo firewall-cmd --permanent --add-port=9000-9001/tcp
sudo firewall-cmd --permanent --add-port=7077/tcp
sudo firewall-cmd --permanent --add-port=8080-8082/tcp
sudo firewall-cmd --reload
```

## 📚 Full Documentation

- [DEPLOYMENT.md](DEPLOYMENT.md) - Comprehensive deployment guide
- [README.md](README.md) - Project overview
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical details

## ✅ Summary

1. **Server**: Run `docker-compose up -d` on 10.16.36.36
2. **Client**: Set `LAKEHOUSE_HOST=10.16.36.36`
3. **Code**: Use `LakehouseClient()` as normal
4. **Done**: Everything automatically uses the remote server!

The platform intelligently separates:
- **External access**: Your client → Remote server IP
- **Internal access**: Docker services → Docker network names

No manual configuration of individual services needed!
