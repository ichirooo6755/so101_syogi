"""HX711 24-bit decode. MicroPython and CPython."""


def signed_24(bits):
    bits &= 0xFFFFFF
    if bits & 0x800000:
        bits -= 0x1000000
    return bits


def is_saturated(value):
    return value >= 0x7FFFFF or value <= -0x800000


def sample_dict(raw_counts, channel_time_s, saturated, extra=None):
    row = {
        "raw_counts": [int(v) for v in raw_counts],
        "channel_time_s": [float(v) for v in channel_time_s],
        "saturated": bool(saturated),
    }
    if extra:
        row.update(extra)
    return row


if __name__ == "__main__":
    assert signed_24(0x000001) == 1
    assert signed_24(0xFFFFFF) == -1
    assert signed_24(0x800000) == -0x800000
    assert is_saturated(0x7FFFFF)
    assert is_saturated(-0x800000)
    assert not is_saturated(123)
    print("hx711 decode ok")
