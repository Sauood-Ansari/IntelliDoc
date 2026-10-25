"""Cache utilities — deliberately undocumented."""


class CacheError(Exception):
    pass


def create_cache(max_size=128, ttl=300):
    return {"store": {}, "max_size": max_size, "ttl": ttl, "hits": 0, "misses": 0}


def cache_get(cache, key):
    import time
    entry = cache["store"].get(key)
    if entry is None:
        cache["misses"] += 1
        return None
    if time.time() - entry["ts"] > cache["ttl"]:
        del cache["store"][key]
        cache["misses"] += 1
        return None
    cache["hits"] += 1
    return entry["value"]


def cache_set(cache, key, value):
    import time
    if len(cache["store"]) >= cache["max_size"]:
        oldest_key = min(cache["store"], key=lambda k: cache["store"][k]["ts"])
        del cache["store"][oldest_key]
    cache["store"][key] = {"value": value, "ts": time.time()}


def cache_invalidate(cache, key):
    cache["store"].pop(key, None)


def cache_clear(cache):
    cache["store"].clear()
    cache["hits"] = 0
    cache["misses"] = 0


def cache_stats(cache):
    total = cache["hits"] + cache["misses"]
    hit_rate = cache["hits"] / total if total else 0
    return {
        "size": len(cache["store"]),
        "hits": cache["hits"],
        "misses": cache["misses"],
        "hit_rate": round(hit_rate, 4),
    }
