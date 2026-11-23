import re, json, sys, random, time
from pathlib import Path
R = Path("/opt/tiyin/tiyin-bot") if len(sys.argv) < 2 else Path(sys.argv[1])
srv, bot = R / "tiyin/server.py", R / "tiyin/bot.py"
S, B = srv.read_text(), bot.read_text()
assert "ANDROID_MACRO" not in B, "уже применено"

def sub1(pat, repl, s, name):
    s2, n = re.subn(pat, repl, s, count=1, flags=re.M)
    assert n == 1, "не найдено: " + name
    return s2

# ---------- server.py ----------
S = sub1(r'^(\s*)path, qs = url\.path\.rstrip\("/"\) or "/", parse_qs\(url\.query\)\n',
         lambda m: m.group(0) + f'{m.group(1)}self._lenient = False\n', S, "dispatch path")
S = sub1(r'^(\s*)if method == "POST" and path == "/api/ingest":\n\s*return self\._ingest\(\)\n',
         lambda m: m.group(0) +
         f'{m.group(1)}if method == "POST" and path.startswith("/api/ingest/"):\n'
         f'{m.group(1)}    return self._ingest(path[len("/api/ingest/"):])\n'
         f'{m.group(1)}if method == "GET" and path == "/detect":\n'
         f'{m.group(1)}    return self._send(200, DETECT_HTML.encode("utf-8"), "text/html; charset=utf-8")\n', S, "ingest route")
S = sub1(r'def _ingest\(self\):', 'def _ingest(self, path_token=""):', S, "_ingest def")
S = sub1(r'^(\s*)token = auth\[7:\]\.strip\(\) if auth\.lower\(\)\.startswith\("bearer "\) else ""\n',
         lambda m: m.group(0) + f'{m.group(1)}token = path_token or token\n{m.group(1)}self._lenient = True\n', S, "token line")
S = sub1(r'^(\s*)data = json\.loads\(self\.rfile\.read\(n\)\)\n(\s*)except ValueError:\n',
         lambda m: f'{m.group(1)}raw = self.rfile.read(n)\n{m.group(1)}data = json.loads(raw)\n{m.group(2)}except ValueError:\n'
                   f'{m.group(2)}    if getattr(self, "_lenient", False):  # MacroDroid: обычный текст пуша\n'
                   f'{m.group(2)}        return {{"source": "push", "text": raw.decode("utf-8", "replace")[:1000]}}\n', S, "_body")
S += '''

DETECT_HTML = """<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Tiyin</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>body{margin:0;height:100vh;display:flex;align-items:center;justify-content:center;
background:#0F3D2E;color:#F2B632;font:600 20px system-ui}</style></head>
<body><div>Tiyin…</div><script>
var tg = window.Telegram && Telegram.WebApp;
if (tg) { tg.ready(); var p = (tg.platform || "unknown").toLowerCase();
  if (p.indexOf("android") === 0) p = "android"; tg.sendData(p); }
</script></body></html>"""
'''

# ---------- bot.py ----------
B = sub1(r'^router = Router\(name="tiyin"\)\n',
         'import json as _json\nfrom aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, BufferedInputFile\n\n'
         'router = Router(name="tiyin")\n', B, "router line")
B = sub1(r'^(\s*)name = esc\(user\["name"\] or ""\)\n',
         lambda m: f'{m.group(1)}plat = _platform(user)\n'
                   f'{m.group(1)}if plat is None and cfg.public_url:\n'
                   f'{m.group(1)}    return await ask_platform(message, cfg)\n'
                   f'{m.group(1)}if plat == "android":\n'
                   f'{m.group(1)}    return await send_android_welcome(message, cfg, user)\n' + m.group(0), B, "start greeting")
B = sub1(r'^async def send_setup\(bot: Bot, chat_id: int, user, cfg: Config\):\n',
         lambda m: m.group(0) + '    if _platform(user) == "android":\n        return await send_android_setup(bot, chat_id, user, cfg)\n',
         B, "send_setup")
