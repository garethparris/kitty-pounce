import pytest

from pounce import next_index, resolve_target


def test_forward_then_backward_returns_to_start():
    """n steps forward then n steps back must land on the original index.

    This is the headline guarantee: a knob turned one way and then back the
    same amount must never drift.
    """
    count = 5
    start = 2
    forward = next_index(count, start, +1)
    back = next_index(count, forward, -1)
    assert back == start


def test_forward_wraps_from_last_to_first():
    assert next_index(count=4, current=3, delta=+1) == 0


def test_backward_wraps_from_first_to_last():
    assert next_index(count=4, current=0, delta=-1) == 3


@pytest.mark.parametrize('count', range(1, 11))
@pytest.mark.parametrize('start', range(0, 5))
@pytest.mark.parametrize('steps', range(1, 6))
def test_n_steps_forward_then_back_always_returns_to_start(count, start, steps):
    if start >= count:
        pytest.skip('start index out of range for this ring size')
    index = start
    for _ in range(steps):
        index = next_index(count, index, +1)
    for _ in range(steps):
        index = next_index(count, index, -1)
    assert index == start


def test_resolve_target_moves_forward_from_active():
    ring = ['a', 'b', 'c']
    assert resolve_target(ring, active='a', delta=+1) == 'b'


def test_resolve_target_wraps_backward_from_first():
    ring = ['a', 'b', 'c']
    assert resolve_target(ring, active='a', delta=-1) == 'c'


def test_resolve_target_empty_ring_is_noop():
    assert resolve_target([], active=None, delta=+1) is None


def test_resolve_target_single_entry_ring_is_noop():
    assert resolve_target(['a'], active='a', delta=+1) is None


def test_resolve_target_no_active_window_is_noop():
    # boss.active_window can genuinely be None (no OS window has focus). With
    # no known current position, moving would be arbitrary, so this is a
    # no-op -- distinct from "active window not in the ring" below.
    ring = ['a', 'b', 'c']
    assert resolve_target(ring, active=None, delta=+1) is None


def test_resolve_target_falls_back_to_first_when_active_not_in_ring():
    # e.g. a stale reference. Falls back to treating index 0 as current.
    ring = ['a', 'b', 'c']
    assert resolve_target(ring, active='not-in-ring', delta=+1) == 'b'
