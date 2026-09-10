import pytest

from pounce import parse_direction


def test_next_means_forward():
    assert parse_direction(['pounce.py', 'next']) == +1


def test_prev_means_backward():
    assert parse_direction(['pounce.py', 'prev']) == -1


def test_unknown_direction_raises():
    with pytest.raises(ValueError, match='next.*prev'):
        parse_direction(['pounce.py', 'sideways'])


def test_missing_direction_raises():
    with pytest.raises(ValueError, match='next.*prev'):
        parse_direction(['pounce.py'])
