import pytest

from sucket.utils import sizeof_fmt


@pytest.mark.parametrize(
    "power,prefix",
    [
        (0, ""),
        (1, "Ki"),
        (2, "Mi"),
        (3, "Gi"),
        (4, "Ti"),
        (5, "Pi"),
        (6, "Ei"),
        (7, "Zi"),
        (8, "Yi"),
    ],
)
def test_sizeof_fmt_units(power, prefix):
    assert sizeof_fmt(1024 ** power) == f"1.0{prefix}B"
    assert sizeof_fmt(1024 ** power * 10) == f"10.0{prefix}B"
    assert sizeof_fmt(1024 ** power * 2.5) == f"2.5{prefix}B"


def test_sizeof_fmt_bytes():
    assert sizeof_fmt(0) == "0.0B"
    assert sizeof_fmt(10) == "10.0B"
    assert sizeof_fmt(1023) == "1023.0B"
    assert sizeof_fmt(1024) == "1.0KiB"


def test_sizeof_fmt_above_YiB():
    yib = 1024 ** 8
    assert sizeof_fmt(yib) == "1.0YiB"
    assert sizeof_fmt(yib * 1024) == "1024.0YiB"
    assert sizeof_fmt(yib * (1024 ** 2)) == "1048576.0YiB"


def test_sizeof_fmt_negative():
    assert sizeof_fmt(-1) == f"-1.0B"
    assert sizeof_fmt(-1023) == f"-1023.0B"
    assert sizeof_fmt(-1024) == f"-1.0KiB"
