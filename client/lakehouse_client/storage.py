"""
Storage module for handling MinIO/S3 operations.
"""

import io
import os
from typing import Optional, Union
import boto3
from botocore.client import Config
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


class StorageManager:
    """Manages storage operations with MinIO/S3."""

    def __init__(
        self,
        endpoint: str = "http://localhost:9000",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
        region: str = "us-east-1",
    ):
        """
        Initialize the StorageManager.

        Args:
            endpoint: MinIO endpoint URL
            access_key: MinIO access key
            secret_key: MinIO secret key
            region: AWS region (for S3 compatibility)
        """
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region

        self.s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=Config(signature_version="s3v4"),
        )

    def create_bucket(self, bucket_name: str) -> bool:
        """
        Create a bucket if it doesn't exist.

        Args:
            bucket_name: Name of the bucket to create

        Returns:
            True if bucket was created or already exists
        """
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            print(f"Bucket '{bucket_name}' already exists")
            return True
        except:
            try:
                self.s3_client.create_bucket(Bucket=bucket_name)
                print(f"Bucket '{bucket_name}' created successfully")
                return True
            except Exception as e:
                print(f"Error creating bucket: {e}")
                return False

    def upload_parquet(
        self,
        file_path: str,
        bucket: str,
        object_name: Optional[str] = None,
        compression: str = "snappy",
    ) -> str:
        """
        Upload a data file as Parquet to MinIO.

        Supports CSV, JSON, and Parquet input files.

        Args:
            file_path: Path to the file to upload
            bucket: Target bucket name
            object_name: Name for the object in MinIO (without extension)
            compression: Parquet compression codec (snappy, gzip, etc.)

        Returns:
            S3 URI of the uploaded file
        """
        # Ensure bucket exists
        self.create_bucket(bucket)

        # Determine object name
        if object_name is None:
            object_name = os.path.splitext(os.path.basename(file_path))[0]

        # Add .parquet extension if not present
        if not object_name.endswith(".parquet"):
            object_name = f"{object_name}.parquet"

        # Read the file into a DataFrame
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == ".csv":
            df = pd.read_csv(file_path)
        elif file_ext == ".json":
            df = pd.read_json(file_path)
        elif file_ext == ".parquet":
            df = pd.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")

        # Convert to PyArrow Table
        table = pa.Table.from_pandas(df)

        # Write to buffer as Parquet
        parquet_buffer = io.BytesIO()
        pq.write_table(table, parquet_buffer, compression=compression)
        parquet_buffer.seek(0)

        # Upload to MinIO
        self.s3_client.upload_fileobj(parquet_buffer, bucket, object_name)

        s3_uri = f"s3a://{bucket}/{object_name}"
        print(f"File uploaded successfully to {s3_uri}")

        return s3_uri

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
            df: Pandas DataFrame to upload
            bucket: Target bucket name
            object_name: Name for the object in MinIO
            compression: Parquet compression codec

        Returns:
            S3 URI of the uploaded file
        """
        # Ensure bucket exists
        self.create_bucket(bucket)

        # Add .parquet extension if not present
        if not object_name.endswith(".parquet"):
            object_name = f"{object_name}.parquet"

        # Convert to PyArrow Table
        table = pa.Table.from_pandas(df)

        # Write to buffer as Parquet
        parquet_buffer = io.BytesIO()
        pq.write_table(table, parquet_buffer, compression=compression)
        parquet_buffer.seek(0)

        # Upload to MinIO
        self.s3_client.upload_fileobj(parquet_buffer, bucket, object_name)

        s3_uri = f"s3a://{bucket}/{object_name}"
        print(f"DataFrame uploaded successfully to {s3_uri}")

        return s3_uri

    def list_objects(self, bucket: str, prefix: str = "") -> list:
        """
        List objects in a bucket.

        Args:
            bucket: Bucket name
            prefix: Filter by prefix

        Returns:
            List of object keys
        """
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
            if "Contents" in response:
                return [obj["Key"] for obj in response["Contents"]]
            return []
        except Exception as e:
            print(f"Error listing objects: {e}")
            return []

    def download_parquet(self, bucket: str, object_name: str) -> pd.DataFrame:
        """
        Download a Parquet file from MinIO as a DataFrame.

        Args:
            bucket: Source bucket name
            object_name: Object key in MinIO

        Returns:
            Pandas DataFrame
        """
        buffer = io.BytesIO()
        self.s3_client.download_fileobj(bucket, object_name, buffer)
        buffer.seek(0)

        df = pd.read_parquet(buffer)
        return df
