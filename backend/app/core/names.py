"""Canonical organization names used by forms, lookups and unique indexes."""
import unicodedata


def clean_name(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).split())


def name_key(value: str) -> str:
    return clean_name(value).casefold()
