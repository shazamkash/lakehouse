# Troubleshooting Guide

This guide covers common issues you may encounter when running the Lakehouse platform.

## Spark Container Issues

### ❌ Permission Denied Error

**Symptom:**
```
mv: cannot create regular file '/opt/bitnami/spark/conf/spark-defaults.conf/spark-defaults.conf.template': Permission denied
spark-master exited with code 1
```

**Cause:**
The Bitnami Spark image manages its configuration directory internally. Mounting a configuration file directly conflicts with the container's initialization process.

**Solution:**
This has been fixed in the latest version. The configuration is now set via environment variables in `docker-compose.yml` using the pattern:
```yaml
environment:
  - SPARK_DEFAULTS_CONF_spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension
```

**If you still see this error:**
```bash
# Pull the latest changes
git pull origin claude/lakehouse-as-a-service-011CULDtY8bng5zaJbPADrb9

# Remove old containers and volumes
docker-compose down -v

# Start fresh
docker-compose up -d
```

### ❌ Spark Master Not Starting

**Symptom:**
```
spark-master exited with code 1
```

**Check logs:**
```bash
docker-compose logs spark-master
```

**Common causes:**
1. Port 8080 or 7077 already in use
2. Insufficient memory allocated to Docker
3. Configuration errors

**Solutions:**
```bash
# Check port usage
lsof -i :8080
lsof -i :7077

# Increase Docker memory to at least 8GB
# Docker Desktop → Settings → Resources → Memory

# Restart services
docker-compose restart spark-master
```

### ❌ Spark Worker Can't Connect to Master

**Symptom:**
```
Worker cannot connect to master
```

**Solution:**
```bash
# Ensure master is running first
docker-compose ps

# Restart worker
docker-compose restart spark-worker

# Check network connectivity
docker exec lakehouse-spark-worker ping spark-master
```

## MinIO Issues

### ❌ MinIO Not Starting

**Symptom:**
```
minio exited with code 1
```

**Common causes:**
1. Ports 9000 or 9001 in use
2. Volume permission issues
3. Corrupted data volume

**Solutions:**
```bash
# Check port usage
lsof -i :9000
lsof -i :9001

# Remove and recreate volumes
docker-compose down -v
docker-compose up -d minio
```

### ❌ Cannot Access MinIO Console

**Symptom:**
Cannot connect to http://localhost:9001

**Solutions:**
```bash
# Check if MinIO is running
docker-compose ps minio

# Check MinIO logs
docker-compose logs minio

# Verify port mapping
docker port lakehouse-minio

# Try accessing from container
docker exec lakehouse-minio curl http://localhost:9001
```

### ❌ S3 Access Denied Errors

**Symptom:**
```
Access Denied (403)
```

**Solutions:**
```bash
# Verify credentials in docker-compose.yml
# Default: minioadmin/minioadmin

# Recreate buckets
docker-compose up minio-setup

# Check bucket policies
docker exec lakehouse-minio mc policy get myminio/warehouse
```

## Trino Issues

### ❌ Trino Not Starting

**Symptom:**
```
trino exited with code 1
```

**Check logs:**
```bash
docker-compose logs trino
```

**Common causes:**
1. Port 8082 in use
2. Insufficient memory
3. Invalid catalog configuration

**Solutions:**
```bash
# Verify config files exist
ls -la config/trino/catalog/
ls -la config/trino/config.properties

# Restart Trino
docker-compose restart trino

# Check memory settings in docker-compose.yml
```

### ❌ Cannot Query Delta Tables

**Symptom:**
```
Table not found: delta.main.default.table_name
```

**Solutions:**
```bash
# Check if table exists in Unity Catalog
# Use Python client to verify

# Verify Trino can access MinIO
docker exec lakehouse-trino curl http://minio:9000

# Check catalog configuration
docker exec lakehouse-trino cat /etc/trino/catalog/delta.properties
```

### ❌ Query Timeout

