"""Ingestion pipeline: read documents, extract, validate, store."""

from __future__ import annotations

from pathlib import Path

from .extract import ConfigError, Extractor
from .models import Invoice
from .store import Store
from .validate import validate


def ingest_directory(
    directory: str | Path,
    extractor: Extractor,
    store: Store,
    pattern: str = "*.txt",
) -> list[Invoice]:
    """Process every matching file. One bad document never stops the batch.

    Configuration errors are the exception: they affect every file, so they propagate.
    """
    results: list[Invoice] = []
    for path in sorted(Path(directory).glob(pattern)):
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            invoice = extractor.extract(text, path.name)
        except ConfigError:
            raise
        except Exception as exc:  # noqa: BLE001 - a bad document must not stop the batch
            invoice = Invoice(source=path.name, issues=[f"extraction failed: {exc}"])
        invoice = validate(invoice)
        store.upsert(invoice)
        results.append(invoice)
    return results
