from max_chat_backend.services.text_chunks import split_text_for_max


def test_short_text_stays_single_chunk() -> None:
    chunks = split_text_for_max("hello", 10)
    assert chunks == ["hello"]


def test_long_text_is_split_into_multiple_chunks() -> None:
    chunks = split_text_for_max("a " * 30, 20)

    assert len(chunks) > 1
    assert all(len(chunk) <= 20 for chunk in chunks)
