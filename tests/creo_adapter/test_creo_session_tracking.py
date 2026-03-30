from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock

from aas_creo_bridge.adapters.session_tracking import (
    CreoSessionTracker,
    SessionChangeAction,
    diff_session,
    snapshot_session,
)
from aas_creo_bridge.adapters.types import CreoSessionFile, CreoSessionState


def _build_client() -> MagicMock:
    client = MagicMock()
    client.file_list.return_value = ["part_a.prt", "assy_b.asm"]
    client.file_get_active.return_value = {"file": "part_a.prt"}

    def file_info_side_effect(file_name: str):
        if file_name == "part_a.prt":
            return {"file": "part_a.prt", "revision": 7}
        if file_name == "assy_b.asm":
            return {"file": "assy_b.asm", "revision": 4}
        return {"file": file_name}

    client.file_get_fileinfo.side_effect = file_info_side_effect
    return client


def test_snapshot_session_tracks_open_files_revision_and_active_file() -> None:
    client = _build_client()

    state = snapshot_session(client)

    assert state.active_file_name == "part_a.prt"
    assert state.files["part_a.prt"].revision == 7
    assert state.files["assy_b.asm"].revision == 4


def test_diff_session_detects_added_removed_revision_and_active_change() -> None:
    previous = CreoSessionState(
        files={
            "part_a.prt": CreoSessionFile("part_a.prt", revision=1),
            "old_part.prt": CreoSessionFile("old_part.prt", revision=3),
        },
        active_file_name="part_a.prt",
    )
    current = CreoSessionState(
        files={
            "part_a.prt": CreoSessionFile("part_a.prt", revision=2),
            "new_part.prt": CreoSessionFile("new_part.prt", revision=1),
        },
        active_file_name="new_part.prt",
    )

    delta = diff_session(previous, current)

    assert [entry.file_name for entry in delta.added] == ["new_part.prt"]
    assert [entry.file_name for entry in delta.removed] == ["old_part.prt"]
    assert [entry.file_name for entry in delta.revision_changed] == ["part_a.prt"]
    assert delta.active_file_changed is True
    assert delta.previous_active_file_name == "part_a.prt"
    assert delta.current_active_file_name == "new_part.prt"


def test_tracker_refresh_returns_no_delta_on_first_refresh() -> None:
    client = _build_client()
    tracker = CreoSessionTracker(client, poll_interval_seconds=0.01)

    _, delta = tracker.refresh()

    assert delta.has_changes is False


def test_tracker_refresh_detects_change_after_initialization() -> None:
    client = _build_client()
    tracker = CreoSessionTracker(client, poll_interval_seconds=0.01)
    tracker.initialize()

    client.file_get_active.return_value = {"file": "assy_b.asm.4"}

    _, delta = tracker.refresh()

    assert delta.active_file_changed is True
    assert delta.current_active_file_name == "assy_b.asm.4"


def test_tracker_remove_listener_stops_notifications() -> None:
    client = _build_client()
    tracker = CreoSessionTracker(client, poll_interval_seconds=0.01)
    events: list[tuple[SessionChangeAction, list[CreoSessionFile]]] = []

    def listener(action: SessionChangeAction, files: list[CreoSessionFile]) -> None:
        events.append((action, files))

    tracker.add_listener(listener)
    tracker.remove_listener(listener)
    tracker.initialize()

    client.file_get_active.return_value = {"file": "assy_b.asm"}
    tracker.refresh()

    assert events == []


def test_poll_until_changed_starts_background_polling_and_returns_immediately() -> None:
    client = _build_client()
    tracker = CreoSessionTracker(client, poll_interval_seconds=0.01)

    start = time.monotonic()
    tracker.poll_until_changed(timeout_seconds=0.2)
    elapsed = time.monotonic() - start

    assert elapsed < 0.05
    assert tracker.is_polling is True

    tracker.stop_polling(join_timeout_seconds=0.5)
    assert tracker.is_polling is False


def test_background_polling_notifies_listener_on_change() -> None:
    client = _build_client()
    tracker = CreoSessionTracker(client, poll_interval_seconds=0.01)
    notified = threading.Event()

    def listener(action: SessionChangeAction, files: list[CreoSessionFile]) -> None:
        if action == SessionChangeAction.active and files and files[0].file_name == "assy_b.asm":
            notified.set()

    tracker.add_listener(listener)
    tracker.initialize()
    tracker.start_polling()

    client.file_get_active.return_value = {"file": "assy_b.asm"}

    assert notified.wait(timeout=1.0)
    tracker.stop_polling(join_timeout_seconds=0.5)
