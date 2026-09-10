import pytest

from pounce import handle_result
from tests.fakes import FakeBoss, FakeTab, FakeTabManager, FakeWindowGroup, single_window_tab


def test_next_focuses_the_next_window_via_remote_control():
    tab = single_window_tab(1, 2)
    boss = FakeBoss({100: FakeTabManager([tab])}, active_window=tab.windows.groups[0].windows[0])

    handle_result(['pounce.py', 'next'], None, 0, boss)

    assert boss.remote_control_calls == [(None, ('focus-window', '--match', 'id:2'))]


def test_prev_wraps_backward_via_remote_control():
    tab = single_window_tab(1, 2)
    boss = FakeBoss({100: FakeTabManager([tab])}, active_window=tab.windows.groups[0].windows[0])

    handle_result(['pounce.py', 'prev'], None, 0, boss)

    assert boss.remote_control_calls == [(None, ('focus-window', '--match', 'id:2'))]


def test_crosses_from_last_window_of_one_tab_to_first_of_the_next():
    tab_a = single_window_tab(1)
    tab_b = single_window_tab(2)
    active = tab_a.windows.groups[0].windows[0]
    boss = FakeBoss({100: FakeTabManager([tab_a, tab_b])}, active_window=active)

    handle_result(['pounce.py', 'next'], None, 0, boss)

    assert boss.remote_control_calls == [(None, ('focus-window', '--match', 'id:2'))]


def test_noop_when_only_one_window_exists():
    tab = single_window_tab(1)
    boss = FakeBoss({100: FakeTabManager([tab])}, active_window=tab.windows.groups[0].windows[0])

    handle_result(['pounce.py', 'next'], None, 0, boss)

    assert boss.remote_control_calls == []


def test_noop_when_target_is_already_the_active_window():
    # Defensive: should the ring ever contain the active window twice, moving
    # onto "itself" must not fire a redundant focus call.
    window = single_window_tab(1).windows.groups[0].windows[0]
    duplicated = FakeTab([FakeWindowGroup([window]), FakeWindowGroup([window])])
    boss = FakeBoss({100: FakeTabManager([duplicated])}, active_window=window)

    handle_result(['pounce.py', 'next'], None, 0, boss)

    assert boss.remote_control_calls == []


def test_noop_when_no_window_is_focused():
    # boss.active_window is genuinely None when no OS window has focus.
    tab = single_window_tab(1, 2)
    boss = FakeBoss({100: FakeTabManager([tab])})  # active_window defaults to None

    handle_result(['pounce.py', 'next'], None, 0, boss)

    assert boss.remote_control_calls == []


def test_unknown_direction_raises():
    boss = FakeBoss({100: FakeTabManager([single_window_tab(1)])})

    with pytest.raises(ValueError, match=r'next.*prev'):
        handle_result(['pounce.py', 'sideways'], None, 0, boss)
