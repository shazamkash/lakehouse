"""
Simple Lakehouse Client - No Java Required

This client only handles:
- Uploading data to MinIO
- Querying tables via Trino

For Delta table creation, use the server-side script:
    python server/create_delta_table.py <s3_path> <catalog> <schema> <table>

This avoids the need for Java/Spark to be installed on the client machine.
"""

from typing import Optional, List, Dict, Any
import os
import pandas as pd

from .storage import StorageManager
from .query import QueryEngine


class SimpleLakehouseClient:
    """
    Simplified Lakehouse client for remote deployments.

    Only requires MinIO and Trino access - no local Java/Spark needed.
    Use server-side scripts for Delta table operations.
    """

    def __init__(
        self,
        minio_endpoint: Optional[str] = None,
        minio_access_key: Optional[str] = None,
        minio_secret_key: Optional[str] = None,
        trino_host: Optional[str] = None,
        trino_port: Optional[int] = None,
        trino_user: Optional[str] = None,
    ):
        """
        Initialize the Simple Lakehouse Client.

        Configuration priority:
        1. Explicitly passed parameters
        2. Environment variables (LAKEHOUSE_*)
        3. Default values

        Environment Variables:
            LAKEHOUSE_HOST: Remote server IP/hostname
            LAKEHOUSE_MINIO_ENDPOINT: MinIO endpoint URL
            LAKEHOUSE_MINIO_ACCESS_KEY: MinIO access key
            LAKEHOUSE_MINIO_SECRET_KEY: MinIO secret key
            LAKEHOUSE_TRINO_HOST: Trino server host
            LAKEHOUSE_TRINO_PORT: Trino server port
            LAKEHOUSE_TRINO_USER: Trino username

        Args:
            minio_endpoint: MinIO endpoint URL
            minio_access_key: MinIO access key
            minio_secret_key: MinIO secret key
            trino_host: Trino server host
            trino_port: Trino server port
            trino_user: Trino username
        """
        # Get remote host from environment or use localhost
        lakehouse_host = os.getenv("LAKEHOUSE_HOST", "localhost")

        # Resolve configuration
        minio_endpoint = minio_endpoint or os.getenv(
            "LAKEHOUSE_MINIO_ENDPOINT", f"http://{lakehouse_host}:9000"
        )
        minio_access_key = minio_access_key or os.getenv(
            "LAKEHOUSE_MINIO_ACCESS_KEY", "minioadmin"
        )
        minio_secret_key = minio_secret_key or os.getenv(
            "LAKEHOUSE_MINIO_SECRET_KEY", "minioadmin"
        )
        trino_host = trino_host or os.getenv("LAKEHOUSE_TRINO_HOST", lakehouse_host)
        trino_port = trino_port or int(os.getenv("LAKEHOUSE_TRINO_PORT", "8082"))
        trino_user = trino_user or os.getenv("LAKEHOUSE_TRINO_USER", "admin")

        self.storage = StorageManager(
            endpoint=minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
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

    def close(self):
        """Close all connections."""
        self.query_engine.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
