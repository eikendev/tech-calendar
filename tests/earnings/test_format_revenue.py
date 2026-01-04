"""
Tests for revenue formatting helper.
"""

import pytest

from tech_calendar.earnings.models import _format_revenue


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param(None, "-", id="none"),
        pytest.param(0, "0", id="zero"),
        pytest.param("invalid", "-", id="invalid-str"),
        pytest.param(0.5, "0", id="fraction"),
        pytest.param(-0.5, "-", id="fraction-neg"),
        pytest.param(1, "1", id="one"),
        pytest.param(999, "999", id="less-than-k"),
        pytest.param(1000, "1 K", id="k"),
        pytest.param(12345, "12 K", id="k-rounded-down"),
        pytest.param(1_000_000, "1.0 M", id="m"),
        pytest.param(1_500_000, "1.5 M", id="m-1-dec"),
        pytest.param(3_000_000_000, "3.00 B", id="b"),
        pytest.param(-2_000_000_000, "-", id="b-neg"),
        pytest.param(1_000_000_000_000, "1.00 T", id="t"),
        pytest.param(" 1500000 ", "1.5 M", id="str-with-spaces"),
    ],
)
def test_format_revenue_parametrized(value, expected):
    """
    Ensure revenue values are formatted into compact human-readable strings.
    """
    assert _format_revenue(value) == expected
