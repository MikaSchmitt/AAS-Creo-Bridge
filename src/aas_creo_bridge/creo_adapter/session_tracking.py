from __future__ import annotations

import logging
import threading
import time
from datetime import UTC, datetime
from enum import Enum
from typing import Callable, Optional

import creopyson

from .types import CreoSessionDelta, CreoSessionFile, CreoSessionState

_logger = logging.getLogger(__name__)


class SessionChangeAction(Enum):
    add = "add"
    remove = "remove"
    revision = "revision"
    active = "active"


SessionChangeListener = Callable[[SessionChangeAction, list[CreoSessionFile]], None]


def snapshot_session(client: creopyson.Client) -> CreoSessionState:
    """Capture file list, per-file revision, and currently active file from Creo."""
    try:
        if not client.is_creo_running():
            return CreoSessionState(
                files={}, active_file_name=None, captured_at=datetime.now(UTC)
            )
    except ConnectionError as e:
        _logger.warning("Failed to connect to Creo: %s", e)
        return CreoSessionState(
            files={}, active_file_name=None, captured_at=datetime.now(UTC)
        )
    file_names = client.file_list() or []
    files: dict[str, CreoSessionFile] = {}

    for file_name in file_names:
        if not isinstance(file_name, str):
            continue
        info = client.file_get_fileinfo(file_name)
        files[file_name] = CreoSessionFile(info.get("file"), info.get("revision"))

    active_data = client.file_get_active() or {}
    active_file_name = (
        active_data.get("file") if isinstance(active_data, dict) else None
    )
    return CreoSessionState(
        files=files, active_file_name=active_file_name, captured_at=datetime.now(UTC)
    )


def diff_session(
        previous: CreoSessionState, current: CreoSessionState
) -> CreoSessionDelta:
    previous_names = set(previous.files)
    current_names = set(current.files)

    added = tuple(
        sorted(
            (current.files[name] for name in (current_names - previous_names)),
            key=lambda item: item.file_name,
        )
    )
    removed = tuple(
        sorted(
            (previous.files[name] for name in (previous_names - current_names)),
            key=lambda item: item.file_name,
        )
    )

    revision_changed_items: list[CreoSessionFile] = []
    for name in sorted(previous_names & current_names):
        previous_file = previous.files[name]
        current_file = current.files[name]
        if previous_file.revision != current_file.revision:
            revision_changed_items.append(current_file)

    active_file_changed = previous.active_file_name != current.active_file_name

    return CreoSessionDelta(
        added=added,
        removed=removed,
        revision_changed=tuple(revision_changed_items),
        active_file_changed=active_file_changed,
        previous_active_file_name=previous.active_file_name,
        current_active_file_name=current.active_file_name,
    )


class CreoSessionTracker:
    """Polling-based tracker for session files, revisions, and active file."""

    def __init__(self, client: creopyson.Client, poll_interval_seconds: float = 1.0):
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be greater than zero")

        self._client = client
        self._poll_interval_seconds = poll_interval_seconds
        self._state: Optional[CreoSessionState] = None
        self._listeners: list[SessionChangeListener] = []
        self._poll_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def add_listener(self, listener: SessionChangeListener) -> None:
        """Register a callback to be notified when the session changes."""
        self._listeners.append(listener)

    def remove_listener(self, listener: SessionChangeListener) -> None:
        """Unregister a previously registered callback."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    @property
    def state(self) -> Optional[CreoSessionState]:
        return self._state

    @property
    def is_polling(self) -> bool:
        return bool(self._poll_thread and self._poll_thread.is_alive())

    def initialize(self) -> CreoSessionState:
        self._state = snapshot_session(self._client)
        return self._state

    def refresh(self) -> tuple[CreoSessionState, CreoSessionDelta]:
        current_state = snapshot_session(self._client)
        if self._state is None:
            self._state = current_state
            return current_state, CreoSessionDelta()

        delta = diff_session(self._state, current_state)
        self._state = current_state
        if delta.has_changes:
            self._notify_listeners(delta)
        return current_state, delta

    def poll_until_changed(self, timeout_seconds: Optional[float] = None) -> None:
        """Start continuous background polling and return immediately."""
        self.start_polling(timeout_seconds=timeout_seconds)

    def start_polling(self, timeout_seconds: Optional[float] = None) -> None:
        """Start a background polling loop if not already running."""
        if self.is_polling:
            return

        self._stop_event.clear()
        self._poll_thread = threading.Thread(
            target=self._poll_loop,
            args=(timeout_seconds,),
            daemon=True,
            name="CreoSessionTrackerPoller",
        )
        self._poll_thread.start()

    def stop_polling(self, join_timeout_seconds: Optional[float] = None) -> None:
        """Stop the background polling loop."""
        self._stop_event.set()
        if self._poll_thread and self._poll_thread.is_alive():
            self._poll_thread.join(timeout=join_timeout_seconds)
        self._poll_thread = None

    def _poll_loop(self, timeout_seconds: Optional[float]) -> None:
        start = time.monotonic()
        if self._state is None:
            self.initialize()

        while not self._stop_event.is_set():
            try:
                self.refresh()
                if (
                        timeout_seconds is not None
                        and (time.monotonic() - start) >= timeout_seconds
                ):
                    break
            except Exception as exc:
                _logger.error(
                    "Error while polling Creo session: %s", exc, exc_info=True
                )

            self._stop_event.wait(self._poll_interval_seconds)

    def _notify_listeners(self, delta: CreoSessionDelta) -> None:
        if delta.added:
            self._emit(SessionChangeAction.add, list(delta.added))
        if delta.removed:
            self._emit(SessionChangeAction.remove, list(delta.removed))
        if delta.revision_changed:
            self._emit(SessionChangeAction.revision, list(delta.revision_changed))
        if delta.active_file_changed:
            files: list[CreoSessionFile] = []
            if self._state and self._state.active_file_name:
                active = self._state.files.get(self._state.active_file_name)
                if active is not None:
                    files = [active]
            self._emit(SessionChangeAction.active, files)

    def _emit(self, action: SessionChangeAction, files: list[CreoSessionFile]) -> None:
        for listener in self._listeners:
            try:
                listener(action, files)
            except Exception as exc:
                _logger.error(
                    "Error in CreoSessionTracker listener: %s", exc, exc_info=True
                )
