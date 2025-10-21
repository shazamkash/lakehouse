# Remote Server Deployment Guide

This guide explains how to deploy and use the Lakehouse platform on a remote server.

## Architecture

The Lakehouse platform uses two types of communication:

1. **Internal Communication** (Service-to-Service)
   - Uses Docker network names (e.g., `minio`, `spark-master`, `trino`)
   - Services communicate within the Docker bridge network
   - Already configured in `docker-compose.yml`

2. **External Communication** (Client-to-Service)
   - Uses the remote server's IP address (e.g., `10.16.36.36`)
   - Python client connects from outside the Docker network
   - Configured via environment variables

## Server Setup

### 1. Deploy on Remote Server (IP: 10.16.36.36)

SSH into your remote server:

```bash
ssh user@10.16.36.36
```

Clone the repository:

```bash
git clone <repository-url>
cd lakehouse
```

### 2. Start Services

Start all Lakehouse services:

```bash
docker-compose up -d
```

Verify all services are running:

```bash
docker-compose ps
```

You should see:
- `lakehouse-minio` - running
- `lakehouse-spark-master` - running
- `lakehouse-spark-worker` - running
- `lakehouse-unity-catalog` - running
- `lakehouse-trino` - running

### 3. Verify External Access

Check that services are accessible from outside the server:

```bash
# From your local machine (not the server)
curl http://10.16.36.36:9000/minio/health/live
curl http://10.16.36.36:8080  # Spark UI
curl http://10.16.36.36:8082/v1/info  # Trino
```

### 4. Configure Firewall (if needed)

Ensure the following ports are open:

```bash
# On the remote server
sudo firewall-cmd --permanent --add-port=9000/tcp  # MinIO API
sudo firewall-cmd --permanent --add-port=9001/tcp  # MinIO Console
sudo firewall-cmd --permanent --add-port=7077/tcp  # Spark Master
sudo firewall-cmd --permanent --add-port=8080/tcp  # Spark UI
sudo firewall-cmd --permanent --add-port=8081/tcp  # Unity Catalog
sudo firewall-cmd --permanent --add-port=8082/tcp  # Trino
sudo firewall-cmd --reload
```

## Client Configuration

### Method 1: Using Environment Variables (Recommended)

On your local machine where you'll run the Python client:

```bash
# Set the remote server IP
export LAKEHOUSE_HOST=10.16.36.36

# Optionally set other configuration
export LAKEHOUSE_MINIO_ACCESS_KEY=minioadmin
export LAKEHOUSE_MINIO_SECRET_KEY=minioadmin
```

Then use the client:

```python
from lakehouse_client import LakehouseClient

# Will automatically connect to 10.16.36.36
client = LakehouseClient()
```

### Method 2: Using .env File (Recommended)

Create a `.env` file on your local machine:

```bash
cd lakehouse
cp .env.example .env
```

Edit `.env`:

```bash
LAKEHOUSE_HOST=10.16.36.36
LAKEHOUSE_MINIO_ACCESS_KEY=minioadmin
LAKEHOUSE_MINIO_SECRET_KEY=minioadmin
```

Use with python-dotenv:

```python
from dotenv import load_dotenv
from lakehouse_client import LakehouseClient

# Load environment variables
load_dotenv()

# Will automatically connect to 10.16.36.36
client = LakehouseClient()
```

Install python-dotenv:

```bash
pip install python-dotenv
```

### Method 3: Explicit Configuration

Pass the remote server IP explicitly:

```python
from lakehouse_client import LakehouseClient

client = LakehouseClient(
    minio_endpoint="http://10.16.36.36:9000",
    minio_access_key="minioadmin",
    minio_secret_key="minioadmin",
    spark_master="spark://10.16.36.36:7077",
    trino_host="10.16.36.36",
    trino_port=8082,
    unity_catalog_url="http://10.16.36.36:8081",
)
```

## Network Configuration Details

### Port Mappings

All services are bound to `0.0.0.0` to accept connections from any interface:

| Service        | Internal Port | External Port | Purpose           |
|----------------|---------------|---------------|-------------------|
| MinIO API      | 9000          | 9000          | S3 operations     |
| MinIO Console  | 9001          | 9001          | Web UI            |
| Spark Master   | 8080          | 8080          | Web UI            |
| Spark Master   | 7077          | 7077          | Client connection |
| Unity Catalog  | 8080          | 8081          | API               |
| Trino          | 8080          | 8082          | Query engine      |

### Internal Service Communication

Services use Docker network names for internal communication:

- Spark → MinIO: `http://minio:9000`
- Spark → Unity Catalog: Uses internal network
- Trino → MinIO: `http://minio:9000`
- Trino → Unity Catalog: `unity-catalog:8080`

**This is already configured and requires no changes.**

### External Client Communication

Python client uses the remote server IP:

- Client → MinIO: `http://10.16.36.36:9000`
- Client → Spark: `spark://10.16.36.36:7077`
- Client → Trino: `10.16.36.36:8082`
- Client → Unity Catalog: `http://10.16.36.36:8081`

## Important: MinIO Endpoint Configuration

The Lakehouse client handles two different MinIO endpoints automatically:

1. **External Endpoint** (for Python client)
   - Used by `StorageManager` to upload/download files
   - Set via `LAKEHOUSE_HOST` or `LAKEHOUSE_MINIO_ENDPOINT`
   - Example: `http://10.16.36.36:9000`

2. **Internal Endpoint** (for Spark)
   - Used by `DeltaManager` for Spark operations
   - Always uses Docker network name: `http://minio:9000`
   - Set via `LAKEHOUSE_MINIO_INTERNAL_ENDPOINT` (rarely needed)

