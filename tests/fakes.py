"""Test doubles standing in for kitty's Boss/TabManager/Tab/WindowList objects.

Kept deliberately minimal: only the attributes pounce.py actually reads, so a
change here that isn't exercised by real kitty behaviour stands out. Typed
against pounce.py's BossLike/TabLike/WindowListLike/WindowGroupLike protocols
so a mismatch (e.g. a return type these fakes get wrong) is caught statically,
not just at runtime.
"""

from collections.abc import Iterator, Mapping


class FakeWindow:
    def __init__(self, window_id: int) -> None:
        self.id = window_id

    def __repr__(self) -> str:
        return f'FakeWindow(id={self.id})'


class FakeWindowGroup:
    """Stands in for kitty's WindowGroup: the last window is the active one."""

    def __init__(self, windows: list[FakeWindow]) -> None:
        self.windows = windows


class FakeWindowList:
    """Stands in for kitty's WindowList: `groups` is on-screen/cycling order."""

    def __init__(self, groups: list[FakeWindowGroup]) -> None:
        self.groups = groups


class FakeTab:
    def __init__(self, groups: list[FakeWindowGroup]) -> None:
        self.windows = FakeWindowList(groups)


class FakeTabManager:
    """Stands in for kitty's TabManager: iteration yields its tabs in order."""

    def __init__(self, tabs: list[FakeTab]) -> None:
        self.tabs = tabs

    def __iter__(self) -> Iterator[FakeTab]:
        return iter(self.tabs)


class FakeBoss:
    """Stands in for kitty's Boss: an insertion-ordered os_window_map."""

    def __init__(self, os_window_map: Mapping[int, FakeTabManager], active_window: FakeWindow | None = None) -> None:
        self.os_window_map = os_window_map
        self.active_window = active_window
        self.remote_control_calls: list[tuple[None, tuple[str, ...]]] = []

    @property
    def all_tabs(self) -> Iterator[FakeTab]:
        for tm in self.os_window_map.values():
            yield from tm

    def call_remote_control(self, self_window: None, args: tuple[str, ...]) -> None:
        self.remote_control_calls.append((self_window, args))


def single_window_tab(*window_ids: int) -> FakeTab:
    """A tab with one window per group -- the common case (plain splits)."""
    return FakeTab([FakeWindowGroup([FakeWindow(wid)]) for wid in window_ids])
