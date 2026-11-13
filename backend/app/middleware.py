"""Single-process request protection for the university deployment."""
import time
import hashlib
from collections import defaultdict, deque
from starlette.responses import JSONResponse

class RequestLimits:
    def __init__(self, app):
        self.app = app
        self.requests = defaultdict(deque)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        if scope.get("method") in ("POST","PATCH","PUT"):
            try:
                size = int(headers.get(b"content-length", b"0"))
            except ValueError:
                size = -1
            if size < 0 or size > 11 * 1024 * 1024:
                return await JSONResponse({"detail":"Request body exceeds limit"},status_code=413)(scope, receive, send)
        path = scope["path"]
        if scope.get("method") == "POST" and (path.endswith("/login") or path.endswith("/register")
                or path.endswith("/generate-doc") or path.endswith("/consistency-check")):
            # Do not trust forwarded IPs. Configure a trusted reverse proxy at deployment.
            identity = headers.get(b"authorization") or str(scope.get("client", ("unknown",))[0]).encode()
            key = (hashlib.sha256(identity).hexdigest(), path.rsplit("/",1)[-1])
            now = time.monotonic()
            for old in list(self.requests):
                if not self.requests[old] or self.requests[old][-1] < now-60:
                    del self.requests[old]
            queue = self.requests[key]
            while queue and queue[0] < now-60:
                queue.popleft()
            if len(queue) >= 20:
                return await JSONResponse({"detail":"Too many requests. Please wait a minute."}, status_code=429,
                                          headers={"Retry-After":"60"})(scope, receive, send)
            queue.append(now)
        await self.app(scope, receive, send)