**Symptom:**
```
Query exceeded maximum time limit
```

**Solutions:**
1. Increase query timeout in `config/trino/config.properties`
2. Optimize your query (add filters, partitions)
3. Increase Trino memory allocation

## Unity Catalog Issues

### ❌ Unity Catalog Not Starting

**Symptom:**
```
unity-catalog exited with code 1
```

**Check logs:**
```bash
docker-compose logs unity-catalog
```

**Solutions:**
```bash
# Ensure MinIO is running first
docker-compose ps minio

# Restart Unity Catalog
docker-compose restart unity-catalog

# Check S3 connectivity
docker exec lakehouse-unity-catalog curl http://minio:9000
```

### ❌ Cannot Register Tables

**Symptom:**
```
Failed to register table in Unity Catalog
```

**Solutions:**
1. Verify catalog and schema exist
2. Check S3 path is accessible
3. Ensure Delta table was created successfully

```python
# Use Python client to debug
from lakehouse_client import LakehouseClient

client = LakehouseClient()
catalogs = client.list_catalogs()
print(catalogs)
```

## Python Client Issues

### ❌ Connection Refused Errors

**Symptom:**
```
ConnectionRefusedError: [Errno 111] Connection refused
```

**Cause:**
Services not running or using wrong host/port

**Solutions:**
```bash
# Check all services are running
docker-compose ps

# Verify service health
docker-compose logs --tail=50

# Ensure you're using correct endpoints
# - MinIO: localhost:9000
# - Spark: localhost:7077
# - Trino: localhost:8082
# - Unity Catalog: localhost:8081
```

### ❌ Import Errors

**Symptom:**
```
ModuleNotFoundError: No module named 'lakehouse_client'
```

**Solutions:**
```bash
# Install the client
cd client
pip install -e .

# Or from root
pip install -e ./client

# Verify installation
pip list | grep lakehouse
```

### ❌ PySpark Import Errors

**Symptom:**
```
ImportError: No module named 'pyspark'
```

**Solutions:**
```bash
# Install dependencies
pip install -r client/requirements.txt

# Or install specific package
pip install pyspark>=3.5.0 delta-spark>=3.0.0
```

### ❌ Delta Lake Dependencies Not Found

**Symptom:**
```
java.lang.ClassNotFoundException: io.delta.sql.DeltaSparkSessionExtension
```

**Cause:**
Delta Lake JARs not available to Spark

**Note:**
This should be handled automatically by the `delta-spark` Python package. If you still see this error:

```python
# Use configure_spark_with_delta_pip from client code
from delta import configure_spark_with_delta_pip

builder = SparkSession.builder...
spark = configure_spark_with_delta_pip(builder).getOrCreate()
```

## Docker Issues

### ❌ Docker Daemon Not Running

**Symptom:**
```
Cannot connect to the Docker daemon
```

**Solutions:**
```bash
# Start Docker
# macOS: Open Docker Desktop
# Linux: sudo systemctl start docker
# Windows: Start Docker Desktop

# Verify Docker is running
docker ps
```

### ❌ Insufficient Memory

**Symptom:**
Services keep restarting or crashing

**Solutions:**
```bash
# Increase Docker memory allocation
# Docker Desktop → Settings → Resources
# Recommended: At least 8GB

# Check current resource usage
docker stats
```

### ❌ Port Conflicts

**Symptom:**
```
Bind for 0.0.0.0:8080 failed: port is already allocated
```

**Solutions:**
```bash
# Find what's using the port
lsof -i :8080

# Option 1: Kill the process
kill <PID>

# Option 2: Change port in docker-compose.yml
ports:
  - "8081:8080"  # Changed from 8080:8080
```

### ❌ Volume Permission Issues

**Symptom:**
```
Permission denied
```

**Solutions:**
```bash
# Remove all volumes and recreate
docker-compose down -v
docker-compose up -d

# Check volume permissions
docker volume inspect lakehouse_minio-data
```

## Network Issues

