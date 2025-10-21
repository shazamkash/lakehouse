# Lakehouse Architecture

This document provides a detailed overview of the Lakehouse platform architecture.

## Overview

The Lakehouse platform combines the best features of data lakes and data warehouses, providing:
- **Scalable storage** via MinIO (S3-compatible)
- **Distributed processing** via Apache Spark
- **ACID transactions** via Delta Lake
- **Unified metadata** via Unity Catalog
- **Fast queries** via Trino

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Python Client                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Storage    │  │  Delta Mgr   │  │ Query Engine │      │
│  │   Manager    │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────┬───────────────┬─────────────────┬────────────────┘
           │               │                 │
           ▼               ▼                 ▼
    ┌───────────┐   ┌─────────────┐   ┌──────────┐
    │   MinIO   │   │    Spark    │   │  Trino   │
    │  (S3 API) │   │   Master    │   │          │
    │           │   │     +       │   │          │
    │ Port 9000 │   │   Worker    │   │ Port 8082│
    └─────┬─────┘   └──────┬──────┘   └─────┬────┘
          │                │                 │
          │         ┌──────▼──────┐          │
          └────────►│    Unity    │◄─────────┘
                    │   Catalog   │
                    │             │
                    │  Port 8081  │
                    └─────────────┘
```

## Components

### 1. MinIO - Object Storage Layer

**Purpose**: S3-compatible object storage for the data lake

**Key Features**:
- S3-compatible API
- Scalable and distributed
- Web console for management
- Bucket-based organization

**Configuration**:
- API Port: 9000
- Console Port: 9001
- Default credentials: minioadmin/minioadmin
- Pre-created buckets: `lakehouse`, `warehouse`, `raw-data`

**Usage**:
```python
client.upload_parquet('data.csv', 'raw-data', 'dataset')
# → s3a://raw-data/dataset.parquet
```

### 2. Apache Spark - Compute Engine

**Purpose**: Distributed data processing and Delta Lake operations

**Architecture**:
- **Spark Master**: Cluster coordinator
- **Spark Worker**: Processing node

**Key Features**:
- Delta Lake integration
- S3A file system support
- Distributed processing
- In-memory computation

**Configuration**:
- Master Port: 7077
- Master UI: 8080
- Worker Memory: 2GB
- Worker Cores: 2

**Delta Lake Settings**:
```
spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension
spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog
```

### 3. Delta Lake - Table Format

**Purpose**: ACID transactions and versioning for data lake tables

**Key Features**:
- ACID transactions
- Time travel (versioning)
- Schema evolution
- Efficient upserts and deletes
- Partition pruning
- Data skipping

**Table Structure**:
```
s3a://warehouse/
  └── {catalog}/
      └── {schema}/
          └── {table}/
              ├── _delta_log/
              │   ├── 00000000000000000000.json
              │   └── ...
              └── part-*.parquet
```

**Operations**:
- Create table from Parquet
- Append new data
- Overwrite data
- Optimize (compact files)
- Vacuum (clean old versions)

### 4. Unity Catalog - Metadata Layer

**Purpose**: Centralized metadata, governance, and access control

**Key Features**:
- Hierarchical namespace (catalog.schema.table)
- Table registration
- Schema management
- Metadata storage

**Hierarchy**:
```
Catalog (e.g., 'main')
  └── Schema (e.g., 'default', 'analytics')
      └── Table (e.g., 'users', 'transactions')
```

**Configuration**:
- Port: 8081
- S3 Endpoint: http://minio:9000

### 5. Trino - Query Engine

**Purpose**: Distributed SQL query engine for data access

**Key Features**:
- Distributed query execution
- Multiple connector support
- ANSI SQL compliance
- Query optimization
- Join optimization

**Catalogs**:
- **delta**: Delta Lake tables via Unity Catalog
- **minio**: Direct S3/MinIO access

**Configuration**:
- Port: 8082
- Coordinator: Single node (can be scaled)
- Memory: 2GB query max

**Query Examples**:
```sql
-- Query Delta table
SELECT * FROM delta.main.default.users;

-- Join tables
SELECT u.name, t.amount
FROM delta.main.default.users u
JOIN delta.main.default.transactions t
  ON u.id = t.user_id;

-- Aggregations
SELECT city, AVG(score)
FROM delta.main.default.users
GROUP BY city;
```

## Data Flow

### Ingestion Flow

```
1. Raw Data File (CSV/JSON/Parquet)
   ↓
2. Python Client - StorageManager
   ↓ (Convert to Parquet)
