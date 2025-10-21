"""
Lakehouse Client - A Python client for interacting with the Lakehouse platform.
"""

from .client import LakehouseClient
from .simple_client import SimpleLakehouseClient

__version__ = "0.1.0"
__all__ = ["LakehouseClient", "SimpleLakehouseClient"]
