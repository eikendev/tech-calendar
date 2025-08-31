from pathlib import Path

from .logging import get_logger

logger = get_logger(__name__)


def write_text_file(path: str | Path, content: str, *, encoding: str = "utf-8") -> Path:
    p = Path(path)

    logger.debug(
        "file_write_start",
        extra={"path": str(p), "encoding": encoding},
    )

    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding=encoding)
        logger.info("file_write_success", extra={"path": str(p)})
        return p
    except Exception as exc:
        logger.exception("file_write_error", exc_info=exc, extra={"path": str(p)})
        raise
