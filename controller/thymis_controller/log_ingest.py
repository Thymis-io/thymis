"""Batched, off-loop writer for device syslog entries.

Devices post one small batch per syslog transaction; committing each request
serially against a multi-GB SQLite database makes ingest latency track disk and
lock contention. The HTTP endpoint only validates and enqueues; this writer
merges queued entries into few transactions.
"""

from __future__ import annotations

import asyncio
import itertools
import logging
from typing import TYPE_CHECKING, cast

from sqlalchemy import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from thymis_controller import crud

if TYPE_CHECKING:
    from thymis_controller import models

logger = logging.getLogger(__name__)

_SENTINEL = object()
_QueueItem = tuple[str, "list[models.LogEntry]"]


class LogIngestor:
    def __init__(
        self,
        engine: Engine,
        *,
        max_queue: int = 50_000,
        max_batch: int = 500,
        max_entries: int = 2_000,
        max_delay: float = 0.5,
    ) -> None:
        self.engine = engine
        self.max_batch = max_batch
        self.max_entries = max_entries
        self.max_delay = max_delay
        self.queue: asyncio.Queue[_QueueItem | object] = asyncio.Queue(
            maxsize=max_queue
        )
        self._task: asyncio.Task | None = None
        self._stopping = False
        self._dropped = 0

    def start(self) -> None:
        self._task = asyncio.create_task(self._run(), name="log-ingestor")

    def submit(self, ssh_public_key: str, entries: list[models.LogEntry]) -> None:
        if not entries:
            return
        try:
            self.queue.put_nowait((ssh_public_key, entries))
        except asyncio.QueueFull:
            self._dropped += 1
            if self._dropped == 1 or self._dropped % 1000 == 0:
                logger.warning(
                    "Log ingest queue full; dropped %d entries so far", self._dropped
                )

    async def stop(self) -> None:
        self._stopping = True
        if self._task is not None:
            self._wake()
            await self._task
            self._task = None

        pending: list[_QueueItem] = []
        while True:
            try:
                item = self.queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            if item is not _SENTINEL:
                pending.append(cast(_QueueItem, item))
        for chunk in itertools.batched(pending, self.max_batch):
            await asyncio.to_thread(self._flush_batch, list(chunk))

    def _wake(self) -> None:
        while True:
            try:
                self.queue.put_nowait(_SENTINEL)
                return
            except asyncio.QueueFull:
                try:
                    self.queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass

    async def _run(self) -> None:
        loop = asyncio.get_running_loop()
        while True:
            first = await self.queue.get()
            if first is _SENTINEL:
                break
            first = cast(_QueueItem, first)
            batch: list[_QueueItem] = [first]
            entry_count = len(first[1])
            deadline = loop.time() + self.max_delay
            while not self._stopping and len(batch) < self.max_batch:
                if entry_count >= self.max_entries:
                    break
                remaining = deadline - loop.time()
                if remaining <= 0:
                    break
                try:
                    item = await asyncio.wait_for(self.queue.get(), remaining)
                except TimeoutError:
                    break
                if item is _SENTINEL:
                    break
                item = cast(_QueueItem, item)
                if entry_count + len(item[1]) > self.max_entries:
                    self.queue.put_nowait(item)
                    break
                batch.append(item)
                entry_count += len(item[1])
            while not self._stopping and len(batch) < self.max_batch:
                if entry_count >= self.max_entries:
                    break
                try:
                    item = self.queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                if item is _SENTINEL:
                    break
                item = cast(_QueueItem, item)
                if entry_count + len(item[1]) > self.max_entries:
                    self.queue.put_nowait(item)
                    break
                batch.append(item)
                entry_count += len(item[1])
            for attempt in range(3):
                try:
                    await asyncio.to_thread(self._flush_batch, batch)
                    break
                except OperationalError:
                    if attempt == 2:
                        logger.exception(
                            "Failed to persist %d ingested log batches",
                            len(batch),
                        )
                    else:
                        await asyncio.sleep(1)
                except Exception:  # noqa: BLE001 - keep the writer alive
                    logger.exception(
                        "Failed to persist %d ingested log batches", len(batch)
                    )
                    break
            if self._stopping:
                break

    def _flush_batch(self, batch: list[_QueueItem]) -> None:
        grouped: dict[str, list[models.LogEntry]] = {}
        for ssh_public_key, entries in batch:
            grouped.setdefault(ssh_public_key, []).extend(entries)
        with Session(self.engine) as session:
            for ssh_public_key, entries in grouped.items():
                crud.logs.create_batch(session, entries, ssh_public_key)
