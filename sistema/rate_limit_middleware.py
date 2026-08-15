"""
Middleware de rate limiting para proteção contra brute force.

Estratégia: sliding window em memória por IP + path.
- Login: 5 tentativas por 60 segundos (IP)
- API geral: 60 requisições por 60 segundos (IP)
"""
import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

_login_hits: dict[str, list[float]] = defaultdict(list)
_api_hits: dict[str, list[float]] = defaultdict(list)


def reset_rate_limits():
    """Limpa contadores de rate limiting (para testes)."""
    _login_hits.clear()
    _api_hits.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    LOGIN_LIMIT = 5
    LOGIN_WINDOW = 60
    API_LIMIT = 60
    API_WINDOW = 60

    def __init__(self, app):
        super().__init__(app)

    def _client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _check(self, store: dict, key: str, limit: int, window: int) -> tuple[bool, int]:
        now = time.time()
        hits = store[key]
        cutoff = now - window
        while hits and hits[0] < cutoff:
            hits.pop(0)
        if len(hits) >= limit:
            retry = int(window - (now - hits[0]))
            return False, max(retry, 1)
        hits.append(now)
        return True, 0

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        ip = self._client_ip(request)

        if path == "/login" and method == "POST":
            allowed, retry = self._check(_login_hits, ip, self.LOGIN_LIMIT, self.LOGIN_WINDOW)
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": f"Muitas tentativas. Tente novamente em {retry}s."},
                    headers={"Retry-After": str(retry)},
                )

        if path.startswith("/api"):
            allowed, retry = self._check(_api_hits, ip, self.API_LIMIT, self.API_WINDOW)
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": f"Limite de requisições excedido. Tente em {retry}s."},
                    headers={"Retry-After": str(retry)},
                )

        return await call_next(request)