NEW = '''# ---------- Android / определение телефона ----------
ANDROID_MACRO = Path(__file__).resolve().parent.parent / "android" / "Tiyin.macro.tpl"
MACRODROID_URL = "https://play.google.com/store/apps/details?id=com.arlosoft.macrodroid"
PLAT_CB = "plat:"
ANDROID_MACRO_CB = "and:macro"


def _platform(user):
    try:
        return _json.loads(user["settings"] or "{}").get("platform")
    except (ValueError, TypeError, KeyError):
        return None


def _set_platform(db: DB, user, plat: str):
    try:
        s = _json.loads(user["settings"] or "{}")
    except (ValueError, TypeError):
        s = {}
    s["platform"] = plat
    db.x("UPDATE users SET settings=? WHERE tg_id=?", (_json.dumps(s), user["tg_id"]))
    return db.user(user["tg_id"])


async def ask_platform(message: Message, cfg: Config):
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(
        text="▶️ Продолжить", web_app=WebAppInfo(url=f"{cfg.public_url}/detect"))]],
        resize_keyboard=True, one_time_keyboard=True)
    await message.answer("Нажмите «Продолжить» — настрою Tiyin под ваш телефон.", reply_markup=kb)


def _choose_markup():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📱 iPhone", callback_data=PLAT_CB + "ios"),
        InlineKeyboardButton(text="🤖 Android", callback_data=PLAT_CB + "android")]])


async def send_android_welcome(message: Message, cfg: Config, user):
    name = esc(user["name"] or "")
    rows = []
    if cfg.public_url:
        rows.append([InlineKeyboardButton(text="Открыть приложение", web_app=WebAppInfo(url=cfg.public_url))])
    rows += [[InlineKeyboardButton(text="1️⃣ Установить MacroDroid", url=MACRODROID_URL)],
             [InlineKeyboardButton(text="2️⃣ Получить автозапись Tiyin", callback_data=ANDROID_MACRO_CB)],
             [InlineKeyboardButton(text="У меня iPhone", callback_data=PLAT_CB + "ios")]]
    await message.answer(
        f"Привет{', ' + name if name else ''}! Я веду учёт расходов.\\n\\n"
        "Напишите трату, например «такси 350», и я её запишу. Чтобы пуши банков записывались сами: "
        "установите бесплатный MacroDroid и откройте файл автозаписи кнопками ниже. Отчёты и лимиты в приложении.\\n\\n"
        "Данные хранятся только для вашего учёта; удалить всё можно в настройках приложения.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


async def send_android_setup(bot: Bot, chat_id: int, user, cfg: Config):
    await bot.send_message(
        chat_id,
        "<b>Автозапись трат (Android)</b>\\n"
        "1. Установите бесплатный MacroDroid (кнопка ниже).\\n"
        "2. Откройте файл ниже → MacroDroid → «Импорт».\\n"
        "3. Разрешите MacroDroid доступ к уведомлениям.\\n"
        "Ключ вводить не нужно. Записываются только уведомления с суммой, мессенджеры не читаются.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Установить MacroDroid", url=MACRODROID_URL)]]))
    if not ANDROID_MACRO.is_file() or not cfg.public_url:
        return await bot.send_message(chat_id, "Файл автозаписи пока недоступен, попробуйте позже.")
    data = ANDROID_MACRO.read_text(encoding="utf-8").replace(
        "TIYIN_URL", f"{cfg.public_url}/api/ingest/{user['token']}")
    await bot.send_document(chat_id, BufferedInputFile(data.encode("utf-8"), filename="Tiyin.macro"),
                            caption="Откройте файл → MacroDroid → «Импорт». Если ключ попал не туда: /rotate, затем /setup.")


@router.message(F.web_app_data)
async def on_platform_data(message: Message, bot: Bot, cfg: Config, db: DB, user):
    raw = (message.web_app_data.data or "").lower()
    plat = "android" if raw.startswith("android") else ("ios" if raw == "ios" else None)
    if not plat:
        await message.answer("Не удалось определить телефон.", reply_markup=ReplyKeyboardRemove())
        return await message.answer("Какой у вас телефон?", reply_markup=_choose_markup())
    user = _set_platform(db, user, plat)
    await message.answer("✅", reply_markup=ReplyKeyboardRemove())
    await on_start(message, bot, cfg, db, user, CommandObject(prefix="/", command="start"))


@router.callback_query(F.data.startswith(PLAT_CB))
async def cb_platform(cb: CallbackQuery, bot: Bot, cfg: Config, db: DB, user):
    plat = cb.data[len(PLAT_CB):]
    if plat not in ("ios", "android"):
        return await cb.answer()
    user = _set_platform(db, user, plat)
    await cb.answer()
    await on_start(cb.message, bot, cfg, db, user, CommandObject(prefix="/", command="start"))


@router.callback_query(F.data == ANDROID_MACRO_CB)
async def cb_android_macro(cb: CallbackQuery, bot: Bot, cfg: Config, user):
    await cb.answer()
    await send_android_setup(bot, cb.message.chat.id, user, cfg)


'''
B = sub1(r'^@router\.callback_query\(F\.data == views\.SETUP_DATA\)\n', lambda m: NEW + m.group(0), B, "setup cb anchor")

