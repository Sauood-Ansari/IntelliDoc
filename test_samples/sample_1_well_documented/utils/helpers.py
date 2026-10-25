"""Utility helpers — fully documented, should yield a high score."""


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format a numeric amount as a currency string.

    Args:
        amount: The monetary value to format.
        currency: ISO-4217 currency code (default ``USD``).

    Returns:
        A formatted string such as ``$1,234.56`` or ``€1.234,56``.
    """
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "INR": "₹"}
    symbol = symbols.get(currency, currency + " ")
    return f"{symbol}{amount:,.2f}"


def clamp(value: float, low: float, high: float) -> float:
    """Restrict *value* to the inclusive range [low, high].

    Args:
        value: The number to clamp.
        low: Lower bound.
        high: Upper bound.

    Returns:
        The clamped value.
    """
    return max(low, min(high, value))


def chunk_list(data: list, size: int) -> list[list]:
    """Split *data* into sub-lists of at most *size* elements.

    Args:
        data: The input list to chunk.
        size: Maximum number of items per chunk.

    Returns:
        A list of lists, each containing up to *size* items.
    """
    return [data[i : i + size] for i in range(0, len(data), size)]


def merge_dicts(*dicts: dict) -> dict:
    """Merge multiple dictionaries into a single dict (last-wins).

    Args:
        *dicts: Variable number of dictionaries to merge.

    Returns:
        A new dictionary containing all key-value pairs.
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result