This separation ensures:
- Python client can access MinIO from outside Docker network
- Spark (running inside Docker) can access MinIO via internal network

## Complete Workflow Example

On your local machine:

```bash
# 1. Set environment variable
export LAKEHOUSE_HOST=10.16.36.36

# 2. Install client
pip install -e ./client

# 3. Run example
cd examples
python quickstart.py
```

The script will:
1. Upload data to MinIO at `10.16.36.36:9000`
2. Submit Spark job to `10.16.36.36:7077`
3. Spark reads/writes to MinIO using `minio:9000` (internal)
4. Query data from Trino at `10.16.36.36:8082`

## Web UIs

Access the web interfaces from your browser:

- **MinIO Console**: http://10.16.36.36:9001
  - Username: `minioadmin`
  - Password: `minioadmin`

- **Spark Master UI**: http://10.16.36.36:8080
  - View running jobs and cluster status

- **Trino UI**: http://10.16.36.36:8082
  - View query history and performance

## Security Considerations

### Production Deployment

For production use, you should:

1. **Change default credentials**:
   ```yaml
   # docker-compose.yml
   environment:
     MINIO_ROOT_USER: your_secure_user
     MINIO_ROOT_PASSWORD: your_secure_password
   ```

2. **Enable SSL/TLS**:
   - Configure MinIO with certificates
   - Enable HTTPS for all services
   - Update client endpoints to use `https://`

3. **Network security**:
   - Use firewall rules to restrict access
   - Consider using VPN or SSH tunneling
   - Implement authentication on all services

4. **Use secrets management**:
   - Don't commit `.env` files
   - Use environment-specific configurations
   - Consider using HashiCorp Vault or similar

### Development vs Production

**Development** (current setup):
- Default credentials
- No authentication
- HTTP (no SSL)
- All ports exposed

**Production** (recommended):
- Strong credentials
- Authentication enabled
- HTTPS with valid certificates
- Firewall restrictions
- Network segmentation

## Troubleshooting Remote Deployment

### Can't Connect to Services

```bash
# Check if services are running
ssh user@10.16.36.36 "docker-compose ps"

# Check if ports are accessible
telnet 10.16.36.36 9000
telnet 10.16.36.36 8082

# Check firewall
ssh user@10.16.36.36 "sudo firewall-cmd --list-ports"
```

### Connection Refused

1. Verify services are bound to `0.0.0.0`:
   ```bash
   ssh user@10.16.36.36 "docker-compose logs minio | grep -i listen"
   ```

2. Check Docker network:
   ```bash
   ssh user@10.16.36.36 "docker network inspect lakehouse_lakehouse-network"
   ```

3. Test from server itself:
   ```bash
   ssh user@10.16.36.36 "curl http://localhost:9000/minio/health/live"
   ```

### Client Can't Upload to MinIO

Verify the client is using the correct external endpoint:

```python
from lakehouse_client import LakehouseClient
import os

print(f"LAKEHOUSE_HOST: {os.getenv('LAKEHOUSE_HOST', 'not set')}")

client = LakehouseClient()
print(f"MinIO endpoint: {client.storage.endpoint}")
# Should show: http://10.16.36.36:9000
```

### Spark Can't Access MinIO

Check Spark is using internal endpoint:

```python
client = LakehouseClient()
print(f"Spark MinIO endpoint: {client.delta.minio_endpoint}")
# Should show: http://minio:9000
```

## Monitoring

### Check Service Health

```bash
# On remote server
docker-compose ps
docker-compose logs --tail=50 spark-master
docker-compose logs --tail=50 trino
```

### Monitor Resource Usage

```bash
# On remote server
docker stats
```

### View Logs

```bash
# Follow all logs
docker-compose logs -f

# Specific service
docker-compose logs -f minio
docker-compose logs -f spark-master
```

## Backup and Data Persistence

### Data Locations

Persistent data is stored in Docker volumes:

- `minio-data`: All object storage data
- `spark-warehouse`: Spark warehouse (metadata)
- `unity-catalog-data`: Unity Catalog metadata

### Backup

```bash
# On remote server
# Backup MinIO data
docker run --rm -v lakehouse_minio-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/minio-backup-$(date +%Y%m%d).tar.gz /data

# Backup Unity Catalog
docker run --rm -v lakehouse_unity-catalog-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/unity-backup-$(date +%Y%m%d).tar.gz /data
```

### Restore

```bash
# Stop services
docker-compose down

# Restore volume
docker run --rm -v lakehouse_minio-data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/minio-backup-20241021.tar.gz -C /

# Start services
docker-compose up -d
```

## Scaling

### Add More Spark Workers

Edit `docker-compose.yml`:

```yaml
spark-worker-2:
  image: bitnami/spark:3.5.0
  container_name: lakehouse-spark-worker-2
  environment:
    - SPARK_MODE=worker
    - SPARK_MASTER_URL=spark://spark-master:7077
    - SPARK_WORKER_MEMORY=2G
    - SPARK_WORKER_CORES=2
    # ... same config as spark-worker
```

### Increase Resources

```yaml
spark-worker:
  # ...
  environment:
    - SPARK_WORKER_MEMORY=4G  # Increase from 2G
    - SPARK_WORKER_CORES=4    # Increase from 2
```

## Additional Resources

- [Getting Started Guide](GETTING_STARTED.md)
- [Architecture Documentation](ARCHITECTURE.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Python Client README](client/README.md)