# ---------- шаблон макроса ----------
def sig(): return random.randint(-2**62, -2**40)
excl = {"org.telegram.messenger": "Telegram", "org.telegram.messenger.web": "Telegram", "com.whatsapp": "WhatsApp",
        "com.whatsapp.w4b": "WhatsApp Business", "com.instagram.android": "Instagram", "com.google.android.gm": "Gmail",
        "com.arlosoft.macrodroid": "MacroDroid", "com.android.systemui": "System UI"}
macro = {"disabledTimestamp": 0, "exportedActionBlocks": [], "forceEvenIfNotEnabledTimestamp": 0, "isActionBlock": False,
 "isBeingImported": False, "isClonedInstance": False, "isExtra": False, "isFavourite": False,
 "lastEditedTimestamp": int(time.time() * 1000), "localVariables": [], "m_GUID": sig(), "m_category": "Tiyin",
 "m_constraintList": [], "m_description": "Автозапись трат в Tiyin (@tiyinplus_bot): пуши с суммой отправляются в бот.",
 "m_descriptionOpen": False, "m_enabled": True, "m_excludeLog": False, "m_headingColor": 0, "m_isOrCondition": False,
 "m_name": "Tiyin — автозапись трат",
 "m_triggerList": [{"enableRegex": True, "m_applicationNameList": list(excl.values()), "m_exactMatch": False,
   "m_excludeApps": True, "m_excludes": False, "m_ignoreOngoing": True, "m_option": 0,
   "m_packageNameList": list(excl.keys()), "m_soundOption": 0, "m_supressMultiples": True,
   "m_textContent": "(?is).*\\d\\s?(kgs|сом|som|с)(\\s|[.,!)]|$).*", "m_SIGUID": sig(),
   "m_classType": "NotificationTrigger", "m_constraintList": [], "m_isDisabled": False, "m_isOrCondition": False}],
 "m_actionList": [{"requestConfig": {"allowAnyCertificate": False, "basicAuthEnabled": False, "basicAuthPassword": "",
   "basicAuthUsername": "", "blockNextAction": False, "contentBodyFileDisplayName": "", "contentBodyFileUri": "",
   "contentBodySource": 0, "contentBodyText": "[not_title]\n[notification]", "contentType": "text/plain",
   "followRedirects": False, "headerParams": [], "queryParams": [], "requestTimeOutSeconds": 15, "requestType": 1,
   "saveResponseFileName": "", "saveResponseFolderPathDisplayName": "", "saveResponseFolderPathUri": "",
   "saveResponseType": 0, "saveReturnCodeToVariable": False, "urlToOpen": "TIYIN_URL"},
   "m_SIGUID": sig(), "m_classType": "HttpRequestAction", "m_constraintList": [], "m_isDisabled": False,
   "m_isOrCondition": False}]}
(R / "android").mkdir(exist_ok=True)
(R / "android" / "Tiyin.macro.tpl").write_text(json.dumps(macro, ensure_ascii=False, indent=1), encoding="utf-8")
srv.write_text(S); bot.write_text(B)
print("PATCH OK")
