# Lakehouse as a Service

A complete lakehouse architecture implementation combining MinIO, Apache Spark, Delta Lake, Unity Catalog, and Trino.

## Architecture Overview

This project provides a fully containerized lakehouse platform with the following components:

1. **MinIO** - S3-compatible object storage for the data lake
2. **Apache Spark** - Distributed compute engine for data processing
3. **Delta Lake** - ACID table format layer
4. **Unity Catalog** - Centralized metadata and governance
5. **Trino** - Distributed SQL query engine for data access
6. **Python Client** - Simple API for interacting with the lakehouse

## Features

- Store data files as Parquet in MinIO (S3-compatible storage)
- Convert S3 objects to Delta tables
- Register Delta tables in Unity Catalog
- Query Delta tables using Trino
- Dockerized setup for easy deployment
- Python client library for seamless integration

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.9+
- At least 8GB RAM allocated to Docker

### Start the Lakehouse

```bash
docker-compose up -d
```

### Install the Python Client

```bash
pip install -e ./client
```

### Basic Usage

```python
from lakehouse_client import LakehouseClient

# Initialize client
client = LakehouseClient()

# Upload data as Parquet to MinIO
client.upload_parquet("data.csv", "raw-data", "my-dataset")

# Convert to Delta table and register in Unity Catalog
client.create_delta_table(
    s3_path="s3://raw-data/my-dataset.parquet",
    catalog="main",
    schema="default",
    table="my_table"
)

# Query the data
results = client.query("SELECT * FROM main.default.my_table LIMIT 10")
print(results)
```

## Project Structure

```
lakehouse/
├── docker-compose.yml          # Main orchestration file
├── config/                     # Configuration files for services
│   ├── minio/                 # MinIO configuration
│   ├── spark/                 # Spark configuration
│   ├── unity-catalog/         # Unity Catalog configuration
│   └── trino/                 # Trino configuration
├── client/                     # Python client library
│   ├── lakehouse_client/
│   │   ├── __init__.py
│   │   ├── storage.py         # MinIO/S3 operations
│   │   ├── delta.py           # Delta Lake operations
│   │   └── query.py           # Trino query operations
│   ├── setup.py
│   └── requirements.txt
├── examples/                   # Example scripts
└── README.md
```

## Services

### MinIO (S3 Storage)
- Web Console: http://localhost:9001
- API Endpoint: http://localhost:9000
- Default credentials: minioadmin/minioadmin

### Spark Master UI
- URL: http://localhost:8080

### Trino UI
- URL: http://localhost:8081

### Unity Catalog
- URL: http://localhost:8080

## Development

### Running Tests

```bash
cd client
pytest tests/
```

### Building the Client

```bash
cd client
pip install -e .
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Python Client                         │
│  (upload, create delta tables, query)                    │
└─────────────┬──────────────┬────────────────┬───────────┘
              │              │                │
              ▼              ▼                ▼
         ┌────────┐    ┌──────────┐    ┌──────────┐
         │ MinIO  │    │  Spark   │    │  Trino   │
         │  (S3)  │    │ (Compute)│    │ (Query)  │
         └────┬───┘    └─────┬────┘    └─────┬────┘
              │              │                │
              └──────────────┼────────────────┘
                             │
                      ┌──────▼──────┐
                      │    Unity    │
                      │   Catalog   │
                      └─────────────┘
```

## Troubleshooting

Having issues? Check the [Troubleshooting Guide](TROUBLESHOOTING.md) for solutions to common problems:

- Spark container permission errors
- Connection issues between services
- Port conflicts
- Performance optimization
- And more...

## Additional Documentation

- [Getting Started Guide](GETTING_STARTED.md) - Step-by-step setup instructions
- [Architecture Documentation](ARCHITECTURE.md) - Detailed technical overview
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions

## License

MIT
