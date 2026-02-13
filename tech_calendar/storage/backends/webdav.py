"""
WebDAV storage backend for SQLite databases.
"""

from __future__ import annotations

import posixpath
import tempfile
from dataclasses import dataclass
from pathlib import Path

from pydantic import AnyUrl, HttpUrl, TypeAdapter
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from webdav3.client import Client
from webdav3.exceptions import WebDavException

from tech_calendar.exceptions import StorageError
from tech_calendar.logging import get_logger
from tech_calendar.storage.backends.base import StorageBackend

logger = get_logger(__name__)
_TARGET_URL = TypeAdapter(HttpUrl)


@dataclass(frozen=True)
class WebDAVTarget:
    """
    Parsed WebDAV target details.
    """

    base_url: str
    remote_path: str
    remote_dir: str
    filename: str
    username: str | None
    password: str | None
    sanitized_url: str


class WebDAVBackend(StorageBackend):
    """
    Storage backend for WebDAV-hosted SQLite files.
    """

    scheme = "webdav"

    def __init__(self, location: AnyUrl) -> None:
        """
        Parse a WebDAV location and initialize the WebDAV client.
        """
        super().__init__(location)
        self._target = self._parse_webdav_location(location)
        self._client = self._build_client(self._target)
        self._temp_dir: tempfile.TemporaryDirectory[str] | None = None
        self._local_path: Path | None = None

    def prepare(self) -> Path:
        """
        Download the remote database into a temporary local path.
        """
        self._temp_dir = tempfile.TemporaryDirectory()
        self._local_path = Path(self._temp_dir.name) / self._target.filename
        if self._remote_exists(self._target.remote_path):
            try:
                self._download(self._target.remote_path, self._local_path)
            except StorageError:
                self._temp_dir.cleanup()
                self._temp_dir = None
                self._local_path = None
                raise
        return self._local_path

    def finalize(self) -> None:
        """
        Upload the local database back to WebDAV and clean up.
        """
        if self._local_path is None:
            return None
        try:
            self._ensure_remote_dir()
            self._upload(self._target.remote_path, self._local_path)
        finally:
            if self._temp_dir is not None:
                self._temp_dir.cleanup()
                self._temp_dir = None

    @staticmethod
    def _parse_webdav_location(location: AnyUrl) -> WebDAVTarget:
        """
        Validate and parse a WebDAV URL embedded after the webdav:// prefix.
        """
        if location.scheme != "webdav":
            raise StorageError(f"invalid webdav storage scheme: {location.scheme}")

        target = WebDAVBackend._extract_target(location)
        parsed = _TARGET_URL.validate_python(target)
        if not parsed.scheme:
            raise StorageError("webdav target is missing a scheme")
        if not parsed.host:
            raise StorageError("webdav target is missing a hostname")

        raw_path = parsed.path or ""
        if not raw_path or raw_path.endswith("/"):
            raise StorageError("webdav target must include a filename")

        normalized_path = posixpath.normpath(raw_path)
        remote_path = normalized_path.lstrip("/")
        if not remote_path or remote_path.endswith("/"):
            raise StorageError("webdav target must include a filename")

        remote_dir = posixpath.dirname(remote_path)
        filename = posixpath.basename(remote_path)

        netloc = parsed.host
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"

        base_url = f"{parsed.scheme}://{netloc}"
        sanitized_url = f"{base_url}{raw_path}"

        return WebDAVTarget(
            base_url=base_url,
            remote_path=remote_path,
            remote_dir=remote_dir,
            filename=filename,
            username=parsed.username,
            password=parsed.password,
            sanitized_url=sanitized_url,
        )

    @staticmethod
    def _extract_target(location: AnyUrl) -> str:
        """
        Convert the AnyUrl value into the embedded WebDAV target URL.
        """
        path = location.path or ""

        if location.host:
            if path.startswith("//"):
                return f"{location.host}:{path}"
            raise StorageError("webdav target must include an http or https scheme")

        if not path:
            raise StorageError("webdav target is empty")

        return path.lstrip("/")

    @staticmethod
    def _build_client(target: WebDAVTarget) -> Client:
        """
        Build a WebDAV client using sanitized connection options.
        """
        options: dict[str, str] = {"webdav_hostname": target.base_url}

        if target.username:
            options["webdav_login"] = target.username
        if target.password:
            options["webdav_password"] = target.password

        return Client(options)

    def _ensure_remote_dir(self) -> None:
        """
        Ensure the remote directory tree exists for the database file.
        """
        if not self._target.remote_dir:
            return None

        current = ""

        for part in self._target.remote_dir.split("/"):
            current = f"{current}/{part}" if current else part
            if not self._remote_exists(current):
                self._mkdir(current)

        return None

    def _remote_exists(self, remote_path: str) -> bool:
        """
        Check whether a WebDAV resource exists, treating 404 as missing.
        """
        try:
            return bool(self._check(remote_path))
        except WebDavException as exc:
            status = getattr(exc, "status", None)
            if status == 404:
                return False
            logger.error("webdav_check_failed", extra={"path": remote_path, "error": str(exc)})
            raise StorageError("failed to check webdav resource") from exc

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1.5, min=1, max=10),
        retry=retry_if_exception_type(WebDavException),
    )
    def _check(self, remote_path: str) -> bool:
        """
        Call the WebDAV check operation with retries.
        """
        return self._client.check(remote_path)

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1.5, min=1, max=10),
        retry=retry_if_exception_type(WebDavException),
    )
    def _download(self, remote_path: str, local_path: Path) -> None:
        """
        Download the remote database file into the local path.
        """
        logger.info("webdav_download_start", extra={"path": remote_path, "target": self._target.sanitized_url})

        try:
            self._client.download_sync(remote_path=remote_path, local_path=str(local_path))
        except WebDavException as exc:
            logger.error("webdav_download_failed", extra={"path": remote_path, "error": str(exc)})
            raise StorageError("failed to download webdav database") from exc

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1.5, min=1, max=10),
        retry=retry_if_exception_type(WebDavException),
    )
    def _mkdir(self, remote_path: str) -> None:
        """
        Create a WebDAV directory with retries.
        """
        try:
            self._client.mkdir(remote_path)
        except WebDavException as exc:
            logger.error("webdav_mkdir_failed", extra={"path": remote_path, "error": str(exc)})
            raise StorageError("failed to create webdav directory") from exc

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1.5, min=1, max=10),
        retry=retry_if_exception_type(WebDavException),
    )
    def _upload(self, remote_path: str, local_path: Path) -> None:
        """
        Upload the local database file to WebDAV.
        """
        logger.info("webdav_upload_start", extra={"path": remote_path, "target": self._target.sanitized_url})

        try:
            self._client.upload_sync(remote_path=remote_path, local_path=str(local_path))
        except WebDavException as exc:
            logger.error("webdav_upload_failed", extra={"path": remote_path, "error": str(exc)})
            raise StorageError("failed to upload webdav database") from exc
