from io import BytesIO

from scripts.esp32_camera import _frames, _valid_jpeg


def test_valid_jpeg_requires_markers_and_minimum_size():
    frame = b"\xff\xd8" + b"x" * 101 + b"\xff\xd9"
    assert _valid_jpeg(frame)
    assert not _valid_jpeg(b"not jpeg")
    assert not _valid_jpeg(b"\xff\xd8short\xff\xd9")


def test_frames_extracts_jpegs_across_multipart_chunks():
    first = b"\xff\xd8" + b"a" * 101 + b"\xff\xd9"
    second = b"\xff\xd8" + b"b" * 101 + b"\xff\xd9"

    class Chunked(BytesIO):
        def read(self, size=-1):
            return super().read(37 if size else size)

    response = Chunked(b"header\r\n" + first + b"boundary" + second)
    assert list(_frames(response)) == [first, second]
