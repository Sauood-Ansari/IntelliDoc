"""IntelliDoc — Shared rate limiter instance.

Kept in a separate module so routers can import it without creating
a circular dependency through app.main.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
