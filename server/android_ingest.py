"""
Tiyin для Android: подключение без ручного ввода и приём пушей.

  POST /api/android/claim   {"token": "..."}  -> {"ok": true, "key": "<ключ автозаписи>"}
  POST /api/ingest/android  Authorization: Bearer <ключ>
                            {"app": "<пакет банка>", "title": "...", "text": "..."}

Подключение к вашему aiohttp-приложению (в том же процессе, что и бот):
    from android_ingest import setup_android_ingest
    setup_android_ingest(app, user_by_key=..., get_key=..., save_push=..., on_linked=...)

  user_by_key(key) -> user_id | None    — та же проверка ключа, что у /api/ingest
  get_key(user_id) -> str               — ключ автозаписи пользователя (тот же, что для iPhone)
  save_push(user_id, text) -> awaitable — та же запись «пуш банка», что для iPhone
  on_linked(user_id) -> awaitable       — например, бот пишет «✅ Автозапись подключена: Android»

Если бот и веб-сервер — разные процессы, перенесите _TOKENS в БД/Redis.
"""
import json
import secrets
import time

from aiohttp import web

TOKEN_TTL = 15 * 60
_TOKENS: dict[str, tuple[int, float]] = {}


def create_link_token(user_id: int) -> str:
    """Одноразовый токен для кнопки «Подключить автозапись» (живёт 15 минут)."""
    now = time.time()
    for t, (_, exp) in list(_TOKENS.items()):
        if exp < now:
            _TOKENS.pop(t, None)
    token = secrets.token_urlsafe(16)
    _TOKENS[token] = (user_id, now + TOKEN_TTL)
    return token


def _claim(token: str) -> int | None:
    item = _TOKENS.pop(token, None)
    if not item or item[1] < time.time():
        return None
    return item[0]


async def _json(request: web.Request) -> dict:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, Exception):
        return {}


def setup_android_ingest(app: web.Application, *, user_by_key, get_key, save_push, on_linked=None) -> None:
    async def claim(request: web.Request) -> web.Response:
        user_id = _claim(str((await _json(request)).get("token", "")))
        if not user_id:
            return web.json_response({"ok": False, "error": "expired"}, status=410)
        if on_linked:
            await on_linked(user_id)
        return web.json_response({"ok": True, "key": get_key(user_id)})

    async def ingest(request: web.Request) -> web.Response:
        auth = request.headers.get("Authorization", "")
        key = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
        user_id = user_by_key(key) if key else None
        if not user_id:
            return web.json_response({"ok": False, "error": "unauthorized"}, status=401)
        data = await _json(request)
        text = "\n".join(s for s in (str(data.get(k, "")).strip() for k in ("title", "text")) if s)
        if not text:
            return web.json_response({"ok": False, "error": "empty"}, status=400)
        await save_push(user_id, text)
        return web.json_response({"ok": True})

    app.router.add_post("/api/android/claim", claim)
    app.router.add_post("/api/ingest/android", ingest)
