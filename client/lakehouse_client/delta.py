"""
Delta Lake module for creating and managing Delta tables.
"""

from typing import Optional, Dict, Any
import requests
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip


class DeltaManager:
    """Manages Delta Lake operations and Unity Catalog integration."""

    def __init__(
        self,
        spark_master: str = "spark://localhost:7077",
        minio_endpoint: str = "http://minio:9000",
        minio_access_key: str = "minioadmin",
        minio_secret_key: str = "minioadmin",
        unity_catalog_url: str = "http://localhost:8081",
    ):
        """
        Initialize the DeltaManager.

        Args:
            spark_master: Spark master URL
            minio_endpoint: MinIO endpoint URL
            minio_access_key: MinIO access key
            minio_secret_key: MinIO secret key
            unity_catalog_url: Unity Catalog server URL
        """
        self.spark_master = spark_master
        self.minio_endpoint = minio_endpoint
        self.minio_access_key = minio_access_key
        self.minio_secret_key = minio_secret_key
        self.unity_catalog_url = unity_catalog_url
        self._spark = None

    @property
    def spark(self) -> SparkSession:
        """
        Get or create a Spark session configured for Delta Lake.

        Returns:
            SparkSession configured with Delta Lake support
        """
        if self._spark is None:
            builder = (
                SparkSession.builder.appName("LakehouseClient")
                .master(self.spark_master)
                .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
                .config(
                    "spark.sql.catalog.spark_catalog",
                    "org.apache.spark.sql.delta.catalog.DeltaCatalog",
                )
                .config("spark.hadoop.fs.s3a.endpoint", self.minio_endpoint)
                .config("spark.hadoop.fs.s3a.access.key", self.minio_access_key)
                .config("spark.hadoop.fs.s3a.secret.key", self.minio_secret_key)
                .config("spark.hadoop.fs.s3a.path.style.access", "true")
                .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
                .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
                .config("spark.sql.warehouse.dir", "s3a://warehouse/")
            )

            self._spark = configure_spark_with_delta_pip(builder).getOrCreate()

        return self._spark

    def create_delta_table(
        self,
        s3_path: str,
        catalog: str,
        schema: str,
        table: str,
        mode: str = "overwrite",
        partition_by: Optional[list] = None,
    ) -> str:
        """
        Create a Delta table from S3 data and register it in Unity Catalog.

        Args:
            s3_path: S3 path to source data (e.g., s3a://bucket/path.parquet)
            catalog: Unity Catalog name
            schema: Schema/database name
            table: Table name
            mode: Write mode (overwrite, append, error, ignore)
            partition_by: Optional list of columns to partition by

        Returns:
            Delta table location path
        """
        # Read source data
        print(f"Reading data from {s3_path}")
        df = self.spark.read.parquet(s3_path)

        # Construct Delta table path
        delta_path = f"s3a://warehouse/{catalog}/{schema}/{table}"

        # Write as Delta table
        print(f"Writing Delta table to {delta_path}")
        writer = df.write.format("delta").mode(mode)

        if partition_by:
            writer = writer.partitionBy(*partition_by)

        writer.save(delta_path)

        # Register in Unity Catalog
        self.register_table_in_unity_catalog(
            catalog=catalog,
            schema=schema,
            table=table,
            delta_path=delta_path,
        )

        print(f"Delta table created: {catalog}.{schema}.{table}")
        return delta_path

    def register_table_in_unity_catalog(
        self,
        catalog: str,
        schema: str,
        table: str,
        delta_path: str,
    ) -> bool:
        """
        Register a Delta table in Unity Catalog.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
            delta_path: Path to Delta table

        Returns:
            True if registration successful
        """
        try:
            # First, ensure catalog exists
            self._ensure_catalog_exists(catalog)

            # Ensure schema exists
            self._ensure_schema_exists(catalog, schema)

            # Register the table using Spark SQL
            full_table_name = f"{catalog}.{schema}.{table}"

            # Drop table if exists
            self.spark.sql(f"DROP TABLE IF EXISTS {full_table_name}")

            # Create external table
            create_table_sql = f"""
            CREATE TABLE {full_table_name}
            USING DELTA
            LOCATION '{delta_path}'
            """

            self.spark.sql(create_table_sql)
            print(f"Table registered in Unity Catalog: {full_table_name}")

            return True

        except Exception as e:
            print(f"Error registering table in Unity Catalog: {e}")
            # Fallback: try using REST API if available
            return self._register_table_via_api(catalog, schema, table, delta_path)

    def _ensure_catalog_exists(self, catalog: str) -> bool:
        """Ensure a catalog exists in Unity Catalog."""
        try:
            self.spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")
            print(f"Catalog '{catalog}' is ready")
            return True
        except Exception as e:
            print(f"Note: Catalog creation - {e}")
            return False

    def _ensure_schema_exists(self, catalog: str, schema: str) -> bool:
        """Ensure a schema exists in Unity Catalog."""
        try:
            self.spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
            print(f"Schema '{catalog}.{schema}' is ready")
            return True
        except Exception as e:
            print(f"Note: Schema creation - {e}")
            return False

    def _register_table_via_api(
        self, catalog: str, schema: str, table: str, delta_path: str
    ) -> bool:
        """
        Register table via Unity Catalog REST API as fallback.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
            delta_path: Delta table location

        Returns:
            True if successful
        """
        try:
            url = f"{self.unity_catalog_url}/api/2.1/unity-catalog/tables"

            payload = {
                "catalog_name": catalog,
                "schema_name": schema,
                "name": table,
                "table_type": "EXTERNAL",
                "data_source_format": "DELTA",
                "storage_location": delta_path,
            }

            response = requests.post(url, json=payload)

            if response.status_code in [200, 201]:
                print(f"Table registered via API: {catalog}.{schema}.{table}")
                return True
            else:
                print(f"API registration returned: {response.status_code}")
                return False

        except Exception as e:
            print(f"Error in API registration: {e}")
            return False

    def read_delta_table(self, catalog: str, schema: str, table: str):
        """
        Read a Delta table.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name

        Returns:
            Spark DataFrame
        """
        full_table_name = f"{catalog}.{schema}.{table}"
        return self.spark.read.format("delta").table(full_table_name)

    def get_table_info(self, catalog: str, schema: str, table: str) -> Dict[str, Any]:
        """
        Get information about a Delta table.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name

        Returns:
            Dictionary with table information
        """
        full_table_name = f"{catalog}.{schema}.{table}"

        # Get table details
        df = self.spark.sql(f"DESCRIBE EXTENDED {full_table_name}")
        details = {row.col_name: row.data_type for row in df.collect()}

        return details

    def optimize_table(self, catalog: str, schema: str, table: str):
        """
        Optimize a Delta table by compacting small files.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
        """
        full_table_name = f"{catalog}.{schema}.{table}"
        self.spark.sql(f"OPTIMIZE {full_table_name}")
        print(f"Table optimized: {full_table_name}")

    def vacuum_table(self, catalog: str, schema: str, table: str, retention_hours: int = 168):
        """
        Clean up old files in a Delta table.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
            retention_hours: Number of hours to retain old files (default: 168 = 7 days)
        """
        full_table_name = f"{catalog}.{schema}.{table}"
        self.spark.sql(f"VACUUM {full_table_name} RETAIN {retention_hours} HOURS")
        print(f"Table vacuumed: {full_table_name}")

    def close(self):
        """Close the Spark session."""
        if self._spark is not None:
            self._spark.stop()
            self._spark = None