### ❌ Services Can't Communicate

**Symptom:**
```
Connection refused between services
```

**Solutions:**
```bash
# Check network exists
docker network ls | grep lakehouse

# Verify all services are on same network
docker network inspect lakehouse_lakehouse-network

# Restart network
docker-compose down
docker-compose up -d
```

### ❌ DNS Resolution Failed

**Symptom:**
```
Could not resolve hostname 'minio'
```

**Solutions:**
```bash
# Ensure services use Docker network names, not localhost
# Inside containers: use 'minio', 'spark-master', etc.
# From host: use 'localhost'

# Restart Docker daemon
# macOS/Windows: Restart Docker Desktop
# Linux: sudo systemctl restart docker
```

## Data Issues

### ❌ Table Not Found

**Symptom:**
```
Table 'catalog.schema.table' not found
```

**Solutions:**
```python
# List all available tables
from lakehouse_client import LakehouseClient

client = LakehouseClient()

# Check catalogs
print(client.list_catalogs())

# Check schemas
print(client.list_schemas('delta'))

# Check tables
print(client.list_tables('delta', 'main.default'))
```

### ❌ Empty Query Results

**Symptom:**
Query returns 0 rows when data should exist

**Solutions:**
```python
# Verify data was written
stats = client.get_table_stats('table_name', 'delta', 'main.default')
print(f"Row count: {stats['row_count']}")

# Check Delta table location
from lakehouse_client import LakehouseClient
client = LakehouseClient()

# Verify S3 files exist
objects = client.list_objects('warehouse', 'main/default/table_name')
print(objects)
```

### ❌ Schema Mismatch

**Symptom:**
```
Schema mismatch error
```

**Solutions:**
```python
# Enable schema auto-merge (already configured in Spark)
# Or explicitly evolve schema when appending data

client.create_delta_table(
    s3_path=s3_uri,
    catalog='main',
    schema='default',
    table='my_table',
    mode='append',  # or 'overwrite'
)
```

## Performance Issues

### ❌ Slow Queries

**Solutions:**
1. Add filters to reduce data scanned
2. Use partitioned tables
3. Optimize tables regularly

```python
# Optimize table
client.optimize_table('main', 'default', 'my_table')

# Use partitioning
client.create_delta_table(
    s3_path=s3_uri,
    catalog='main',
    schema='default',
    table='my_table',
    partition_by=['year', 'month']
)
```

### ❌ Out of Memory Errors

**Symptom:**
```
java.lang.OutOfMemoryError
```

**Solutions:**
```yaml
# Increase Spark memory in docker-compose.yml
environment:
  - SPARK_WORKER_MEMORY=4G  # Increase from 2G
  - SPARK_DRIVER_MEMORY=2G
```

## Getting Help

### Collect Debug Information

```bash
# Service status
docker-compose ps

# Recent logs from all services
docker-compose logs --tail=100

# Specific service logs
docker-compose logs --tail=100 spark-master
docker-compose logs --tail=100 trino
docker-compose logs --tail=100 minio
docker-compose logs --tail=100 unity-catalog

# Resource usage
docker stats

# Network info
docker network inspect lakehouse_lakehouse-network

# Volume info
docker volume ls
```

### Complete Reset

If all else fails, start fresh:

```bash
# Stop all services
docker-compose down

# Remove all volumes (⚠️  destroys all data)
docker-compose down -v

# Remove images (optional)
docker-compose down --rmi all

# Start fresh
docker-compose up -d

# Wait for services to be healthy
docker-compose ps
```

### Report Issues

When reporting issues, include:
1. Output of `docker-compose ps`
2. Relevant logs from `docker-compose logs`
3. Your docker-compose.yml (if modified)
4. Steps to reproduce the issue
5. Expected vs actual behavior

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [MinIO Documentation](https://min.io/docs/)
- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [Delta Lake Documentation](https://docs.delta.io/)
- [Trino Documentation](https://trino.io/docs/current/)