3. MinIO - Object Storage
   ↓ (s3a://bucket/file.parquet)
4. Spark - Read Parquet
   ↓ (Transform & Write)
5. Delta Lake - ACID Table
   ↓ (s3a://warehouse/catalog/schema/table/)
6. Unity Catalog - Register Table
   ↓ (metadata)
7. Trino - Query Access
   ↓
8. Query Results
```

### Query Flow

```
1. SQL Query
   ↓
2. Trino Coordinator
   ↓ (Parse & Plan)
3. Unity Catalog
   ↓ (Get metadata)
4. Trino Workers
   ↓ (Read from S3)
5. MinIO - Delta Files
   ↓ (Process)
6. Result Set
```

## Network Architecture

All services run in the `lakehouse-network` Docker bridge network:

```
lakehouse-network (Bridge)
├── minio (minio:9000, minio:9001)
├── spark-master (spark-master:7077, spark-master:8080)
├── spark-worker (internal)
├── unity-catalog (unity-catalog:8080)
└── trino (trino:8080)
```

External access:
- MinIO: localhost:9000 (API), localhost:9001 (Console)
- Spark: localhost:8080 (Master UI)
- Unity Catalog: localhost:8081
- Trino: localhost:8082

## Storage Layout

### MinIO Buckets

```
lakehouse/          # General lakehouse storage
warehouse/          # Delta Lake tables
  ├── main/         # Main catalog
  │   ├── default/  # Default schema
  │   └── analytics/# Analytics schema
  └── ...
raw-data/           # Raw ingested data
  ├── dataset1.parquet
  └── dataset2.parquet
```

### Delta Table Layout

```
s3a://warehouse/catalog/schema/table/
├── _delta_log/
│   ├── 00000000000000000000.json  # Transaction log
│   ├── 00000000000000000001.json
│   └── ...
├── part-00000-....parquet         # Data files
├── part-00001-....parquet
└── ...
```

## Performance Optimization

### Delta Lake Optimizations

1. **File Compaction** (OPTIMIZE)
   - Merges small files into larger ones
   - Improves read performance
   - Reduces metadata overhead

2. **Partition Pruning**
   - Skips irrelevant partitions
   - Reduces data scanned
   - Faster query execution

3. **Data Skipping**
   - Uses min/max statistics
   - Skips files without relevant data
   - Automatic with Delta Lake

4. **Z-Ordering**
   - Co-locates related data
   - Improves filter performance
   - Reduces files scanned

### Trino Optimizations

1. **Predicate Pushdown**
   - Filters applied at source
   - Reduces data transfer
   - Faster queries

2. **Partition Awareness**
   - Prunes partitions early
   - Reduces I/O
   - Better performance

3. **Distributed Joins**
   - Parallel join execution
   - Hash-based joins
   - Optimized for large datasets

## Scalability

### Horizontal Scaling

**Spark Workers**:
```yaml
spark-worker-2:
  image: bitnami/spark:3.5.0
  environment:
    - SPARK_MODE=worker
    - SPARK_MASTER_URL=spark://spark-master:7077
```

**Trino Workers**:
```yaml
trino-worker:
  image: trinodb/trino:435
  volumes:
    - ./config/trino/worker.properties:/etc/trino/config.properties
```

### Vertical Scaling

Adjust memory and CPU in docker-compose.yml:
```yaml
environment:
  - SPARK_WORKER_MEMORY=4G
  - SPARK_WORKER_CORES=4
```

## Security Considerations

### Current Setup (Development)
- Default credentials (minioadmin/minioadmin)
- No authentication on Spark/Trino
- Internal network only

### Production Recommendations
1. Enable authentication on all services
2. Use SSL/TLS for communication
3. Implement Unity Catalog access control
4. Use secrets management (e.g., Vault)
5. Network segmentation
6. Audit logging

## Monitoring

### Health Checks

MinIO:
```bash
curl http://localhost:9000/minio/health/live
```

Spark:
```bash
curl http://localhost:8080
```

Trino:
```bash
curl http://localhost:8082/v1/info
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f spark-master
docker-compose logs -f trino
```

### Metrics

- Spark UI: http://localhost:8080 (Job execution, stages)
- Trino UI: http://localhost:8082 (Query history, performance)
- MinIO Console: http://localhost:9001 (Storage usage)

## Backup and Recovery

### Data Backup
```bash
# Backup MinIO data
docker run --rm -v minio-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/minio-backup.tar.gz /data
```

### Metadata Backup
```bash
# Backup Unity Catalog
docker run --rm -v unity-catalog-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/unity-backup.tar.gz /data
```

## Future Enhancements

1. **Multi-node Spark cluster**
2. **Trino worker nodes**
3. **Iceberg table format support**
4. **Apache Hudi support**
5. **Airflow for orchestration**
6. **Superset for visualization**
7. **Ranger for access control**
8. **Prometheus + Grafana monitoring**

## References

- [Delta Lake Documentation](https://docs.delta.io/)
- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [Trino Documentation](https://trino.io/docs/current/)
- [Unity Catalog](https://github.com/unitycatalog/unitycatalog)
- [MinIO Documentation](https://min.io/docs/)
