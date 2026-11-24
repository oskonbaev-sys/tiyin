import re, sys
from pathlib import Path
R = Path("/opt/tiyin/tiyin-bot") if len(sys.argv) < 2 else Path(sys.argv[1])
srv, bot, web = R / "tiyin/server.py", R / "tiyin/bot.py", R / "webapp/index.html"
S, B, W = srv.read_text(), bot.read_text(), web.read_text()
assert "_app_login" not in S, "уже применено"

def sub1(pat, repl, s, name):
    s2, n = re.subn(pat, repl, s, count=1, flags=re.M)
    assert n == 1, "не найдено: " + name
    return s2

# --- server: Bearer-ключ для API мини-приложения
S = sub1(r'^(\s*)def _user\(self\):\n', lambda m: m.group(0) +
    f'{m.group(1)}    auth = self.headers.get("Authorization", "")\n'
    f'{m.group(1)}    if auth.lower().startswith("bearer "):  # Android-приложение: вход по коду из бота\n'
    f'{m.group(1)}        u = db.user_by_token(auth[7:].strip())\n'
    f'{m.group(1)}        if u:\n'
    f'{m.group(1)}            return u\n', S, "_user")
# --- server: маршрут входа
S = sub1(r'^(\s*)if method == "GET" and path == "/detect":\n', lambda m:
    f'{m.group(1)}if method == "POST" and path == "/api/app/login":\n{m.group(1)}    return self._app_login()\n' + m.group(0), S, "detect route")
S = sub1(r'^(\s*)def _register\(self\):\n', lambda m:
    f'{m.group(1)}def _app_login(self):\n'
    f'{m.group(1)}    if not app.rate_ok("login:" + self.client_address[0]):\n'
    f'{m.group(1)}        raise ApiError(429, "too many requests")\n'
    f'{m.group(1)}    code = str(self._body().get("code") or "").strip()[:12]\n'
    f'{m.group(1)}    db.x("CREATE TABLE IF NOT EXISTS app_codes(code TEXT PRIMARY KEY, user_id INTEGER, exp INTEGER)")\n'
    f'{m.group(1)}    row = db.one("SELECT * FROM app_codes WHERE code=?", (code,)) if code else None\n'
    f'{m.group(1)}    if row:\n'
    f'{m.group(1)}        db.x("DELETE FROM app_codes WHERE code=?", (code,))\n'
    f'{m.group(1)}    if not row or row["exp"] < time.time():\n'
    f'{m.group(1)}        raise ApiError(401, "bad code")\n'
    f'{m.group(1)}    user = db.user(row["user_id"])\n'
    f'{m.group(1)}    if not user:\n'
    f'{m.group(1)}        raise ApiError(401, "bad code")\n'
    f'{m.group(1)}    self._json(200, {{"ok": True, "token": user["token"], "name": user["name"] or ""}})\n\n' + m.group(0), S, "_register")

# --- bot: команда /login (до общего обработчика неизвестных команд)
NEW = '''@router.message(cmd("login"))
async def on_app_login(message: Message, db: DB, user):
    import secrets as _secrets
    db.x("CREATE TABLE IF NOT EXISTS app_codes(code TEXT PRIMARY KEY, user_id INTEGER, exp INTEGER)")
    db.x("DELETE FROM app_codes WHERE user_id=? OR exp<?", (user["tg_id"], int(time.time())))
    code = f"{_secrets.randbelow(1000000):06d}"
    db.x("INSERT OR REPLACE INTO app_codes(code, user_id, exp) VALUES(?,?,?)", (code, user["tg_id"], int(time.time()) + 600))
    await message.answer(f"Код для входа в приложение Tiyin: <code>{code}</code>\\nДействует 10 минут, одноразовый. Никому его не пересылайте.")


'''
B = sub1(r'^@router\.message\(F\.text\.startswith\("/"\)\)\n', lambda m: NEW + m.group(0), B, "unknown cmd anchor")

# --- webapp: ключ приложения из #app_token
W = sub1(r'^(\s*)if \(tg && tg\.initData\) headers\["X-Init-Data"\] = tg\.initData;\n', lambda m:
    f'{m.group(1)}const appToken = () => {{ try {{ const mm = location.hash.match(/app_token=([^&]+)/); '
    f'if (mm) {{ localStorage.setItem("tiyin_app_token", decodeURIComponent(mm[1])); history.replaceState(null, "", location.pathname + location.search); }} '
    f'return localStorage.getItem("tiyin_app_token") || ""; }} catch (e) {{ return ""; }} }};\n'
    + m.group(0) + f'{m.group(1)}else if (appToken()) headers["Authorization"] = "Bearer " + appToken();\n', W, "webapp headers")

srv.write_text(S); bot.write_text(B); web.write_text(W)
print("PATCH2 OK")
