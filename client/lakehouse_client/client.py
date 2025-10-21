"""
Main Lakehouse Client integrating all components.
"""

from typing import Optional, List, Dict, Any, Union
import os
import pandas as pd

from .storage import StorageManager
from .delta import DeltaManager
from .query import QueryEngine


class LakehouseClient:
    """
    Main client for interacting with the Lakehouse platform.

    Provides a unified interface for:
    - Uploading data to MinIO as Parquet
    - Creating Delta tables
    - Registering tables in Unity Catalog
    - Querying data via Trino
    """

    def __init__(
        self,
        minio_endpoint: Optional[str] = None,
        minio_access_key: Optional[str] = None,
        minio_secret_key: Optional[str] = None,
        spark_master: Optional[str] = None,
        trino_host: Optional[str] = None,
        trino_port: Optional[int] = None,
        trino_user: Optional[str] = None,
        unity_catalog_url: Optional[str] = None,
    ):
        """
        Initialize the Lakehouse Client.

        Configuration priority:
        1. Explicitly passed parameters
        2. Environment variables (LAKEHOUSE_*)
        3. Default values

        Environment Variables:
            LAKEHOUSE_HOST: Remote server IP/hostname (e.g., 10.16.36.36)
            LAKEHOUSE_MINIO_ENDPOINT: MinIO endpoint URL
            LAKEHOUSE_MINIO_ACCESS_KEY: MinIO access key
            LAKEHOUSE_MINIO_SECRET_KEY: MinIO secret key
            LAKEHOUSE_SPARK_MASTER: Spark master URL
            LAKEHOUSE_TRINO_HOST: Trino server host
            LAKEHOUSE_TRINO_PORT: Trino server port
            LAKEHOUSE_TRINO_USER: Trino username
            LAKEHOUSE_UNITY_CATALOG_URL: Unity Catalog URL

        Args:
            minio_endpoint: MinIO endpoint URL (default: http://localhost:9000)
            minio_access_key: MinIO access key (default: minioadmin)
            minio_secret_key: MinIO secret key (default: minioadmin)
            spark_master: Spark master URL (default: spark://localhost:7077)
            trino_host: Trino server host (default: localhost)
            trino_port: Trino server port (default: 8082)
            trino_user: Trino username (default: admin)
            unity_catalog_url: Unity Catalog server URL (default: http://localhost:8081)
        """
        # Get remote host from environment or use localhost
        lakehouse_host = os.getenv("LAKEHOUSE_HOST", "localhost")

        # Resolve configuration with priority: param > env > default
        minio_endpoint = minio_endpoint or os.getenv(
            "LAKEHOUSE_MINIO_ENDPOINT", f"http://{lakehouse_host}:9000"
        )
        minio_access_key = minio_access_key or os.getenv(
            "LAKEHOUSE_MINIO_ACCESS_KEY", "minioadmin"
        )
        minio_secret_key = minio_secret_key or os.getenv(
            "LAKEHOUSE_MINIO_SECRET_KEY", "minioadmin"
        )
        spark_master = spark_master or os.getenv(
            "LAKEHOUSE_SPARK_MASTER", f"spark://{lakehouse_host}:7077"
        )
        trino_host = trino_host or os.getenv(
            "LAKEHOUSE_TRINO_HOST", lakehouse_host
        )
        trino_port = trino_port or int(os.getenv("LAKEHOUSE_TRINO_PORT", "8082"))
        trino_user = trino_user or os.getenv("LAKEHOUSE_TRINO_USER", "admin")
        unity_catalog_url = unity_catalog_url or os.getenv(
            "LAKEHOUSE_UNITY_CATALOG_URL", f"http://{lakehouse_host}:8081"
        )

        # For Spark (DeltaManager), use internal Docker network endpoint
        # This allows Spark (running inside Docker) to communicate with MinIO
        minio_internal_endpoint = os.getenv(
            "LAKEHOUSE_MINIO_INTERNAL_ENDPOINT", "http://minio:9000"
        )

        self.storage = StorageManager(
            endpoint=minio_endpoint,  # External endpoint for client
            access_key=minio_access_key,
            secret_key=minio_secret_key,
        )

        self.delta = DeltaManager(
            spark_master=spark_master,
            minio_endpoint=minio_internal_endpoint,  # Internal endpoint for Spark
            minio_access_key=minio_access_key,
            minio_secret_key=minio_secret_key,
            unity_catalog_url=unity_catalog_url,
        )

        self.query_engine = QueryEngine(
            host=trino_host,
            port=trino_port,
            user=trino_user,
        )

    # Storage Operations

    def upload_parquet(
        self,
        file_path: str,
        bucket: str,
        object_name: Optional[str] = None,
        compression: str = "snappy",
    ) -> str:
        """
        Upload a data file as Parquet to MinIO.

        Args:
            file_path: Path to the file (CSV, JSON, or Parquet)
            bucket: Target bucket name
            object_name: Object name in MinIO (without extension)
            compression: Parquet compression codec

        Returns:
            S3 URI of uploaded file
        """
        return self.storage.upload_parquet(file_path, bucket, object_name, compression)

    def upload_dataframe(
        self,
        df: pd.DataFrame,
        bucket: str,
        object_name: str,
        compression: str = "snappy",
    ) -> str:
        """
        Upload a Pandas DataFrame as Parquet to MinIO.

        Args:
            df: Pandas DataFrame
            bucket: Target bucket name
            object_name: Object name in MinIO
            compression: Parquet compression codec

        Returns:
            S3 URI of uploaded file
        """
        return self.storage.upload_dataframe(df, bucket, object_name, compression)

    def list_objects(self, bucket: str, prefix: str = "") -> List[str]:
        """
        List objects in a bucket.

        Args:
            bucket: Bucket name
            prefix: Filter by prefix

        Returns:
            List of object keys
        """
        return self.storage.list_objects(bucket, prefix)

    # Delta Lake Operations

    def create_delta_table(
        self,
        s3_path: str,
        catalog: str,
        schema: str,
        table: str,
        mode: str = "overwrite",
        partition_by: Optional[List[str]] = None,
    ) -> str:
        """
        Create a Delta table from S3 data and register in Unity Catalog.

        Args:
            s3_path: S3 path to source data
            catalog: Catalog name
            schema: Schema name
            table: Table name
            mode: Write mode (overwrite, append, error, ignore)
            partition_by: Optional list of partition columns

        Returns:
            Delta table location path
        """
        return self.delta.create_delta_table(
            s3_path=s3_path,
            catalog=catalog,
            schema=schema,
            table=table,
            mode=mode,
            partition_by=partition_by,
        )

    def read_delta_table(self, catalog: str, schema: str, table: str):
        """
        Read a Delta table as a Spark DataFrame.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name

        Returns:
            Spark DataFrame
        """
        return self.delta.read_delta_table(catalog, schema, table)

    def optimize_table(self, catalog: str, schema: str, table: str):
        """
        Optimize a Delta table by compacting small files.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
        """
        self.delta.optimize_table(catalog, schema, table)

    def vacuum_table(
        self,
        catalog: str,
        schema: str,
        table: str,
        retention_hours: int = 168,
    ):
        """
        Clean up old files in a Delta table.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
            retention_hours: Hours to retain old files
        """
        self.delta.vacuum_table(catalog, schema, table, retention_hours)

    # Query Operations

    def query(
        self,
        sql: str,
        catalog: Optional[str] = None,
        schema: Optional[str] = None,
    ) -> List[tuple]:
        """
        Execute a SQL query via Trino.

        Args:
            sql: SQL query string
            catalog: Optional catalog name
            schema: Optional schema name

        Returns:
            List of result tuples
        """
        return self.query_engine.query(sql, catalog, schema)

    def query_to_dataframe(
        self,
        sql: str,
        catalog: Optional[str] = None,
        schema: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Execute a SQL query and return results as a DataFrame.

        Args:
            sql: SQL query string
            catalog: Optional catalog name
            schema: Optional schema name

        Returns:
            Pandas DataFrame
        """
        return self.query_engine.query_to_dataframe(sql, catalog, schema)

    def list_catalogs(self) -> List[str]:
        """
        List all available catalogs.

        Returns:
            List of catalog names
        """
        return self.query_engine.list_catalogs()

    def list_schemas(self, catalog: Optional[str] = None) -> List[str]:
        """
        List all schemas in a catalog.

        Args:
            catalog: Catalog name

        Returns:
            List of schema names
        """
        return self.query_engine.list_schemas(catalog)

    def list_tables(
        self,
        catalog: Optional[str] = None,
        schema: Optional[str] = None,
    ) -> List[str]:
        """
        List all tables in a schema.

        Args:
            catalog: Catalog name
            schema: Schema name

        Returns:
            List of table names
        """
        return self.query_engine.list_tables(catalog, schema)

    def describe_table(
        self,
        table: str,
        catalog: Optional[str] = None,
        schema: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Describe the structure of a table.

        Args:
            table: Table name
            catalog: Catalog name
            schema: Schema name

        Returns:
            DataFrame with table structure
        """
        return self.query_engine.describe_table(table, catalog, schema)

    def get_table_stats(
        self,
        table: str,
        catalog: Optional[str] = None,
        schema: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get statistics for a table.

        Args:
            table: Table name
            catalog: Catalog name
            schema: Schema name

        Returns:
            Dictionary with table stats
        """
        return self.query_engine.get_table_stats(table, catalog, schema)

    # Complete Workflow

    def ingest_and_create_table(
        self,
        file_path: str,
        bucket: str,
        catalog: str,
        schema: str,
        table: str,
        object_name: Optional[str] = None,
        partition_by: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Complete workflow: Upload file to MinIO and create Delta table.

        Args:
            file_path: Path to data file
            bucket: MinIO bucket
            catalog: Catalog name
            schema: Schema name
            table: Table name
            object_name: Optional object name
            partition_by: Optional partition columns

        Returns:
            Dictionary with S3 URI and Delta table path
        """
        # Step 1: Upload to MinIO as Parquet
        s3_uri = self.upload_parquet(file_path, bucket, object_name)

        # Step 2: Create Delta table and register in Unity Catalog
        delta_path = self.create_delta_table(
            s3_path=s3_uri,
            catalog=catalog,
            schema=schema,
            table=table,
            partition_by=partition_by,
        )

        return {
            "s3_uri": s3_uri,
            "delta_path": delta_path,
            "table": f"{catalog}.{schema}.{table}",
        }

    def close(self):
        """Close all connections."""
        self.delta.close()
        self.query_engine.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
