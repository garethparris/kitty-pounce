import pytest

from pounce import build_ring
from tests.fakes import FakeBoss, FakeTab, FakeTabManager, FakeWindow, FakeWindowGroup, single_window_tab


def test_flattens_os_windows_then_tabs_then_windows_within_each_tab():
    # OS window 100: tab with windows 1,2 ; tab with window 3
    # OS window 200: tab with window 4
    tab_a = single_window_tab(1, 2)
    tab_b = single_window_tab(3)
    tab_c = single_window_tab(4)
    boss = FakeBoss(
        {
            100: FakeTabManager([tab_a, tab_b]),
            200: FakeTabManager([tab_c]),
        }
    )

    ring = build_ring(boss, order='creation')

    assert [w.id for w in ring] == [1, 2, 3, 4]


def test_creation_order_is_the_default():
    boss = FakeBoss({100: FakeTabManager([single_window_tab(1)])})

    assert build_ring(boss) == build_ring(boss, order='creation')


def test_a_window_group_contributes_only_its_active_window():
    # A grouped/stacked cell (e.g. windows 5 and 6 sharing one on-screen
    # position) contributes only its active (last) member -- matching what
    # kitty's own next_window cycles through.
    tab = FakeTabManager([_tab_with_groups([[5, 6], [7]])])
    boss = FakeBoss({100: tab})

    ring = build_ring(boss, order='creation')

    assert [w.id for w in ring] == [6, 7]


def test_position_order_sorts_os_windows_top_to_bottom_left_to_right():
    tab_a = single_window_tab(1)
    tab_b = single_window_tab(2)
    boss = FakeBoss(
        {
            100: FakeTabManager([tab_a]),  # will be at screen x=500
            200: FakeTabManager([tab_b]),  # will be at screen x=0 -- should sort first
        }
    )
    positions = {100: (500, 0), 200: (0, 0)}

    ring = build_ring(boss, order='position', get_os_window_pos=positions.get)

    assert [w.id for w in ring] == [2, 1]


def test_position_order_sorts_unknown_position_last():
    tab_a = single_window_tab(1)
    tab_b = single_window_tab(2)
    boss = FakeBoss(
        {
            100: FakeTabManager([tab_a]),
            200: FakeTabManager([tab_b]),
        }
    )
    # get_os_window_pos returns None for an os window kitty doesn't know
    # about, per fast_data_types.pyi/state.c -- must not raise.
    positions = {100: None, 200: (0, 0)}

    ring = build_ring(boss, order='position', get_os_window_pos=positions.get)

    assert [w.id for w in ring] == [2, 1]


def test_unknown_order_raises():
    boss = FakeBoss({100: FakeTabManager([single_window_tab(1)])})

    with pytest.raises(ValueError, match=r'unknown order'):
        build_ring(boss, order='sideways')


def _tab_with_groups(groups: list[list[int]]) -> FakeTab:
    return FakeTab([FakeWindowGroup([FakeWindow(wid) for wid in ids]) for ids in groups])
