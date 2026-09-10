"""kitty-pounce: cycle kitty windows (splits) across every tab, in every OS
window, as one flat ring.

Dropped into ~/.config/kitty/ and bound with `map ... kitten pounce.py next`
(or `prev`). See README.md for installation and configuration.

This file is re-read, re-compiled and re-exec'd by kitty on every keypress
(kittens/runner.py has no module cache for custom kittens), so it is kept as
one self-contained file with minimal top-level imports.
"""

from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

try:
    # The fallback below is narrower than the real decorator's kwargs, deliberately.
    from kittens.tui.handler import (
        result_handler,  # pyright: ignore[reportAssignmentType]
    )
except ImportError:  # pragma: no cover - only missing outside a kitty process

    def result_handler(*_args: object, **_kwargs: object) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Stand-in so this module imports cleanly under plain pytest."""

        def wrap(fn: Callable[..., Any]) -> Callable[..., Any]:
            return fn

        return wrap


class WindowLike(Protocol):
    """The slice of kitty.window.Window this file actually touches.

    A Protocol rather than the real class: kitty's internal APIs are
    unstable and undocumented by its own admission (custom.rst.txt:54-55),
    so this is the explicit, auditable seam this file depends on -- and it
    lets tests use plain fakes with no kitty import at all. Each member cites
    the source it was verified against.
    """

    id: int  # window.py -- globally unique, the handle to match on


class WindowGroupLike(Protocol):
    """One on-screen cell: normally one window, or several stacked/grouped."""

    @property
    def windows(self) -> Sequence[WindowLike]:  # window_list.py WindowGroup.windows -- last entry is the active one
        ...


class WindowListLike(Protocol):
    """A tab's windows. `groups` is on-screen order -- what kitty's own
    next_window/previous_window cycles via activate_next_window_group
    (window_list.py:500-501), unlike WindowList.__iter__ (all_windows), which
    is creation order and can disagree with it once windows are moved around.
    """

    @property
    def groups(self) -> Sequence[WindowGroupLike]:  # window_list.py:174
        ...


class TabLike(Protocol):
    """The slice of kitty.tabs.Tab this file actually touches. See WindowLike."""

    @property
    def windows(self) -> WindowListLike:  # tabs.py:211
        ...


class BossLike(Protocol):
    """The slice of kitty.boss.Boss this file actually touches. See TabLike."""

    @property
    def os_window_map(self) -> Mapping[int, Iterable[TabLike]]:  # boss.py:414 -- OS-window creation order
        # Read-only property, not a plain attribute: the real value type is
        # dict[int, TabManager], and only a covariant (read-only) member lets
        # that satisfy Iterable[TabLike] (TabManager.__iter__ yields Tab)
        # without a mutable attribute's invariance getting in the way.
        ...

    @property
    def active_window(self) -> WindowLike | None:  # boss.py:1632-1634 -- the globally focused window, or None
        ...

    @property
    def all_tabs(self) -> Iterator[TabLike]:  # boss.py:550-553
        ...

    def call_remote_control(self, self_window: None, args: tuple[str, ...]) -> object:  # boss.py:879-909, in-process
        # self_window narrowed to None (not object): this file only ever
        # passes None, and a Protocol method parameter must be contravariant
        # -- the real Boss only accepts Window | None, not arbitrary objects.
        ...


if TYPE_CHECKING:
    from kitty.boss import Boss
    from kitty.tabs import Tab
    from kitty.window import Window
    from kitty.window_list import WindowGroup, WindowList

    def _protocols_match_real_kitty_types(  # pyright: ignore[reportUnusedFunction]
        boss: Boss, tab: Tab, window: Window, window_list: WindowList, window_group: WindowGroup
    ) -> None:
        """Never called. Exists only so a type-check against a sibling kitty
        checkout (see CONTRIBUTING.md) fails loudly here if these types drift
        away from what the protocols above assume.
        """
        _boss_check: BossLike = boss
        _tab_check: TabLike = tab
        _window_check: WindowLike = window
        _window_list_check: WindowListLike = window_list
        _window_group_check: WindowGroupLike = window_group


_DIRECTIONS = {'next': +1, 'prev': -1}

_T = TypeVar('_T')


def parse_direction(args: list[str]) -> int:
    """Return +1 for 'next', -1 for 'prev'.

    `args[0]` is the kitten name as written in the `map` line (mangled by
    kitty, hyphens -> underscores), NOT the script path -- the direction is
    always `args[1]`.
    """
    direction = args[1] if len(args) > 1 else None
    if direction is None or direction not in _DIRECTIONS:
        raise ValueError(f"expected 'next' or 'prev', got {direction!r}")
    return _DIRECTIONS[direction]


def next_index(count: int, current: int, delta: int) -> int:
    """Return the ring index reached by moving `delta` steps from `current`.

    A single modulo over `count` is what guarantees symmetry: `delta` steps
    one way followed by `delta` steps back always returns to `current`.
    """
    return (current + delta) % count


def _tabs_in_order(
    boss: BossLike,
    order: str,
    get_os_window_pos: Callable[[int], tuple[int, int] | None] | None,
) -> list[TabLike]:
    """Return every tab, in the OS-window ordering `order` selects. Tabs
    within each OS window are always in visual tab-bar order.

    - 'creation' (default): OS-window creation order x visual tab-bar order,
      i.e. `boss.all_tabs`.
    - 'position': OS windows sorted top-to-bottom, left-to-right by screen
      position. An OS window kitty can't currently place (get_os_window_pos
      returns None) sorts last rather than raising.
    """
    if order == 'creation':
        return list(boss.all_tabs)

    if order == 'position':
        if get_os_window_pos is None:
            from kitty.fast_data_types import get_os_window_pos

        def sort_key(os_window_id: int) -> tuple[float, float]:
            pos = get_os_window_pos(os_window_id)
            if pos is None:
                return (float('inf'), float('inf'))
            x, y = pos
            return (y, x)

        tabs: list[TabLike] = []
        for os_window_id in sorted(boss.os_window_map, key=sort_key):
            tabs.extend(boss.os_window_map[os_window_id])
        return tabs

    raise ValueError(f'unknown order: {order!r}')


def build_ring(
    boss: BossLike,
    order: str = 'creation',
    get_os_window_pos: Callable[[int], tuple[int, int] | None] | None = None,
) -> list[WindowLike]:
    """Return the flat list of windows to cycle over: every window, in every
    tab, in every OS window -- one entry per on-screen position (a group of
    stacked/grouped windows contributes only its active member, matching
    what kitty's own next_window/previous_window would cycle to).

    This is the single ordering seam: swapping the OS-window strategy (see
    `_tabs_in_order`) touches nothing else in the file.
    """
    ring: list[WindowLike] = []
    for tab in _tabs_in_order(boss, order, get_os_window_pos):
        for group in tab.windows.groups:
            if group.windows:
                ring.append(group.windows[-1])
    return ring


def resolve_target(ring: list[_T], active: _T | None, delta: int) -> _T | None:
    """Return the ring entry `delta` steps from `active`, or None for a no-op.

    Generic in the ring's element type: this function only needs identity
    equality, not anything Tab-specific -- kept that way so it stays testable
    with plain values, with no kitty types involved.

    None means: 0/1 entries in the ring, or no known active tab (moving would
    be arbitrary). If `active` is set but not found in the ring, index 0 is
    treated as the current position -- this is the documented fallback for a
    stale reference.
    """
    if len(ring) < 2 or active is None:
        return None
    try:
        current = ring.index(active)
    except ValueError:
        current = 0
    return ring[next_index(len(ring), current, delta)]


def main(args: list[str]) -> None:
    """Required by kittens/runner.py (a bare `g['main']` lookup) but never
    called: a no-UI kitten's handle_result runs with no child process and no
    overlay window (kitty/boss.py short-circuits before either is created).
    """


@result_handler(no_ui=True)
def handle_result(args: list[str], data: None, target_window_id: int, boss: BossLike) -> None:
    delta = parse_direction(args)
    ring = build_ring(boss)
    active = boss.active_window
    target = resolve_target(ring, active, delta)
    if target is None or target is active:
        return

    # `focus-window` runs in-process (call_remote_control never touches the
    # socket) and calls Boss.set_active_window(window,
    # switch_os_window_if_needed=True) directly (kitty/rc/focus_window.py),
    # which activates the window's tab and raises its OS window in one step
    # -- no fallback needed, unlike focus-tab's windowless-tab gap.
    boss.call_remote_control(None, ('focus-window', '--match', f'id:{target.id}'))
