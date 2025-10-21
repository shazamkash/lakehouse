"""
Query module for executing SQL queries via Trino.
"""

from typing import List, Dict, Any, Optional, Union
import trino
from trino.auth import BasicAuthentication
import pandas as pd


class QueryEngine:
    """Manages SQL query execution via Trino."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8082,
        user: str = "admin",
        catalog: str = "delta",
        schema: str = "default",
        auth: Optional[BasicAuthentication] = None,
    ):
        """
        Initialize the QueryEngine.

        Args:
            host: Trino server host
            port: Trino server port
            user: Username for authentication
            catalog: Default catalog to use
            schema: Default schema to use
            auth: Optional authentication object
        """
        self.host = host
        self.port = port
        self.user = user
        self.catalog = catalog
        self.schema = schema
        self.auth = auth

        self.connection = trino.dbapi.connect(
            host=host,
            port=port,
            user=user,
            catalog=catalog,
            schema=schema,
            auth=auth,
        )

    def query(
        self,
        sql: str,
        catalog: Optional[str] = None,
        schema: Optional[str] = None,
    ) -> List[tuple]:
        """
        Execute a SQL query and return results.

        Args:
            sql: SQL query string
            catalog: Optional catalog to use (overrides default)
            schema: Optional schema to use (overrides default)

        Returns:
            List of result tuples
        """
        cursor = self.connection.cursor()

        # Set catalog and schema if specified
        if catalog:
            cursor.execute(f"USE {catalog}.{schema or self.schema}")

        cursor.execute(sql)
        results = cursor.fetchall()

        return results

    def query_to_dataframe(
        self,
        sql: str,
        catalog: Optional[str] = None,
        schema: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Execute a SQL query and return results as a Pandas DataFrame.

        Args:
            sql: SQL query string
            catalog: Optional catalog to use (overrides default)
            schema: Optional schema to use (overrides default)

        Returns:
            Pandas DataFrame with query results
        """
        cursor = self.connection.cursor()

        # Set catalog and schema if specified
        if catalog:
            cursor.execute(f"USE {catalog}.{schema or self.schema}")

        cursor.execute(sql)

        # Get column names
        columns = [desc[0] for desc in cursor.description]

        # Fetch all results
        results = cursor.fetchall()

        # Create DataFrame
        df = pd.DataFrame(results, columns=columns)

        return df

    def execute(
        self,
        sql: str,
        catalog: Optional[str] = None,
        schema: Optional[str] = None,
    ) -> bool:
        """
        Execute a SQL statement (DDL/DML) without returning results.

        Args:
            sql: SQL statement
            catalog: Optional catalog to use (overrides default)
            schema: Optional schema to use (overrides default)

        Returns:
            True if execution successful
        """
        try:
            cursor = self.connection.cursor()

            # Set catalog and schema if specified
            if catalog:
                cursor.execute(f"USE {catalog}.{schema or self.schema}")

            cursor.execute(sql)
            return True
        except Exception as e:
            print(f"Error executing SQL: {e}")
            return False

    def list_catalogs(self) -> List[str]:
        """
        List all available catalogs.

        Returns:
            List of catalog names
        """
        results = self.query("SHOW CATALOGS")
        return [row[0] for row in results]

    def list_schemas(self, catalog: Optional[str] = None) -> List[str]:
        """
        List all schemas in a catalog.

        Args:
            catalog: Catalog name (uses default if not specified)

        Returns:
            List of schema names
        """
        catalog = catalog or self.catalog
        results = self.query(f"SHOW SCHEMAS FROM {catalog}")
        return [row[0] for row in results]

    def list_tables(
        self,
        catalog: Optional[str] = None,
        schema: Optional[str] = None,
    ) -> List[str]:
        """
        List all tables in a schema.

        Args:
            catalog: Catalog name (uses default if not specified)
            schema: Schema name (uses default if not specified)

        Returns:
            List of table names
        """
        catalog = catalog or self.catalog
        schema = schema or self.schema
        results = self.query(f"SHOW TABLES FROM {catalog}.{schema}")
        return [row[0] for row in results]

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
            catalog: Catalog name (uses default if not specified)
            schema: Schema name (uses default if not specified)

        Returns:
            DataFrame with table structure
        """
        catalog = catalog or self.catalog
        schema = schema or self.schema
        sql = f"DESCRIBE {catalog}.{schema}.{table}"
        return self.query_to_dataframe(sql)

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
            catalog: Catalog name (uses default if not specified)
            schema: Schema name (uses default if not specified)

        Returns:
            Dictionary with table statistics
        """
        catalog = catalog or self.catalog
        schema = schema or self.schema
        full_table = f"{catalog}.{schema}.{table}"

        stats = {}

        # Get row count
        try:
            count_result = self.query(f"SELECT COUNT(*) FROM {full_table}")
            stats["row_count"] = count_result[0][0] if count_result else 0
        except:
            stats["row_count"] = None

        # Get table info
        try:
            info_df = self.describe_table(table, catalog, schema)
            stats["columns"] = len(info_df)
            stats["column_info"] = info_df.to_dict("records")
        except:
            stats["columns"] = None
            stats["column_info"] = []

        return stats

    def query_iterator(
        self,
        sql: str,
        catalog: Optional[str] = None,
        schema: Optional[str] = None,
        batch_size: int = 1000,
    ):
        """
        Execute a query and return results as an iterator (for large result sets).

        Args:
            sql: SQL query string
            catalog: Optional catalog to use (overrides default)
            schema: Optional schema to use (overrides default)
            batch_size: Number of rows to fetch per batch

        Yields:
            Batches of result tuples
        """
        cursor = self.connection.cursor()

        # Set catalog and schema if specified
        if catalog:
            cursor.execute(f"USE {catalog}.{schema or self.schema}")

        cursor.execute(sql)

        while True:
            rows = cursor.fetchmany(batch_size)
            if not rows:
                break
            yield rows

    def create_view(
        self,
        view_name: str,
        sql: str,
        catalog: Optional[str] = None,
        schema: Optional[str] = None,
        replace: bool = True,
    ) -> bool:
        """
        Create a view from a SQL query.

        Args:
            view_name: Name for the view
            sql: SQL query defining the view
            catalog: Optional catalog to use (overrides default)
            schema: Optional schema to use (overrides default)
            replace: Whether to replace if view exists

        Returns:
            True if creation successful
        """
        catalog = catalog or self.catalog
        schema = schema or self.schema

        replace_clause = "OR REPLACE " if replace else ""
        create_sql = f"CREATE {replace_clause}VIEW {catalog}.{schema}.{view_name} AS {sql}"

        return self.execute(create_sql, catalog, schema)

    def drop_table(
        self,
        table: str,
        catalog: Optional[str] = None,
        schema: Optional[str] = None,
        if_exists: bool = True,
    ) -> bool:
        """
        Drop a table.

        Args:
            table: Table name
            catalog: Optional catalog to use (overrides default)
            schema: Optional schema to use (overrides default)
            if_exists: Add IF EXISTS clause

        Returns:
            True if successful
        """
        catalog = catalog or self.catalog
        schema = schema or self.schema

        if_exists_clause = "IF EXISTS " if if_exists else ""
        sql = f"DROP TABLE {if_exists_clause}{catalog}.{schema}.{table}"

        return self.execute(sql, catalog, schema)

    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
