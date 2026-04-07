def split_text_for_max(text: str, limit: int) -> list[str]:
    normalized = (text or "").strip()
    if not normalized:
        return [""]
    if len(normalized) <= limit:
        return [normalized]

    chunks: list[str] = []
    remaining = normalized

    while len(remaining) > limit:
        split_at = _find_split_position(remaining, limit)
        chunk = remaining[:split_at].strip()
        if not chunk:
            chunk = remaining[:limit].strip()
            split_at = limit
        chunks.append(chunk)
        remaining = remaining[split_at:].strip()

    if remaining:
        chunks.append(remaining)
    return chunks


def _find_split_position(text: str, limit: int) -> int:
    for separator in ("\n", ". ", "! ", "? ", "; ", ", ", " "):
        index = text.rfind(separator, 0, limit + 1)
        if index > limit // 2:
            return index + len(separator.strip())
    return limit
