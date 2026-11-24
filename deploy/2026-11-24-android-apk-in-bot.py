import re, sys
from pathlib import Path
R = Path("/opt/tiyin/tiyin-bot") if len(sys.argv) < 2 else Path(sys.argv[1])
bot = R / "tiyin/bot.py"
B = bot.read_text()
assert "APK_URL" not in B, "уже применено"
a = B.index("async def send_android_welcome(")
b = B.index("@router.message(F.web_app_data)")
NEW = '''APK_URL = "https://github.com/oskonbaev-sys/tiyin/releases/download/latest/Tiyin.apk"
APP_CODE_CB = "and:code"


def _new_app_code(db: DB, user) -> str:
    import secrets as _secrets
    db.x("CREATE TABLE IF NOT EXISTS app_codes(code TEXT PRIMARY KEY, user_id INTEGER, exp INTEGER)")
    db.x("DELETE FROM app_codes WHERE user_id=? OR exp<?", (user["tg_id"], int(time.time())))
    code = f"{_secrets.randbelow(1000000):06d}"
    db.x("INSERT OR REPLACE INTO app_codes(code, user_id, exp) VALUES(?,?,?)", (code, user["tg_id"], int(time.time()) + 600))
    return code


def _android_markup(cfg: Config):
    rows = []
    if cfg.public_url:
        rows.append([InlineKeyboardButton(text="Открыть приложение", web_app=WebAppInfo(url=cfg.public_url))])
    rows += [[InlineKeyboardButton(text="1️⃣ Скачать Tiyin для Android", url=APK_URL)],
             [InlineKeyboardButton(text="2️⃣ Получить код для входа", callback_data=APP_CODE_CB)],
             [InlineKeyboardButton(text="У меня iPhone", callback_data=PLAT_CB + "ios")]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def send_android_welcome(message: Message, cfg: Config, user):
    name = esc(user["name"] or "")
    await message.answer(
        f"Привет{', ' + name if name else ''}! Я веду учёт расходов.\\n\\n"
        "Напишите трату, например «такси 350», и я её запишу. Чтобы пуши банков записывались сами, "
        "установите приложение Tiyin для Android и войдите по коду (кнопки ниже). Отчёты и лимиты в приложении.\\n\\n"
        "Данные хранятся только для вашего учёта; удалить всё можно в настройках приложения.",
        reply_markup=_android_markup(cfg))


async def send_android_setup(bot: Bot, chat_id: int, user, cfg: Config):
    await bot.send_message(
        chat_id,
        "<b>Автозапись трат (Android)</b>\\n"
        "1. Скачайте и установите Tiyin (кнопка ниже). Если телефон спросит — разрешите установку из браузера.\\n"
        "2. Нажмите «Получить код для входа» и введите код в приложении.\\n"
        "3. В приложении: ⋮ → «Автозапись» → включите доступ к уведомлениям.\\n"
        "Ключ вводить не нужно. Записываются только уведомления с суммой, мессенджеры не читаются.",
        reply_markup=_android_markup(cfg))


@router.callback_query(F.data == APP_CODE_CB)
async def cb_app_code(cb: CallbackQuery, db: DB, user):
    await cb.answer()
    code = _new_app_code(db, user)
    await cb.message.answer(f"Код для входа в приложение Tiyin: <code>{code}</code>\\n"
                            "Действует 10 минут, одноразовый. Никому его не пересылайте.")


'''
B = B[:a] + NEW + B[b:]
open(bot, "w").write(B)
print("PATCH3 OK")
