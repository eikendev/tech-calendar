"""
Storage backend implementations and registry.
"""

from tech_calendar.storage.backends.base import StorageBackend
from tech_calendar.storage.backends.local_file import LocalFileBackend
from tech_calendar.storage.backends.webdav import WebDAVBackend

__all__ = ["LocalFileBackend", "StorageBackend", "WebDAVBackend"]
