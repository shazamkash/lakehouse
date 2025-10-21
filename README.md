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

#### Option 1: SimpleLakehouseClient (No Java Required) - Recommended for Remote Deployment

```python
from lakehouse_client import SimpleLakehouseClient

# Initialize client (no Java needed!)
client = SimpleLakehouseClient()

# Upload data as Parquet to MinIO
s3_uri = client.upload_parquet("data.csv", "raw-data", "my-dataset")

# Create Delta table on server (see server/create_delta_table.py)
# Then query the data
results = client.query_to_dataframe("SELECT * FROM delta.main.default.my_table")
print(results)
```

#### Option 2: Full LakehouseClient (Requires Java 17+)

```python
from lakehouse_client import LakehouseClient

# Initialize client (requires Java 17+ installed locally)
client = LakehouseClient()

# Upload data as Parquet to MinIO
client.upload_parquet("data.csv", "raw-data", "my-dataset")

# Convert to Delta table and register in Unity Catalog
client.create_delta_table(
    s3_path="s3a://raw-data/my-dataset.parquet",
    catalog="main",
    schema="default",
    table="my_table"
)

# Query the data
results = client.query("SELECT * FROM delta.main.default.my_table LIMIT 10")
print(results)
```

**Note**: Full client requires Java 17+. See [JAVA_SETUP.md](JAVA_SETUP.md) for installation instructions.

## Remote Server Deployment

To deploy on a remote server (e.g., 10.16.36.36):

### On the Remote Server

```bash
# Start services
docker-compose up -d
```

### On Your Local Machine

```bash
# Set the remote server IP
export LAKEHOUSE_HOST=10.16.36.36

# Or create a .env file
cp .env.example .env
# Edit .env and set LAKEHOUSE_HOST=10.16.36.36

# Install client
pip install -e ./client

# Use the client (automatically connects to remote server)
python examples/quickstart.py
```

The client will automatically connect to the remote server using the `LAKEHOUSE_HOST` environment variable.

See the [Deployment Guide](DEPLOYMENT.md) for detailed instructions.

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
- [Deployment Guide](DEPLOYMENT.md) - Remote server deployment instructions
- [Java Setup Guide](JAVA_SETUP.md) - Java requirements and alternatives
- [Architecture Documentation](ARCHITECTURE.md) - Detailed technical overview
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions
- [Server Scripts](server/README.md) - Server-side Delta table operations

## License

MIT
